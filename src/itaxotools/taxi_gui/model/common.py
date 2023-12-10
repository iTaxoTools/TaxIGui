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

from PySide6 import QtCore

from itaxotools.common.bindings import Property, PropertyObject
from itaxotools.common.types import Type
from itaxotools.common.utility import override

from ..types import TreeItem


class _TypedPropertyObjectMeta(type(PropertyObject), type(Type)):
    def __new__(cls, name, bases, attrs):
        obj = super().__new__(cls, name, bases, attrs)
        return cls._patch_object(obj, name, bases)


class Object(PropertyObject, Type, metaclass=_TypedPropertyObjectMeta):
    """Interface for backend structures"""

    name = Property(str, "")

    def __init__(self, name=None):
        super().__init__()
        if name:
            self.name = name

    def __repr__(self):
        return Type.__repr__(self)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        for a, b in zip(self.properties, other.properties):
            if a.key != b.key:
                return False
            if a.value != b.value:
                return False
        return True


class Group(Object):
    pass


class MainModel(PropertyObject):
    dashboard = Property(bool, False)

    dirty_data = Property(bool, True)
    busy = Property(bool, False)


class ItemModel(QtCore.QAbstractItemModel):
    """The main model that holds all Items"""

    focused = QtCore.Signal(QtCore.QModelIndex)
    ItemRole = QtCore.Qt.UserRole

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = TreeItem(None)
        self.tasks = self.root.add_child(Group("Tasks"))
        self.sequences = self.root.add_child(Group("Sequences"))
        self.files = self.root.add_child(Group("Imported Files"))

    @property
    def tasks_index(self):
        group = self.tasks
        return self.createIndex(group.row, 0, group)

    @property
    def sequences_index(self):
        group = self.sequences
        return self.createIndex(group.row, 0, group)

    def _add_entry(self, group, child, focus=False):
        parent = self.createIndex(group.row, 0, group)
        row = len(group.children)
        self.beginInsertRows(parent, row, row)
        group.add_child(child)

        def entryChanged():
            index = self.index(row, 0, parent)
            self.dataChanged.emit(index, index)

        child.properties.name.notify.connect(entryChanged)
        self.endInsertRows()
        index = self.index(row, 0, parent)
        self.dataChanged.emit(index, index)
        if focus:
            self.focus(index)
        return index

    def add_task(self, task, focus=False):
        return self._add_entry(self.tasks, task, focus)

    def add_sequence(self, sequence, focus=False):
        return self._add_entry(self.sequences, sequence, focus)

    def add_file(self, file, focus=False):
        for row, file_item in enumerate(self.files.children):
            if file_item.object.path == file.path:
                parent = self.createIndex(self.files.row, 0, self.files)
                index = self.index(row, 0, parent)
                if focus:
                    self.focus(index)
                return index
        return self._add_entry(self.files, file, focus)

    def find_task(self, task_type):
        for row, task_item in enumerate(self.tasks.children):
            if type(task_item.object) is task_type:
                parent = self.createIndex(self.tasks.row, 0, self.tasks)
                return self.index(row, 0, parent)
        return None

    def focus(self, index):
        self.focused.emit(index)

    def remove_index(self, index):
        parent = index.parent()
        parentItem = parent.internalPointer()
        row = index.row()
        self.beginRemoveRows(parent, row, row)
        parentItem.children.pop(row)
        self.endRemoveRows()

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.root

    @override
    def index(
        self, row: int, column: int, parent=QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        if parent.isValid() and column != 0:
            return QtCore.QModelIndex()

        parentItem = self.getItem(parent)

        if row < 0 or row >= len(parentItem.children):
            return QtCore.QModelIndex()

        childItem = parentItem.children[row]
        return self.createIndex(row, 0, childItem)

    @override
    def parent(self, index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if item.parent is self.root or item.parent is None:
            return QtCore.QModelIndex()
        return self.createIndex(item.parent.row, 0, item.parent)

    @override
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.root.children)

        parentItem = parent.internalPointer()
        return len(parentItem.children)

    @override
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 1

    @override
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return item.object.name
        if role == self.ItemRole:
            return item
        return None

    @override
    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        item = index.internalPointer()
        flags = super().flags(index)
        if item in self.root.children:
            flags = flags & ~QtCore.Qt.ItemIsEnabled
        return flags
