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


class Group(Item):

    width = 256
    height = 32
    marginLeft = 4
    marginBottom = 2

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        # if option.state & QtWidgets.QStyle.State_Selected:
        #     painter.fillRect(option.rect, option.palette.dark())
        # elif option.state & QtWidgets.QStyle.State_MouseOver:
        #     painter.fillRect(option.rect, option.palette.dark())
        # else:
        #     painter.fillRect(option.rect, option.palette.dark())

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
    marginLeft = 8

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillRect(option.rect, option.palette.light())
        else:
            painter.fillRect(option.rect, option.palette.mid())

        textRect = QtCore.QRect(option.rect)
        textRect.adjust(self.marginLeft, 0, 0, 0)
        painter.drawText(textRect, QtCore.Qt.AlignVCenter, self.name)


class ItemModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()

        self.items = [
            Group('Tasks'),
            Task('DEREP #1'),
            Task('DEREP #2'),
            Task('DECONT'),
            Group('Sequences'),
            Task('Frog Samples'),
            Task('Finch Samples'),
        ]

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

    ### CLICKABLE REGIONS:
    ### https://forum.qt.io/topic/28142/detect-clicked-icon-of-item-solved/5
    # def editorEvent(self, event, model, option, index):
    #     print(event)
    #     return super().event(event)

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

        self.itemModel = ItemModel()
        self.itemView = ItemView()
        self.itemView.setModel(self.itemModel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.itemView)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
