# -----------------------------------------------------------------------------
# Taxi3Gui - GUI for Taxi3
# Copyright (C) 2022  Patmanidis Stefanos
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
from PySide6 import QtWidgets
from PySide6 import QtGui

from abc import ABC, abstractmethod
from pathlib import Path

from itaxotools.common.widgets import VectorIcon
from itaxotools.common.resources import get_common
from itaxotools.common.utility import override

from .model import Object, Group


class Item:
    def __init__(self, data, parent=None):
        self.children = list()
        self.parent = parent
        self.data = data

    def add_child(self, data):
        child = Item(data, self)
        self.children.append(child)
        return child

    @property
    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class ItemModel(QtCore.QAbstractItemModel):

    DataRole = QtCore.Qt.UserRole

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = Item('')
        self.tasks = self.root.add_child(Group('Tasks'))
        self.sequences = self.root.add_child(Group('Sequences'))

    def _add_entry(self, group, child):
        parent = self.createIndex(group.row, 0, group)
        row = len(group.children)
        self.beginInsertRows(parent, row, row)
        item = group.add_child(child)
        def entryChanged():
            index = self.index(row, 0, parent)
            self.dataChanged.emit(index, index)
        child.changed.connect(entryChanged)
        self.endInsertRows()

    def add_task(self, task):
        self._add_entry(self.tasks, task)

    def add_sequence(self, sequence):
        self._add_entry(self.sequences, sequence)

    def remove_index(self, index):
        parent = index.parent()
        parentItem = parent.internalPointer()
        row = index.row()
        self.beginRemoveRows(parent, row, row)
        parentItem.children.pop(row)
        self.endRemoveRows()

    @override
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if column != 0:
            return QtCore.QModelIndex()

        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            parentItem = self.root

        if row >= len(parentItem.children):
            return QtCore.QModelIndex()

        childItem = parentItem.children[row]
        return self.createIndex(row, 0, childItem)

    @override
    def parent(self, index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if item is self.root or item.parent is None:
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
            return item.data.name
        if role == self.DataRole:
            return item
        return None


class ItemView(ABC):

    width: int
    height: int

    def __init__(self, item: Item):
        self.item = item

    @abstractmethod
    def sizeHint(self, option, index) -> QtCore.QSize:
        ...

    @abstractmethod
    def paint(self, painter, option, index) -> None:
        ...

    def mouseEvent(self, event, model, option, index) -> None:
        pass


class GroupView(ItemView):

    width = 256
    height = 32
    marginLeft = 4
    marginBottom = 2

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        textRect = QtCore.QRect(option.rect)
        textRect.adjust(self.marginLeft, 0, 0, -self.marginBottom)
        font = painter.font()
        font.setPixelSize(16)
        painter.setFont(font)
        painter.drawText(textRect, QtCore.Qt.AlignBottom, self.item.data.name)

        line = QtCore.QLine(
            option.rect.left(),
            option.rect.bottom(),
            option.rect.right(),
            option.rect.bottom(),
            )
        painter.drawLine(line)


class EntryView(ItemView):

    width = 256
    height = 52
    marginLeft = 4
    marginText = 40
    iconSize = 32

    def __init__(self, item, icon=None):
        super().__init__(item)
        assert icon is not None
        self.icon = icon

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillRect(option.rect, option.palette.light())
        else:
            painter.fillRect(option.rect, option.palette.mid())

        rect = self.textRect(option)
        painter.drawText(rect, QtCore.Qt.AlignVCenter, self.item.data.name)

        rect = self.iconRect(option)
        mode = QtGui.QIcon.Disabled
        if option.state & QtWidgets.QStyle.State_Selected:
            mode = QtGui.QIcon.Normal
        pix = self.icon.pixmap(QtCore.QSize(*[self.iconSize]*2), mode)
        painter.drawPixmap(rect, pix)

    def iconRect(self, option):
        left = option.rect.left() + self.marginLeft
        vCenter = option.rect.center().y()
        return QtCore.QRect(
            left, vCenter - self.iconSize/2 + 1,
            self.iconSize, self.iconSize)

    def textRect(self, option):
        rect = QtCore.QRect(option.rect)
        return rect.adjusted(self.marginText, 0, 0, 0)

    def mouseEvent(self, event, model, option, index):
        rect = self.iconRect(option)
        if rect.contains(event.pos()):
            name = model.data(index, QtCore.Qt.DisplayRole)
            print('clicked on', name)


class ItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

        self.icon = VectorIcon(
            get_common(Path('icons/svg/arrow-right.svg')),
            self.parent().window().colormap)

    def indexView(self, index):
        item = index.data(ItemModel.DataRole)
        if item.children:
            return GroupView(item)
        return EntryView(item, icon=self.icon)

    @override
    def sizeHint(self, option, index):
        view = self.indexView(index)
        return view.sizeHint(option, index)

    @override
    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        painter.save()
        view = self.indexView(index)
        view.paint(painter, option, index)
        painter.restore()

    @override
    def editorEvent(self, event, model, option, index):
        if not (
            event.type() == QtCore.QEvent.MouseButtonRelease and
            event.button() == QtCore.Qt.LeftButton
        ):
            return super().event(event)
        view = self.indexView(index)
        view.mouseEvent(event, model, option, index)
        return super().event(event)


class ItemTreeView(QtWidgets.QTreeView):
    selected = QtCore.Signal(Item, QtCore.QModelIndex)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            ItemTreeView {
                background: palette(Midlight);
                border: 0px solid transparent;
            }
        """)
        # self.setSpacing(2)
        self.setHeaderHidden(True)
        self.setIndentation(0)
        ##????? condense
        self.delegate = ItemDelegate(self)
        self.setItemDelegate(self.delegate)

    @override
    def currentChanged(self, current, previous):
        item = self.model().data(current, ItemModel.DataRole)
        self.selected.emit(item, current)

    @override
    def sizeHint(self):
        w = self.sizeHintForColumn(0)
        h = self.sizeHintForRow(0)
        return QtCore.QSize(w, h)

    @override
    def setModel(self, model):
        super().setModel(model)
        self.expandAll()


class SideBar(QtWidgets.QFrame):
    selected = QtCore.Signal(Item, QtCore.QModelIndex)

    def __init__(self, model=None, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            SideBar {
                border: 0px solid transparent;
                border-right: 1px solid palette(Dark);
            }
        """)

        self.model = model or ItemModel()
        self.view = ItemTreeView(self)
        self.view.setModel(self.model)
        self.view.selected.connect(self.selected)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
