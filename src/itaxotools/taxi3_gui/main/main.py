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
from ..utility import PropertyObject, Property
from .body import Body
from .footer import Footer
from .header import Header
from .sidebar import SideBar


class MainState(PropertyObject):
    dirty_data = Property(bool, True)
    busy = Property(bool, False)


class Main(ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)
        self.state = MainState()

        self.setWindowIcon(app.resources.icons.app)
        self.setWindowTitle(app.title)
        self.resize(800, 500)

        self.act()
        self.draw()

    def act(self):
        """Populate dialog actions"""
        self.actions = AttrDict()

        action = QtGui.QAction('&Home', self)
        action.setIcon(app.resources.icons.home)
        action.setStatusTip('Open the dashboard')
        action.triggered.connect(self.handleHome)
        self.actions.home = action

        action = QtGui.QAction('&Open', self)
        action.setIcon(app.resources.icons.open)
        action.setShortcut(QtGui.QKeySequence.Open)
        action.setStatusTip('Open an existing file')
        action.triggered.connect(self.handleOpen)
        self.actions.open = action

        action = QtGui.QAction('&Save', self)
        action.setIcon(app.resources.icons.save)
        action.setShortcut(QtGui.QKeySequence.Save)
        action.setStatusTip('Save results')
        action.triggered.connect(self.handleSave)
        self.actions.save = action

        action = QtGui.QAction('&Run', self)
        action.setIcon(app.resources.icons.run)
        action.setShortcut('Ctrl+R')
        action.setStatusTip('Run MolD')
        self.actions.start = action

        action = QtGui.QAction('S&top', self)
        action.setIcon(app.resources.icons.stop)
        action.setShortcut(QtGui.QKeySequence.Cancel)
        action.setStatusTip('Stop MolD')
        self.actions.stop = action

        action = QtGui.QAction('Cl&ear', self)
        action.setIcon(app.resources.icons.clear)
        action.setShortcut('Ctrl+E')
        action.setStatusTip('Stop MolD')
        self.actions.clear = action

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.sidebar = SideBar(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        for action in self.actions:
            self.widgets.header.toolBar.addAction(action)
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

    def handleHome(self):
        self.widgets.body.showDashboard()
        self.widgets.sidebar.clearSelection()

    def handleOpen(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, f'{app.title} - Open File')
        if not filenames:
            return
        if len(filenames) == 1:
            path = Path(filenames[0])
            app.model.items.add_sequence(SequenceModel(path), focus=True)
        else:
            paths = [Path(filename) for filename in filenames]
            app.model.items.add_sequence(BulkSequencesModel(paths), focus=True)

    def handleSave(self):
        try:
            self._handleSave()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, app.title, str(exception))

    def _handleSave(self):
        item = self.widgets.body.activeItem
        if not item:
            QtWidgets.QMessageBox.information(self, app.title, 'Please select a sequence and try again.')
            return
        if isinstance(item.object, SequenceModel):
            source = item.object.path
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, f'{app.title} - Save File',
                QtCore.QDir.currentPath() + '/' + source.name)
            if not filename:
                return
            destination = Path(filename)
            shutil.copy(source, destination)
            return
        if isinstance(item.object, BulkSequencesModel):
            filename = QtWidgets.QFileDialog.getExistingDirectory(
                self, f'{app.title} - Save Bulk Files',
                QtCore.QDir.currentPath())
            if not filename:
                return
            directory = Path(filename)
            for sequence in item.object.sequences:
                source = sequence.path
                destination = directory / source.name
                shutil.copy(source, destination)
            return
        QtWidgets.QMessageBox.information(self, app.title, 'Please select a sequence and try again.')

    def reject(self):
        if self.state.dirty_data:
            return super().reject()
        return True
