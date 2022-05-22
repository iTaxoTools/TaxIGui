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
from .sidebar import Item
from .dashboard import Dashboard


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.updateView()

    def updateView(self):
        pass


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: Palette(Shadow);""")


class SequenceView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: Palette(Dark);""")
        self.draw()

    def draw(self):
        self.draw_main_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.frame)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_main_card(self):
        frame = QtWidgets.QFrame(self)
        frame.setStyleSheet("""background: Palette(Midlight);""")
        label = QtWidgets.QLabel('')
        self.draw_buttons()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label, 1)
        layout.addLayout(self.buttons, 0)
        frame.setLayout(layout)
        self.frame = frame
        self.label = label

    def draw_buttons(self):
        open = QtWidgets.QPushButton('Open')
        inspect = QtWidgets.QPushButton('Inspect')
        remove = QtWidgets.QPushButton('Remove')

        open.clicked.connect(self.handleOpen)
        inspect.clicked.connect(self.handleInspect)
        remove.clicked.connect(self.handleRemove)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(open)
        layout.addWidget(inspect)
        layout.addWidget(remove)
        self.buttons = layout

    def setObject(self, object):
        if self.object:
            self.object.changed.disconnect(self.updateView)
        self.object = object
        self.object.changed.connect(self.updateView)
        self.updateView()

    def updateView(self):
        if not self.object:
            return
        self.label.setText(self.object.name)

    def handleOpen(self):
        print('open', self.object.name)

    def handleInspect(self):
        print('inspect', self.object.name)

    def handleRemove(self):
        print('remove', self.object.name)
        self.parent().removeActiveItem()


class Body(QtWidgets.QStackedWidget):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.activeItem = None
        self.activeIndex = None
        self.views = dict()

        self.dashboard = Dashboard(self.model, self)
        self.addWidget(self.dashboard)

        self.addView(Task, TaskView)
        self.addView(Sequence, SequenceView)

    def addView(self, object_type, view_type):
        view = view_type(self)
        self.views[object_type] = view
        self.addWidget(view)

    def showItem(self, item: Item, index: QtCore.QModelIndex):
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
        view.setObject(object)
        self.setCurrentWidget(view)
        return True

    def removeActiveItem(self):
        self.model.remove_index(self.activeIndex)

    def showDashboard(self):
        self.setCurrentWidget(self.dashboard)
