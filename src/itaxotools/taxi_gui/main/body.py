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
from ..model.common import Item
from ..model.tasks import TaskModel
from ..view.tasks import TaskView
from .dashboard import Dashboard


class ScrollArea(QtWidgets.QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)


class Body(QtWidgets.QStackedWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.actions = parent.actions
        self.activeItem = None
        self.activeIndex = None
        self.binder = Binder()
        self.areas = dict()

        self.dashboard = Dashboard(self)
        self.addWidget(self.dashboard)

        self.showDashboard()

    def addView(self, object_type, view_type, *args, **kwargs):
        area = ScrollArea(self)
        view = view_type(parent=area, *args, **kwargs)
        area.setWidget(view)
        self.areas[object_type] = area
        self.addWidget(area)

    def showItem(self, item: Item, index: QtCore.QModelIndex):
        self.activeItem = item
        self.activeIndex = index
        if not item or not index.isValid():
            self.showDashboard()
            return False
        object = item.object
        area = self.areas.get(type(object))
        if not area:
            self.showDashboard()
            return False
        view = area.widget()
        view.setObject(object)
        self.setCurrentWidget(area)
        area.ensureVisible(0, 0)
        if isinstance(object, TaskModel):
            self.bindTask(object, view)
        return True

    def bindTask(self, task: TaskModel, view: TaskView):
        self.binder.unbind_all()
        self.actions.open.setEnabled(False)

        self.binder.bind(task.properties.ready, self.actions.start.setEnabled)
        self.binder.bind(task.properties.editable, self.actions.start.setVisible)
        self.binder.bind(task.properties.busy, self.actions.stop.setVisible)
        self.binder.bind(task.properties.busy, self.actions.home.setEnabled, lambda busy: not busy)
        self.binder.bind(task.properties.done, self.actions.save.setEnabled)
        self.binder.bind(task.properties.done, self.actions.clear.setVisible)

        self.binder.bind(self.actions.start.triggered, view.start)
        self.binder.bind(self.actions.stop.triggered, view.stop)
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
        self.actions.open.setEnabled(True)
