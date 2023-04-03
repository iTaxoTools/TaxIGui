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

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from .. import app
from ..model.common import Item, ItemModel, Object
from ..types import ComparisonMode, Notification, PairwiseComparisonConfig
from ..utility import Guard, Binder


class ObjectView(QtWidgets.QFrame):

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.container = parent
        self.binder = Binder()
        self.object = None

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
        msgBox.setWindowTitle(app.title)
        msgBox.setIcon(icon)
        msgBox.setText(notification.text)
        msgBox.setDetailedText(notification.info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.window().msgShow(msgBox)

    def getOpenPath(self, caption='Open File', dir='', filter=''):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f'{app.title} - {caption}', dir, filter=filter)
        if not filename:
            return None
        return Path(filename)

    def getSavePath(self, caption='Open File', dir=''):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)

    def getExistingDirectory(self, caption='Open File', dir=''):
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)

    def getConfirmation(self, title='Confirmation', text='Are you sure?'):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(f'{app.title} - {title}')
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText(text)
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = self.window().msgShow(msgBox)
        return confirm == QtWidgets.QMessageBox.Yes


class TaskView(ObjectView):

    def start(self):
        self.container.ensureVisible(0, 0)
        self.object.start()

    def stop(self):
        if self.getConfirmation(
            'Stop diagnosis',
            'Are you sure you want to stop the ongoing diagnosis?'
        ):
            self.object.stop()

    def save(self):
        path = self.getExistingDirectory(
            'Save All', str(self.object.suggested_directory))
        if path:
            self.object.save_all(path)

    def clear(self):
        if self.getConfirmation(
            'Clear results',
            'Are you sure you want to clear all results and try again?'
        ):
            self.object.clear()
