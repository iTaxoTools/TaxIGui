# -----------------------------------------------------------------------------
# TaxiGui - GUI for Taxi2
# Copyright (C) 2022-2023  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6 import QtCore

from pathlib import Path
from typing import Protocol, Type

from itaxotools.common.bindings import Binder, Property
from itaxotools.common.utility import AttrDict, override
from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.model.common import ItemModel, Object
from itaxotools.taxi_gui.model.input_file import InputFileModel
from itaxotools.taxi_gui.model.tasks import SubtaskModel
from itaxotools.taxi_gui.threading import ReportDone
from itaxotools.taxi_gui.types import FileFormat, FileInfo, Notification

from .process import get_file_info


class ItemProxyModel(QtCore.QAbstractProxyModel):
    ItemRole = ItemModel.ItemRole

    def __init__(self, model=None, root=None):
        super().__init__()
        self.unselected = "---"
        self.root = None
        if model and root:
            self.setSourceModel(model, root)

    def get_default_index(self):
        return self.index(0, 0)

    def sourceDataChanged(self, topLeft, bottomRight):
        self.dataChanged.emit(
            self.mapFromSource(topLeft), self.mapFromSource(bottomRight)
        )

    def add_file(self, file: InputFileModel):
        index = self.source.add_file(file, focus=False)
        return self.mapFromSource(index)

    @override
    def setSourceModel(self, model, root):
        super().setSourceModel(model)
        self.root = root
        self.source = model
        model.dataChanged.connect(self.sourceDataChanged)

    @override
    def mapFromSource(self, sourceIndex):
        item = sourceIndex.internalPointer()
        if not item or item.parent != self.root:
            return QtCore.QModelIndex()
        return self.createIndex(item.row + 1, 0, item)

    @override
    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return QtCore.QModelIndex()
        if proxyIndex.row() == 0:
            return QtCore.QModelIndex()
        item = proxyIndex.internalPointer()
        source = self.sourceModel()
        return source.createIndex(item.row, 0, item)

    @override
    def index(
        self, row: int, column: int, parent=QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        if parent.isValid() or column != 0:
            return QtCore.QModelIndex()
        if row < 0 or row > len(self.root.children):
            return QtCore.QModelIndex()
        if row == 0:
            return self.createIndex(0, 0)
        return self.createIndex(row, 0, self.root.children[row - 1])

    @override
    def parent(self, index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        return QtCore.QModelIndex()

    @override
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.root.children) + 1

    @override
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 1

    @override
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None
        if index.row() == 0:
            if role == QtCore.Qt.DisplayRole:
                return self.unselected
            return None
        return super().data(index, role)

    @override
    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.row() == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return super().flags(index)


class FileInfoSubtaskModel(SubtaskModel):
    task_name = "FileInfoSubtask"

    done = QtCore.Signal(FileInfo)

    def start(self, path: Path):
        super().start(get_file_info, path)

    def onDone(self, report: ReportDone):
        self.done.emit(report.result)
        self.busy = False


class DataFileProtocol(Protocol):
    def is_valid(self) -> bool:
        pass

    def as_dict(self) -> AttrDict:
        pass

    @classmethod
    def from_file_info(cls, info: FileInfo, *args, **kwargs) -> DataFileProtocol:
        pass


class ImportedInputModel(Object):
    notification = QtCore.Signal(Notification)
    updated = QtCore.Signal()

    model = Property(QtCore.QAbstractItemModel, None)
    index = Property(QtCore.QModelIndex, None)
    object = Property(DataFileProtocol, None)
    format = Property(FileFormat, None)

    def __init__(self, cast_type: Type[DataFileProtocol], *cast_args, **cast_kwargs):
        super().__init__()
        self.cast_type = cast_type
        self.cast_args = cast_args
        self.cast_kwargs = cast_kwargs

        item_model = app.model.items
        self.model = ItemProxyModel(item_model, item_model.files)
        self.binder = Binder()

    def add_info(self, info: FileInfo):
        index = self.model.add_file(InputFileModel(info))
        self.set_index(index)

    def set_index(self, index: QtCore.QModelIndex):
        if index == self.index:
            return
        try:
            object = self._cast_from_index(index)
        except Exception:
            # raise e
            self.notification.emit(Notification.Warn("Unexpected file format."))
            self.properties.index.update()
            self.properties.object.update()
            self.properties.format.update()
            return

        self._set_object(object)
        self.index = index

    def _set_object(self, object: DataFileProtocol):
        if object == self.object:
            return
        self.format = object.info.format if object else None
        self.binder.unbind_all()
        if object:
            for property in object.properties:
                self.binder.bind(property, self.updated)
        self.object = object
        self.updated.emit()

    def _cast_from_index(self, index: QtCore.QModelIndex) -> DataFileProtocol | None:
        if not index:
            return
        item = self.model.data(index, ItemProxyModel.ItemRole)
        if not item:
            return None
        info = item.object.info
        return self.cast_type.from_file_info(info, *self.cast_args, **self.cast_kwargs)

    def is_valid(self) -> bool:
        if self.object:
            return self.object.is_valid()
        return False

    def as_dict(self) -> AttrDict | None:
        if self.object:
            return self.object.as_dict()
        return None
