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


class VerticalRollAnimation(QtCore.QPropertyAnimation):
    def __init__(self, widget: QtWidgets.QWidget):
        super().__init__(widget, b"maximumHeight")
        self._visible_target = widget.isVisible()
        self.finished.connect(self.handleFinished)
        self.valueChanged.connect(self.handleChange)

        self.setStartValue(0)
        self.setEndValue(widget.sizeHint().height())
        self.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self.setDuration(300)

    def setAnimatedVisible(self, visible: bool):
        if visible == self._visible_target:
            self.targetObject().setVisible(visible)
            return
        self._visible_target = visible
        if visible:
            self.setEndValue(self.targetObject().sizeHint().height())
            self.setDirection(QtCore.QAbstractAnimation.Forward)
        else:
            self.setDirection(QtCore.QAbstractAnimation.Backward)
        if self.state() != QtCore.QAbstractAnimation.Running:
            self.start()
        self.targetObject().setVisible(True)

    def animatedShow(self):
        self.setAnimatedVisible(True)

    def animatedHide(self):
        self.setAnimatedVisible(False)

    def handleFinished(self):
        self.targetObject().setVisible(self._visible_target)
        self.targetObject().setMaximumHeight(16777215)

    def handleChange(self):
        self.setEndValue(self.targetObject().sizeHint().height())
