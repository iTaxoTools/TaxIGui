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
from itaxotools.taxi_gui.view.widgets import DisplayFrame

from .. import app
from ..model.tasks import TaskModel


class DashItem(QtWidgets.QAbstractButton):
    pass


class DashItemLegacy(DashItem):
    def __init__(self, text, subtext, pixmap, slot, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.subtext = subtext
        self.pixmap = pixmap
        self.clicked.connect(slot)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self._mouseOver = False
        self.pad_x = 4
        self.pad_y = 4
        self.pad_text = 20
        self.pad_pixmap = 8
        self.bookmark_width = 2

    @override
    def sizeHint(self):
        return QtCore.QSize(260, 90)

    @override
    def event(self, event):
        if isinstance(event, QtGui.QEnterEvent):
            self._mouseOver = True
            self.update()
        elif isinstance(event, QtCore.QEvent) and event.type() == QtCore.QEvent.Leave:
            self._mouseOver = False
            self.update()
        return super().event(event)

    @override
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        rect = QtCore.QRect(0, 0, self.width(), self.height())
        palette = QtGui.QGuiApplication.palette()
        self.paintBack(painter, rect, palette)
        self.paintPixmap(painter, rect, palette)
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

    def paintPixmap(self, painter, rect, palette):
        if self.pixmap is None:
            return
        pix_rect = QtCore.QRect(rect)
        pix_rect.setWidth(pix_rect.height())
        pix_rect.moveLeft(self.pad_text / 2)
        pix_rect.adjust(
            self.pad_pixmap, self.pad_pixmap, -self.pad_pixmap, -self.pad_pixmap
        )
        painter.drawPixmap(pix_rect, self.pixmap)
        rect.adjust(pix_rect.width() + self.pad_text, 0, 0, 0)

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


class DashItemConstrained(DashItem):
    def __init__(self, text, subtext, pixmap, slot, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.subtext = subtext
        self.pixmap = pixmap
        self.clicked.connect(slot)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )
        self._mouseOver = False
        self.pad_x = 4
        self.pad_y = 4
        self.pad_text = 20
        self.pad_pixmap = 16
        self.bookmark_width = 2

        self._text_font = self.font()
        self._text_font.setPixelSize(20)
        self._text_font.setBold(True)
        self._text_font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)

        self._subtext_font = self.font()
        self._subtext_font.setPixelSize(16)
        self._subtext_font.setBold(False)

        self._size_hint = self._refresh_size_hint()
        self.setMaximumHeight(160)
        self.setMaximumWidth(720)

    @override
    def sizeHint(self):
        return QtCore.QSize(self._size_hint)

    @override
    def event(self, event):
        if isinstance(event, QtGui.QEnterEvent):
            self._mouseOver = True
            self.update()
        elif isinstance(event, QtCore.QEvent) and event.type() == QtCore.QEvent.Leave:
            self._mouseOver = False
            self.update()
        return super().event(event)

    @override
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        rect = QtCore.QRect(0, 0, self.width(), self.height())
        palette = QtGui.QGuiApplication.palette()
        self.paintBack(painter, rect, palette)
        self.paintPixmap(painter, rect, palette)
        self.paintText(painter, rect, palette)
        self.paintSubtext(painter, rect, palette)

    @override
    def resizeEvent(self, event):
        width = self._refresh_size_hint(self.height()).width()
        self.setMinimumWidth(width)
        return super().resizeEvent(event)

    def _refresh_size_hint(self, height=None):
        height = height or 100
        width = 2 * self.pad_x + 2 * self.pad_text
        if self.pixmap is not None:
            width += height
        text_metrics = QtGui.QFontMetrics(self._text_font)
        subtext_metrics = QtGui.QFontMetrics(self._subtext_font)
        text_width = text_metrics.horizontalAdvance(self.text())
        subtext_width = subtext_metrics.horizontalAdvance(self.subtext)
        width += max(text_width, subtext_width)
        return QtCore.QSize(width, height)

    def paintBack(self, painter, rect, palette):
        bg = palette.color(QtGui.QPalette.Midlight)
        if self._mouseOver:
            bg = palette.color(QtGui.QPalette.Light)
        painter.fillRect(rect, bg)

        rect = rect.adjusted(self.pad_x, self.pad_y, 0, -self.pad_y)
        rect.setWidth(self.bookmark_width)
        painter.fillRect(rect, palette.color(QtGui.QPalette.Mid))

    def paintPixmap(self, painter, rect, palette):
        if self.pixmap is None:
            return
        pix_rect = QtCore.QRect(rect)
        pix_rect.setWidth(pix_rect.height())
        pix_rect.moveLeft(self.pad_text / 4)
        pix_rect.adjust(
            self.pad_pixmap, self.pad_pixmap, -self.pad_pixmap, -self.pad_pixmap
        )
        painter.drawPixmap(pix_rect, self.pixmap)
        rect.adjust(pix_rect.width() + self.pad_text, 0, 0, 0)

    def paintText(self, painter, rect, palette):
        painter.save()
        rect = rect.adjusted(self.pad_text, self.pad_y, -self.pad_x, -self.pad_y)
        rect.setHeight(rect.height() / 2)

        painter.setFont(self._text_font)

        text_color = palette.color(QtGui.QPalette.Text)
        painter.setPen(text_color)

        painter.drawText(rect, QtCore.Qt.AlignBottom, self.text())
        painter.restore()

    def paintSubtext(self, painter, rect, palette):
        painter.save()

        painter.setFont(self._subtext_font)

        text_color = palette.color(QtGui.QPalette.Shadow)
        painter.setPen(text_color)

        rect = rect.adjusted(self.pad_text, self.pad_y, -self.pad_x, -self.pad_y)
        rect.setTop(rect.top() + self.pad_y + rect.height() / 2)

        painter.drawText(rect, QtCore.Qt.AlignTop, self.subtext)
        painter.restore()


