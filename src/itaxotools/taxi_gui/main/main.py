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

"""Main dialog window"""

from PySide6 import QtGui, QtWidgets

from types import ModuleType

from itaxotools.common.utility import AttrDict
from itaxotools.common.widgets import ToolDialog

from .. import app
from .body import Body
from .footer import Footer
from .header import Header
from .sidebar import SideBar


class Main(ToolDialog):
    """Main window, hosts all tasks and actions"""

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        icon = app.config.icon.resource
        if icon is not None:
            self.setWindowIcon(icon)
        self.setWindowTitle(app.config.title)
        self.resize(680, 500)

        self.act()
        self.draw()

        self.addTasks(app.config.tasks)

    def act(self):
        """Populate dialog actions"""
        self.actions = AttrDict()

        action = QtGui.QAction("&Home", self)
        action.setIcon(app.resources.icons.home.resource)
        action.setStatusTip("Open the dashboard")
        action.triggered.connect(self.handleHome)
        action.setVisible(len(app.config.tasks) > 1)
        self.actions.home = action

        action = QtGui.QAction("&Open", self)
        action.setIcon(app.resources.icons.open.resource)
        action.setShortcut(QtGui.QKeySequence.Open)
        action.setStatusTip("Open an existing file")
        action.setVisible(app.config.show_open)
        self.actions.open = action

        action = QtGui.QAction("&Save", self)
        action.setIcon(app.resources.icons.save.resource)
        action.setShortcut(QtGui.QKeySequence.Save)
        action.setStatusTip("Save results")
        action.setVisible(app.config.show_save)
        self.actions.save = action

        action = QtGui.QAction("&Run", self)
        action.setIcon(app.resources.icons.run.resource)
        action.setShortcut("Ctrl+R")
        action.setStatusTip("Run MolD")
        self.actions.start = action

        action = QtGui.QAction("S&top", self)
        action.setIcon(app.resources.icons.stop.resource)
        action.setShortcut(QtGui.QKeySequence.Cancel)
        action.setStatusTip("Stop MolD")
        self.actions.stop = action

        action = QtGui.QAction("Cl&ear", self)
        action.setIcon(app.resources.icons.clear.resource)
        action.setShortcut("Ctrl+E")
        action.setStatusTip("Stop MolD")
        self.actions.clear = action

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.sidebar = SideBar(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        self.widgets.sidebar.setVisible(False)

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

    def addTasks(self, tasks: list[ModuleType | list[ModuleType]]):
        for task in tasks:
            if isinstance(task, list):
                for subtask in task:
                    subtask = app.Task.from_module(subtask)
                    self.addTask(subtask)
                self.widgets.body.dashboard.addSeparator()
            else:
                task = app.Task.from_module(task)
                self.addTask(task)

        if len(tasks) == 1:
            self.widgets.body.dashboard.addTaskIfNew(task.model)

    def addTask(self, task):
        self.widgets.body.addView(task.model, task.view)
        self.widgets.body.dashboard.addTaskItem(task)

    def handleHome(self):
        self.widgets.body.showDashboard()
        self.widgets.sidebar.clearSelection()

    def reject(self):
        if app.model.main.dirty_data:
            return super().reject()
        return True
