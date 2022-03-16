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


class Item(ABC):

    width: int
    height: int

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def sizeHint(self, option, index) -> QtCore.QSize:
        ...

    @abstractmethod
    def paint(self, painter, option, index) -> None:
        ...

    def mouseEvent(self, event, model, option, index) -> None:
        pass


class Group(Item):

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
        painter.drawText(textRect, QtCore.Qt.AlignBottom, self.name)

        line = QtCore.QLine(
            option.rect.left(),
            option.rect.bottom(),
            option.rect.right(),
            option.rect.bottom(),
            )
        painter.drawLine(line)


class Task(Item):

    width = 256
    height = 52
    marginLeft = 4
    marginText = 40
    iconSize = 32

    def __init__(self, name, icon):
        self.name = name
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
        painter.drawText(rect, QtCore.Qt.AlignVCenter, self.name)

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
            model.onIconClicked(index)


class ItemModel(QtCore.QAbstractListModel):

    def __init__(self, items):
        super().__init__()
        self.items = items

    def rowCount(self, parent):
        return len(self.items)

    def data(self, index, role):
        if (
            index.row() < 0 or
            index.row() >= len(self.items) or
            index.column() != 0
        ):
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.items[index.row()].name
        if role == QtCore.Qt.UserRole:
            return self.items[index.row()]
        return None

    def onIconClicked(self, index):
        print('clicked on', self.data(index, QtCore.Qt.UserRole).name)


class ItemDelegate(QtWidgets.QStyledItemDelegate):
    def sizeHint(self, option, index):
        item = index.data(QtCore.Qt.UserRole)
        return item.sizeHint(option, index)

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        item = index.data(QtCore.Qt.UserRole)
        painter.save()
        item.paint(painter, option, index)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if not (
            event.type() == QtCore.QEvent.MouseButtonRelease and
            event.button() == QtCore.Qt.LeftButton
        ):
            return super().event(event)
        item = index.data(QtCore.Qt.UserRole)
        item.mouseEvent(event, model, option, index)
        return super().event(event)


class ItemView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            ItemView {
                background: palette(Midlight);
                border: 0px solid transparent;
            }
        """)
        self.setSpacing(2)
        self.delegate = ItemDelegate()
        self.setItemDelegate(self.delegate)

    def sizeHint(self):
        w = self.sizeHintForColumn(0)
        h = self.sizeHintForRow(0)
        return QtCore.QSize(w, h)


class SideBar(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setStyleSheet("""
            SideBar {
                border: 0px solid transparent;
                border-right: 1px solid palette(Mid);
            }
        """)

        icon = VectorIcon(
            get_common(Path('icons/svg/arrow-right.svg')),
            self.window().colormap)
        items = [
            Group('Tasks'),
            Task('DEREP #1', icon),
            Task('DEREP #2', icon),
            Task('DECONT', icon),
            Group('Sequences'),
            Task('Frog Samples', icon),
            Task('Finch Samples', icon),
        ]

        self.itemModel = ItemModel(items)
        self.itemView = ItemView(self)
        self.itemView.setModel(self.itemModel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.itemView)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