class Dashboard(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet("Dashboard {background: Palette(dark);}")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )

    def addTaskItem(self, task: app.Task):
        raise NotImplementedError()

    def addTaskIfNew(self, task: app.Task):
        raise NotImplementedError()

    def addSeparator(self):
        raise NotImplementedError()


class DashboardLegacy(Dashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_count = 0

        self.setStyleSheet("DashboardLegacy {background: Palette(dark);}")

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(6)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(5, 1)
        layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(layout)

    def addTaskItem(self, task):
        row, column = divmod(self._task_count, 2)
        item = DashItemLegacy(
            text=task.title,
            subtext=task.description,
            pixmap=task.pixmap.resource,
            slot=lambda: self.addTaskIfNew(task.model),
            parent=self,
        )
        self.layout().addWidget(item, row, column)
        self._task_count += 1

    def addTaskIfNew(self, type: TaskModel):
        index = app.model.items.find_task(type)
        if index is None:
            index = app.model.items.add_task(type())
        app.model.items.focus(index)

    def addSeparator(self):
        pass


class DashboardConstrained(Dashboard):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        task_layout = QtWidgets.QVBoxLayout()
        task_layout.setContentsMargins(6, 6, 6, 6)
        task_layout.setSpacing(12)

        stretch_layout = QtWidgets.QHBoxLayout()
        stretch_layout.addStretch(1)
        stretch_layout.addLayout(task_layout, 9)
        stretch_layout.addStretch(1)

        task_widget = QtWidgets.QFrame()
        task_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )
        task_widget.setLayout(stretch_layout)

        frame = DisplayFrame(stretch=5, parent=self)
        frame.setWidget(task_widget)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frame, 1)
        self.setLayout(layout)

        self.task_layout = task_layout

    def addTaskItem(self, task):
        item = DashItemConstrained(
            text=task.title,
            subtext=task.description,
            pixmap=task.pixmap.resource,
            slot=lambda: self.addTaskIfNew(task.model),
            parent=self,
        )
        self.task_layout.addWidget(item, 7)

    def addTaskIfNew(self, type: TaskModel):
        index = app.model.items.find_task(type)
        if index is None:
            index = app.model.items.add_task(type())
        app.model.items.focus(index)

    def addSeparator(self):
        self.task_layout.addSpacing(16)
        self.task_layout.addStretch(1)
