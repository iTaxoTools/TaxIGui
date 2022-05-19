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

from PySide6 import QtCore
from PySide6 import QtWidgets

from .model import Object, Task, Sequence
from .dashboard import Dashboard


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None
        self.setStyleSheet("""background: red;""")

    def setObject(self, object):
        self.object = object


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: green;""")



class SequenceView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: blue;""")



class Body(QtWidgets.QStackedWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard = Dashboard(self)
        self.addWidget(self.dashboard)
        self.views = dict()

        self.addView(Task, TaskView)
        self.addView(Sequence, SequenceView)

    def addView(self, object_type, view_type):
        view = view_type(self)
        self.views[object_type] = view
        self.addWidget(view)

    def show(self, object: Object):
        view = self.views.get(type(object))
        if not view:
            return False
        view.setObject(object)
        self.setCurrentWidget(view)
        return True

    def showDashboard(self):
        self.setCurrentWidget(self.dashboard)
