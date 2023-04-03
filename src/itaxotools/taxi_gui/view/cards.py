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

from itaxotools.common.utility import AttrDict, override

from .animations import VerticalRollAnimation


class CardLayout(QtWidgets.QBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(QtWidgets.QBoxLayout.TopToBottom)
        # self.setContentsMargins(8, 8, 8, 8)

    def expandingDirections(self):
        return QtCore.Qt.Vertical

    def hasHeightForWidth(self):
        return False

    def setGeometry(self, rect):
        super().setGeometry(rect)

        margins = self.contentsMargins()
        rect.adjust(margins.left(), margins.top(), -margins.right(), -margins.bottom())

        width = rect.width()
        height = rect.height()
        yy_incr = height / self.count()
        xx = rect.x()
        yy = rect.y()
        for index in range(self.count()):
            item = self.itemAt(index)
            item_rect = QtCore.QRect(xx, yy, width, yy_incr)
            if isinstance(item, QtWidgets.QWidget) and not item.isVisible():
                continue
            if isinstance(item, QtWidgets.QWidgetItem) and not item.widget().isVisible():
                continue
            item_rect.setHeight(item.sizeHint().height())
            item.setGeometry(item_rect)
            yy += item.sizeHint().height()
            yy += self.spacing()

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        width = 0
        height = 0
        visible = 0
        for index in range(self.count()):
            item = self.itemAt(index)
            if isinstance(item, QtWidgets.QWidget) and not item.isVisible():
                continue
            if isinstance(item, QtWidgets.QWidgetItem) and not item.widget().isVisible():
                continue
            visible += 1
            width = max(width, item.sizeHint().width())
            height += item.sizeHint().height()
        if visible > 1:
            height += (visible - 1) * self.spacing()
        size = QtCore.QSize(width, height)

        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

        return size


class Card(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")
        self.roll_animation = VerticalRollAnimation(self)
        self.controls = AttrDict()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(24)
        self.setLayout(layout)

    def addWidget(self, widget):
        self.layout().addWidget(widget)

    def addLayout(self, widget):
        self.layout().addLayout(widget)

    @override
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.layout().count():
            self.paintSeparators()

    def paintSeparators(self):
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        painter.setPen(option.palette.color(QtGui.QPalette.Mid))

        layout = self.layout()
        frame = layout.contentsRect()
        left = frame.left()
        right = frame.right()

        items = [
            item for item in (layout.itemAt(id) for id in range(0, layout.count()))
            if item.widget() and item.widget().isVisible()
            or item.layout()
        ]
        pairs = zip(items[:-1], items[1:])

        for first, second in pairs:
            bottom = first.geometry().bottom()
            top = second.geometry().top()
            middle = (bottom + top) / 2
            painter.drawLine(left, middle, right, middle)


class CardCustom(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""CardCustom{background: Palette(Midlight);}""")
        self.roll_animation = VerticalRollAnimation(self)
        self.controls = AttrDict()

        layout = CardLayout()
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(24)
        self.setLayout(layout)

    def addWidget(self, widget):
        self.layout().addWidget(widget)

    def addLayout(self, widget):
        self.layout().addLayout(widget)

    @override
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.layout().count():
            self.paintSeparators()

    def paintSeparators(self):
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        painter.setPen(option.palette.color(QtGui.QPalette.Mid))

        layout = self.layout()
        frame = layout.contentsRect()
        left = frame.left()
        right = frame.right()

        items = [
            item for item in (layout.itemAt(id) for id in range(0, layout.count()))
            if item.widget() and item.widget().isVisible()
            or item.layout()
        ]
        pairs = zip(items[:-1], items[1:])

        for first, second in pairs:
            bottom = first.geometry().bottom()
            top = second.geometry().top()
            middle = (bottom + top) / 2
            painter.drawLine(left, middle, right, middle)
