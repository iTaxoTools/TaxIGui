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

"""Main dialog window"""

from PySide6 import QtCore, QtGui, QtWidgets

import shutil
from pathlib import Path

from itaxotools.common.utility import AttrDict
from itaxotools.common.widgets import ToolDialog

from .. import app
from ..model import BulkSequencesModel, SequenceModel
from .body import Body
from .footer import Footer
from .header import Header
from .sidebar import SideBar


class Main(ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)

        self.title = 'Taxi3'

        self.setWindowIcon(app.resources.icons.app)
        self.setWindowTitle(self.title)
        self.resize(800, 500)

        self.draw()
        self.act()

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.sidebar = SideBar(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        self.widgets.sidebar.selected.connect(self.widgets.body.showItem)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.widgets.header, 0, 0, 1, 2)
        layout.addWidget(self.widgets.sidebar, 1, 0, 1, 1)
        layout.addWidget(self.widgets.body, 1, 1, 1, 1)
        layout.addWidget(self.widgets.footer, 2, 0, 1, 2)
        layout.setSpacing(0)
        layout.setColumnStretch(1, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def act(self):
        """Populate dialog actions"""
        self.actions = {}

        self.actions['home'] = QtGui.QAction('&Home', self)
        self.actions['home'].setIcon(app.resources.icons.home)
        self.actions['home'].setStatusTip('Open the dashboard')
        self.actions['home'].triggered.connect(self.handleHome)

        self.actions['open'] = QtGui.QAction('&Open', self)
        self.actions['open'].setIcon(app.resources.icons.open)
        self.actions['open'].setShortcut(QtGui.QKeySequence.Open)
        self.actions['open'].setStatusTip('Open an existing file')
        self.actions['open'].triggered.connect(self.handleOpen)

        self.actions['save'] = QtGui.QAction('&Save', self)
        self.actions['save'].setIcon(app.resources.icons.save)
        self.actions['save'].setShortcut(QtGui.QKeySequence.Save)
        self.actions['save'].setStatusTip('Save results')
        self.actions['save'].triggered.connect(self.handleSave)

        self.widgets.header.toolBar.addAction(self.actions['home'])
        self.widgets.header.toolBar.addAction(self.actions['open'])
        self.widgets.header.toolBar.addAction(self.actions['save'])

    def handleHome(self):
        self.widgets.body.showDashboard()

    def handleOpen(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, f'{self.title} - Open File')
        if not filenames:
            return
        if len(filenames) == 1:
            path = Path(filenames[0])
            app.model.items.add_sequence(SequenceModel(path))
        else:
            paths = [Path(filename) for filename in filenames]
            app.model.items.add_sequence(BulkSequencesModel(paths))

    def handleSave(self):
        try:
            self._handleSave()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, self.title, str(exception))

    def _handleSave(self):
        item = self.widgets.body.activeItem
        if not item:
            QtWidgets.QMessageBox.information(self, self.title, 'Please select a sequence and try again.')
            return
        if isinstance(item.object, SequenceModel):
            source = item.object.path
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, f'{self.title} - Save File',
                QtCore.QDir.currentPath() + '/' + source.name)
            if not filename:
                return
            destination = Path(filename)
            shutil.copy(source, destination)
            return
        if isinstance(item.object, BulkSequencesModel):
            filename = QtWidgets.QFileDialog.getExistingDirectory(
                self, f'{self.title} - Save Bulk Files',
                QtCore.QDir.currentPath())
            if not filename:
                return
            directory = Path(filename)
            for sequence in item.object.sequences:
                source = sequence.path
                destination = directory / source.name
                shutil.copy(source, destination)
            return
        QtWidgets.QMessageBox.information(self, self.title, 'Please select a sequence and try again.')
