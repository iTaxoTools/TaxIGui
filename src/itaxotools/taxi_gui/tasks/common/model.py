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

from itaxotools.common.utility import override


class ItemProxyModel(QtCore.QAbstractProxyModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = None
        self.unselected = '---'

    def sourceDataChanged(self, topLeft, bottomRight):
        self.dataChanged.emit(self.mapFromSource(topLeft), self.mapFromSource(bottomRight))

    @override
    def setSourceModel(self, model, root):
        super().setSourceModel(model)
        self.root = root
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
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
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
