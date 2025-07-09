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

from PySide6 import QtCore, QtGui, QtWidgets

from types import ModuleType

from itaxotools.common.utility import AttrDict, override
from itaxotools.common.widgets import ToolDialog

from .. import app
from ..types import ChildAction
from .body import Body
from .footer import Footer
from .header import Header
from .sidebar import SideBar


class ParentAction(QtGui.QAction):
    triggered_child = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._button = None
        self._action = None
        self._children: dict[QtGui.QAction, str] = {}
        self._menu = QtWidgets.QMenu()
        self._menu.setMinimumWidth(160)
        self._menu.setStyleSheet(
            """
            QMenu {
                border: 1px solid palette(Mid);
                background-color: palette(Light);
            }

            QMenu::item {
                padding: 4px 8px;
                padding-left: 16px;
                color: Palette(Text);
            }

            QMenu::item:selected {
                background-color: Palette(Highlight);
                color: Palette(Light);
            }

            QMenu::icon {
                width: 0px;
            }
        """
        )

    def setActions(self, actions: list[ChildAction]):
        self._menu.clear()
        for child in actions:
            action = QtGui.QAction(child.label, self)
            action.setStatusTip(child.tip)
            action.triggered.connect(self._handle_child_trigger)
            self._menu.addAction(action)
            self._children[action] = child.key

    def clearActions(self):
        self._children.clear()
        self._menu.clear()

    def generateToolButton(self):
        self._button = QtWidgets.QToolButton()
        self._button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self._button.setDefaultAction(self)
        self._button.setMenu(self._menu)
        self._action = QtWidgets.QWidgetAction(self)
        self._action.setDefaultWidget(self._button)
        self._action.setVisible(False)
        return self._button, self._action

    def _handle_child_trigger(self):
        key = self._children[self.sender()]
        self.triggered_child.emit(key)

    @override
    def setEnabled(self, value: bool):
        super().setEnabled(value)
        if self._action:
            self._action.setEnabled(value)

    @override
    def setVisible(self, value: bool):
        if not self._action:
            super().setVisible(value)
            return
        if self._children:
            super().setVisible(False)
            self._action.setVisible(value)
        else:
            super().setVisible(value)
            self._action.setVisible(False)


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

        action = ParentAction("&Open", self)
        action.setIcon(app.resources.icons.open.resource)
        action.setShortcut(QtGui.QKeySequence.Open)
        action.setStatusTip("Open an existing file")
        action.setVisible(app.config.show_open)
        self.actions.open = action

        action = ParentAction("&Save", self)
        action.setIcon(app.resources.icons.save.resource)
        action.setShortcut(QtGui.QKeySequence.Save)
        action.setStatusTip("Save results")
        action.setVisible(app.config.show_save)
        self.actions.save = action

        action = ParentAction("&Export", self)
        action.setIcon(app.resources.icons.export.resource)
        action.setShortcut("Ctrl+E")
        action.setStatusTip("Export results")
        action.setVisible(app.config.show_export)
        self.actions.export = action

        action = QtGui.QAction("&Run", self)
        action.setIcon(app.resources.icons.run.resource)
        action.setShortcut("Ctrl+R")
        action.setStatusTip("Run analysis")
        self.actions.start = action

        action = QtGui.QAction("S&top", self)
        action.setIcon(app.resources.icons.stop.resource)
        action.setShortcut(QtGui.QKeySequence.Cancel)
        action.setStatusTip("Stop analysis")
        self.actions.stop = action

        action = QtGui.QAction("C&lear", self)
        action.setIcon(app.resources.icons.clear.resource)
        action.setShortcut("Ctrl+L")
        action.setStatusTip("Clear results")
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
            self.addToolBarAction(action)

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

    def addToolBarAction(self, action: QtGui.QAction):
        self.widgets.header.toolBar.addAction(action)
        if isinstance(action, ParentAction):
            _, widget_action = action.generateToolButton()
            self.widgets.header.toolBar.addAction(widget_action)

    def addTasks(self, tasks: list[ModuleType | list[ModuleType]]):
        for task in tasks:
            if isinstance(task, list):
                if not task:
                    self.addSeparator()
                elif isinstance(task[0], str):
                    self.addCaption(task[0], *task[1:])
                else:
                    for subtask in task:
                        subtask = app.Task.from_module(subtask)
                        self.addTask(subtask)
                    self.addSeparator()
            else:
                task = app.Task.from_module(task)
                self.addTask(task)

        if len(tasks) == 1:
            self.widgets.body.dashboard.addTaskIfNew(task.model)

    def addTask(self, task):
        self.widgets.body.addView(task.model, task.view)
        self.widgets.body.dashboard.addTaskItem(task)

    def addSeparator(self):
        self.widgets.body.dashboard.addSeparator()

    def addCaption(self, task: str, *args):
        self.widgets.body.dashboard.addCaptionItem(task, *args)

    def handleHome(self):
        self.widgets.body.showDashboard()
        self.widgets.sidebar.clearSelection()

    def reject(self):
        if app.model.main.dirty_data:
            return super().reject()
        return True

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.BackButton:
            self.actions.home.trigger()
