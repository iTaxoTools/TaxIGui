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

from itaxotools.common.utility import override

from .. import app
from ..model.tasks import TaskModel


class DashItem(QtWidgets.QAbstractButton):

    def __init__(self, text, subtext, slot, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.subtext = subtext
        self.clicked.connect(slot)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self._mouseOver = False
        self.pad_x = 4
        self.pad_y = 4
        self.pad_text = 18
        self.bookmark_width = 2

    @override
    def sizeHint(self):
        return QtCore.QSize(260, 90)

    @override
    def event(self, event):
        if isinstance(event, QtGui.QEnterEvent):
            self._mouseOver = True
            self.update()
        elif (
            isinstance(event, QtCore.QEvent) and
            event.type() == QtCore.QEvent.Leave
        ):
            self._mouseOver = False
            self.update()
        return super().event(event)

    @override
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = QtCore.QRect(0, 0, self.width(), self.height())
        palette = QtGui.QGuiApplication.palette()
        self.paintBack(painter, rect, palette)
        self.paintText(painter, rect, palette)
        self.paintSubtext(painter, rect, palette)

    def paintBack(self, painter, rect, palette):
        bg = palette.color(QtGui.QPalette.Midlight)
        if self._mouseOver:
            bg = palette.color(QtGui.QPalette.Light)
        painter.fillRect(rect, bg)

        rect = rect.adjusted(self.pad_x, self.pad_y, 0, -self.pad_y)
        rect.setWidth(self.bookmark_width)
        painter.fillRect(rect, palette.color(QtGui.QPalette.Mid))

    def paintText(self, painter, rect, palette):
        painter.save()
        rect = rect.adjusted(self.pad_text, self.pad_y, -self.pad_x, -self.pad_y)
        rect.setHeight(rect.height() / 2)

        font = painter.font()
        font.setPixelSize(18)
        font.setBold(True)
        font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)
        painter.setFont(font)

        text_color = palette.color(QtGui.QPalette.Text)
        painter.setPen(text_color)

        painter.drawText(rect, QtCore.Qt.AlignBottom, self.text())
        painter.restore()

    def paintSubtext(self, painter, rect, palette):
        text_color = palette.color(QtGui.QPalette.Shadow)
        painter.setPen(text_color)

        rect = rect.adjusted(self.pad_text, self.pad_y, -self.pad_x, -self.pad_y)
        rect.setTop(rect.top() + self.pad_y + rect.height() / 2)
        painter.drawText(rect, QtCore.Qt.AlignTop, self.subtext)


class Dashboard(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_count = 0

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            Dashboard {
                background: Palette(dark);
            }
            """)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(6)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(5, 1)
        layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(layout)

    def addTaskItem(self, task):
        row, column = divmod(self._task_count, 2)
        item = DashItem(
            task.title,
            task.description,
            lambda: self.addTaskIfNew(task.model),
            self)
        self.layout().addWidget(item, row, column)
        self._task_count += 1

    def addTaskIfNew(self, type: TaskModel):
        index = app.model.items.find_task(type)
        if index is None:
            index = app.model.items.add_task(type())
        app.model.items.focus(index)
