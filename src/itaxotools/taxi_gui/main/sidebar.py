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

from PySide6 import QtCore, QtGui, QtWidgets

from abc import ABC, abstractmethod

from itaxotools.common.utility import override

from .. import app
from ..model.common import Group, ItemModel, TreeItem


class ItemView(ABC):
    width: int
    height: int

    def __init__(self, item: TreeItem):
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
    width = 210
    height = 32
    marginLeft = 16
    marginBottom = 2

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        textRect = QtCore.QRect(option.rect)
        textRect.adjust(self.marginLeft, 0, 0, -self.marginBottom)
        font = painter.font()
        font.setPixelSize(16)
        painter.setFont(font)
        painter.drawText(textRect, QtCore.Qt.AlignBottom, self.item.object.name)

        line = QtCore.QLine(
            option.rect.left(),
            option.rect.bottom(),
            option.rect.right(),
            option.rect.bottom(),
        )
        painter.drawLine(line)


class EntryView(ItemView):
    width = 210
    height = 44
    marginLeft = 14
    marginText = 50
    iconSize = 32

    def __init__(self, item, icon=None):
        super().__init__(item)
        assert icon is not None
        self.icon = icon

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width, self.height)

    def paint(self, painter, option, index):
        if option.state & QtWidgets.QStyle.State_Selected:
            bg_brush = option.palette.highlight()
            text_color = option.palette.color(QtGui.QPalette.BrightText)
        elif option.state & QtWidgets.QStyle.State_MouseOver:
            bg_brush = option.palette.light()
            text_color = option.palette.color(QtGui.QPalette.Text)
        else:
            bg_brush = option.palette.mid()
            text_color = option.palette.color(QtGui.QPalette.Text)

        painter.setBrush(bg_brush)
        painter.drawRect(option.rect)

        rect = self.textRect(option)
        painter.setPen(text_color)
        painter.drawText(rect, QtCore.Qt.AlignVCenter, self.item.object.name)

        rect = self.iconRect(option)
        mode = QtGui.QIcon.Disabled
        if option.state & QtWidgets.QStyle.State_Selected:
            mode = QtGui.QIcon.Normal
        pix = self.icon.pixmap(QtCore.QSize(*[self.iconSize] * 2), mode)
        painter.drawPixmap(rect, pix)

    def iconRect(self, option):
        left = option.rect.left() + self.marginLeft
        vCenter = option.rect.center().y()
        return QtCore.QRect(
            left, vCenter - self.iconSize / 2 + 1, self.iconSize, self.iconSize
        )

    def textRect(self, option):
        rect = QtCore.QRect(option.rect)
        return rect.adjusted(self.marginText, 0, 0, 0)

    def mouseEvent(self, event, model, option, index):
        rect = self.iconRect(option)
        if rect.contains(event.pos()):
            name = index.data(QtCore.Qt.DisplayRole)
            print("clicked on", name)


class ItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        self.icon = app.resources.icons.arrow

    def indexView(self, index):
        item = index.data(ItemModel.ItemRole)
        if isinstance(item.object, Group):
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
            event.type() == QtCore.QEvent.MouseButtonRelease
            and event.button() == QtCore.Qt.LeftButton
        ):
            return super().event(event)
        view = self.indexView(index)
        view.mouseEvent(event, model, option, index)
        return super().event(event)


class ItemTreeView(QtWidgets.QTreeView):
    selected = QtCore.Signal(TreeItem, QtCore.QModelIndex)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setExpandsOnDoubleClick(False)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.setStyleSheet(
            """
            ItemTreeView {
                background: palette(Midlight);
                border: 0px solid transparent;
            }
        """
        )
        # self.setSpacing(2)
        self.setHeaderHidden(True)
        self.setIndentation(0)
        # ????? condense
        self.delegate = ItemDelegate(self)
        self.setItemDelegate(self.delegate)

    @override
    def currentChanged(self, current, previous):
        item = current.data(ItemModel.ItemRole)
        self.selected.emit(item, current)

    @override
    def sizeHint(self):
        w = self.sizeHintForColumn(0)
        h = self.sizeHintForRow(0)
        return QtCore.QSize(w, h)

    @override
    def setModel(self, model):
        super().setModel(model)
        model.focused.connect(self.setCurrentIndex)
        self.expandAll()


class SideBar(QtWidgets.QFrame):
    selected = QtCore.Signal(TreeItem, QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            """
            SideBar {
                border: 0px solid transparent;
                border-right: 1px solid palette(Dark);
            }
        """
        )
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )

        self.view = ItemTreeView(self)
        self.view.setModel(app.model.items)
        self.view.selected.connect(self.selected)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def clearSelection(self):
        self.view.setCurrentIndex(QtCore.QModelIndex())
