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

from PySide6 import QtCore, QtWidgets

from itaxotools.common.bindings import Binder

from .. import app
from ..model.common import TreeItem
from ..model.tasks import TaskModel
from ..view.tasks import TaskView
from .dashboard import DashboardConstrained, DashboardLegacy


class Body(QtWidgets.QStackedWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.actions = parent.actions
        self.activeItem = None
        self.activeIndex = None
        self.binder = Binder()
        self.views = dict()

        match app.config.dashboard:
            case "legacy":
                dashboard_class = DashboardLegacy
            case "constrained":
                dashboard_class = DashboardConstrained
            case _:
                raise ValueError(
                    f"Invalid dashboard config: {repr(app.config.dashboard)}"
                )
        self.dashboard = dashboard_class(self)
        self.addWidget(self.dashboard)

        self.showDashboard()

    def addView(self, object_type, view_type, *args, **kwargs):
        view = view_type(parent=self, *args, **kwargs)
        self.views[object_type] = view
        self.addWidget(view)

    def showItem(self, item: TreeItem, index: QtCore.QModelIndex):
        self.activeItem = item
        self.activeIndex = index
        if not item or not index.isValid():
            self.showDashboard()
            return False
        object = item.object
        view = self.views.get(type(object))
        if not view:
            self.showDashboard()
            return False
        view.ensureVisible()
        view.setObject(object)
        self.setCurrentWidget(view)
        if isinstance(object, TaskModel):
            self.bindTask(object, view)
        return True

    def bindTask(self, task: TaskModel, view: TaskView):
        self.binder.unbind_all()

        self.binder.bind(task.properties.can_open, self.actions.open.setEnabled)
        self.binder.bind(task.properties.can_save, self.actions.save.setEnabled)
        self.binder.bind(task.properties.can_start, self.actions.start.setVisible)
        self.binder.bind(task.properties.can_stop, self.actions.stop.setVisible)
        self.binder.bind(task.properties.done, self.actions.clear.setVisible)

        self.binder.bind(task.properties.ready, self.actions.start.setEnabled)
        self.binder.bind(
            task.properties.busy, self.actions.home.setEnabled, lambda busy: not busy
        )
        self.binder.bind(
            task.properties.busy,
            self.actions.open.setEnabled,
            lambda busy: not busy and task.can_open,
        )
        self.binder.bind(task.properties.done, self.actions.save.setEnabled)

        self.binder.bind(self.actions.start.triggered, view.start)
        self.binder.bind(self.actions.stop.triggered, view.stop)
        self.binder.bind(self.actions.open.triggered, view.open)
        self.binder.bind(self.actions.save.triggered, view.save)
        self.binder.bind(self.actions.clear.triggered, view.clear)

    def removeActiveItem(self):
        app.model.items.remove_index(self.activeIndex)

    def showDashboard(self):
        self.setCurrentWidget(self.dashboard)
        self.binder.unbind_all()
        self.actions.stop.setVisible(False)
        self.actions.clear.setVisible(False)
        self.actions.start.setVisible(True)
        self.actions.start.setEnabled(False)
        self.actions.save.setEnabled(False)
        self.actions.open.setEnabled(False)
