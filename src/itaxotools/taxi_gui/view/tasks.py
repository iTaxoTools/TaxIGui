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

from PySide6 import QtWidgets

from pathlib import Path

from itaxotools.common.bindings import Binder
from itaxotools.taxi_gui.view.widgets import DisplayFrame

from .. import app
from ..model.common import Object
from ..types import Notification
from .widgets import ScrollArea


class ObjectView(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.container = parent
        self.binder = Binder()
        self.object = None

    def ensureVisible(self):
        pass

    def setObject(self, object: Object):
        self.object = object
        self.binder.unbind_all()
        self.binder.bind(object.notification, self.showNotification)

    def showNotification(self, notification):
        icon = {
            Notification.Info: QtWidgets.QMessageBox.Information,
            Notification.Warn: QtWidgets.QMessageBox.Warning,
            Notification.Fail: QtWidgets.QMessageBox.Critical,
        }[notification.type]

        msgBox = QtWidgets.QMessageBox(self.window())
        msgBox.setWindowTitle(app.config.title)
        msgBox.setIcon(icon)
        msgBox.setText(notification.text)
        msgBox.setDetailedText(notification.info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.window().msgShow(msgBox)

    def getOpenPath(self, caption="Open File", dir="", filter=""):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f"{app.config.title} - {caption}", dir=dir, filter=filter
        )
        if not filename:
            return None
        return Path(filename)

    def getSavePath(self, caption="Save File", dir="", filter=""):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window(), f"{app.config.title} - {caption}", dir=dir, filter=filter
        )
        if not filename:
            return None
        return Path(filename)

    def getExistingDirectory(self, caption="Open Folder", dir="", filter=""):
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.window(), f"{app.config.title} - {caption}", dir=dir, filter=filter
        )
        if not filename:
            return None
        return Path(filename)

    def getConfirmation(self, title="Confirmation", text="Are you sure?"):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(f"{app.config.title} - {title}")
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText(text)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = self.window().msgShow(msgBox)
        return confirm == QtWidgets.QMessageBox.Yes


class TaskView(ObjectView):
    def start(self):
        self.object.start()

    def stop(self):
        if self.getConfirmation(
            "Stop diagnosis", "Are you sure you want to stop the ongoing diagnosis?"
        ):
            self.object.stop()

    def open(self):
        path = self.getOpenPath()
        if path:
            self.object.open(path)

    def save(self):
        path = self.getExistingDirectory(
            "Save All", str(self.object.suggested_directory)
        )
        if path:
            self.object.save(path)

    def clear(self):
        if self.getConfirmation(
            "Clear results", "Are you sure you want to clear all results and try again?"
        ):
            self.object.clear()


class ScrollTaskView(TaskView):
    def __init__(self, parent=None, max_width=920):
        super().__init__(parent)
        self.max_width = max_width
        self.area = ScrollArea(self)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.area, 1)
        super().setLayout(layout)

        self.frame = DisplayFrame(stretch=999, center_vertical=False)
        self.inner_frame = DisplayFrame(stretch=99, center_vertical=False)
        self.inner_frame.setStyleSheet("DisplayFrame {background: Palette(mid);}")
        self.inner_frame.setMaximumWidth(self.max_width)
        self.inner_frame.setContentsMargins(4, 8, 4, 8)
        self.area.setWidget(self.frame)
        self.frame.setWidget(self.inner_frame)

    def ensureVisible(self):
        self.area.ensureVisible(0, 0)

    def start(self):
        self.area.ensureVisible(0, 0)
        super().start()

    def setWidget(self, widget):
        """Children may populate the view here"""
        self.inner_frame.setWidget(widget)

    def setLayout(self, layout):
        """Children may populate the view here"""
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setWidget(widget)
