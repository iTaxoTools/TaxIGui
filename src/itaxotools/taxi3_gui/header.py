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
from PySide6 import QtGui

from itaxotools.common import resources
from itaxotools.common.widgets import ScalingImage, VectorPixmap, VLineSeparator


class ToolLogo(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(256)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setPixmap(VectorPixmap(
            resources.get(
                __package__, 'logos/taxi3.svg'),
            size=QtCore.QSize(44, 44)))


class ProjectLogo(ScalingImage):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)
        self.logo = QtGui.QPixmap(
            resources.get('logos/itaxotools-logo-64px.png'))


class ToolBar(QtWidgets.QToolBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)


class Header(QtWidgets.QFrame):

    def __init__(self):
        super().__init__()
        self.draw()

    def draw(self):
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Maximum)
        self.setStyleSheet("""
            Header {
                background: palette(Light);
                border-top: 1px solid palette(Mid);
                border-bottom: 1px solid palette(Dark);
                }
            """)
        self.toolLogo = ToolLogo()
        self.projectLogo = ProjectLogo()
        self.toolBar = ToolBar()

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.toolLogo)
        layout.addSpacing(8)
        layout.addWidget(self.toolBar)
        layout.addSpacing(8)
        layout.addStretch(8)
        layout.addWidget(self.projectLogo)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
