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
    def __init__(self, parent=None):
        super().__init__(QtWidgets.QBoxLayout.TopToBottom, parent)

    def __iter__(self):
        for index in range(self.count()):
            yield self.itemAt(index)

    def _isItemVisible(self, item):
        if isinstance(item, QtWidgets.QWidget):
            return item.isVisible()
        elif isinstance(item, QtWidgets.QWidgetItem):
            return item.widget().isVisible()
        return True

    def _iterVisibleItemHeights(self, width=-1):
        for item in self:
            if not self._isItemVisible(item):
                continue
            if item.hasHeightForWidth():
                yield item.heightForWidth(width)
            else:
                yield item.sizeHint().height()

    def expandingDirections(self):
        return QtCore.Qt.Vertical

    def minimumSize(self):
        return self.sizeHint()

    def minimumHeightForWidth(self, width):
        return self.heightForWidth(width)

    def hasHeightForWidth(self):
        for item in self:
            if item.hasHeightForWidth():
                return True
        return False

    def heightForWidth(self, width):
        margins = self.contentsMargins()
        width -= margins.left() + margins.right()
        height = margins.top() + margins.bottom()

        for item_height in self._iterVisibleItemHeights(width):
            height += item_height

        visible = sum(1 for item in self if self._isItemVisible(item))
        if visible > 1:
            height += (visible - 1) * self.spacing()

        return height

    def minimumWidth(self):
        margins = self.contentsMargins()
        width = margins.left() + margins.right()

        for item in self:
            if not self._isItemVisible(item):
                continue
            width = max(width, item.sizeHint().width())

        return width

    def sizeHint(self):
        width = self.minimumWidth()
        height = self.heightForWidth(width)
        size = QtCore.QSize(width, height)
        return size

    def setGeometry(self, rect):
        margins = self.contentsMargins()
        rect = rect.marginsRemoved(margins)

        width = rect.width()
        height = rect.height()
        yy_incr = height / self.count() if self.count() else 0
        xx = rect.x()
        yy = rect.y()
        for item in self:
            item_rect = QtCore.QRect(xx, yy, width, yy_incr)
            if not self._isItemVisible(item):
                continue
            if item.hasHeightForWidth():
                height = item.heightForWidth(width)
            else:
                height = item.sizeHint().height()
            item_rect.setHeight(height)
            item.setGeometry(item_rect)
            yy += height
            yy += self.spacing()

    def separatorPositions(self, width=-1):
        positions = []
        cursor = self.contentsMargins().top()
        for height in self._iterVisibleItemHeights(width):
            cursor += height
            position = cursor + self.spacing() / 2
            positions.append(position)
            cursor += self.spacing()
        return positions[:-1]


class Card(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")
        self.roll_animation = VerticalRollAnimation(self)
        self.controls = AttrDict()
        self.separator_margin = 8

        layout = CardLayout()
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(24)
        self.setLayout(layout)

    def addWidget(self, widget):
        self.layout().addWidget(widget)

    def addLayout(self, widget):
        self.layout().addLayout(widget)

    @override
    def update(self):
        self.layout().invalidate()
        super().update()

    @override
    def setVisible(self, value):
        super().setVisible(value)
        self.update()

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

        left = self.separator_margin
        right = self.width() - self.separator_margin

        for position in self.layout().separatorPositions(self.width()):
            painter.drawLine(left, position, right, position)
