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

from PySide6 import QtCore, QtGui, QtWidgets

from itaxotools.common.utility import override

from .. import app
from ..model import DecontaminateModel, DereplicateModel, Task, VersusAllModel


class DashItem(QtWidgets.QAbstractButton):

    def __init__(self, text, slot, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self._mouseOver = False
        self.clicked.connect(slot)

    @override
    def sizeHint(self):
        return QtCore.QSize(200, 80)

    @override
    def event(self, event):
        if isinstance(event, QtGui.QEnterEvent):
            self._mouseOver = True
            self.update()
        elif (
            isinstance(event, QtCore.QEvent) and
            event.type() == QtCore.QEvent.Leave
        ):
            self._mouseOver = False
            self.update()
        return super().event(event)

    @override
    def paintEvent(self, event):
        palette = QtGui.QGuiApplication.palette()
        painter = QtGui.QPainter(self)
        rect = QtCore.QRect(0, 0, self.width(), self.height())

        bg = palette.color(QtGui.QPalette.Midlight)
        if self._mouseOver:
            bg = palette.color(QtGui.QPalette.Light)
        painter.fillRect(rect, bg)

        rect.adjust(4, 0, 0, 0)
        painter.drawText(rect, QtCore.Qt.AlignVCenter, self.text())


class Dashboard(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            Dashboard {
                background: Palette(dark);
            }
            """)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(DashItem('Dereplicate', self.handleDereplicate, self), 0, 0)
        layout.addWidget(DashItem('Decontaminate', self.handleDecontaminate, self), 0, 1)
        layout.addWidget(DashItem('Versus All', self.handleVersusAll, self), 1, 0)
        layout.addWidget(DashItem('Versus Reference', self.handleVersusReference, self), 1, 1)
        layout.setSpacing(4)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(5, 1)
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)

    def handleDereplicate(self):
        app.model.items.add_task(DereplicateModel(), focus=True)

    def handleDecontaminate(self):
        app.model.items.add_task(DecontaminateModel(), focus=True)

    def handleVersusAll(self):
        app.model.items.add_task(VersusAllModel(), focus=True)

    def handleVersusReference(self):
        app.model.items.add_task(Task('VREF'), focus=True)
