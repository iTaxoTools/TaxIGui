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

from itaxotools.common.widgets import ScalingImage, VLineSeparator

from .. import app


class ToolLogo(QtWidgets.QLabel):
    def __init__(self, pixmap, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setFixedWidth(210)
        self.setFixedWidth(160)
        self.setAlignment(QtCore.Qt.AlignCenter)
        if pixmap is not None:
            self.setPixmap(pixmap)


class ProjectLogo(ScalingImage):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setFixedHeight(64)
        self.logo = app.resources.pixmaps.logo_project.resource


class ToolBar(QtWidgets.QToolBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setStyleSheet(
            """
            QToolBar {
                spacing: 2px;
                }
            QToolButton {
                color: palette(Shadow);
                background: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                letter-spacing: 1px;
                font-weight: bold;
                font-size: 14px;
                min-width: 74px;
                min-height: 38px;
                padding: 0px 8px 0px 8px;
                margin: 0px 0px 0px 0px;
                text-align: right;
                }
            QToolButton:hover {
                background: palette(Window);
                border: 1px solid transparent;
                }
            QToolButton:disabled {
                color: palette(Mid);
                }
            QToolButton:pressed {
                background: palette(Midlight);
                border: 1px solid palette(Mid);
                border-radius: 2px;
                }
            QToolButton[popupMode="2"]:pressed {
                padding: 0px 8px 1px 8px;
                margin: 0px 0px -1px 0px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
                }
            QToolButton::menu-indicator {
                image: none;
                width: 30px;
                border-bottom: 1px solid palette(Mid);
                subcontrol-origin: padding;
                subcontrol-position: bottom;
                }
            QToolButton::menu-indicator:disabled {
                border-bottom: 1px solid palette(Midlight);
                }
            QToolButton::menu-indicator:pressed {
                border-bottom: 0px;
                }
            """
        )


class Header(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.setStyleSheet(
            """
            Header {
                background: palette(Light);
                border-top: 1px solid palette(Mid);
                border-bottom: 1px solid palette(Dark);
                }
            """
        )
        self.toolLogo = ToolLogo(app.config.pixmap.resource, self)
        self.projectLogo = ProjectLogo(self)
        self.toolBar = ToolBar(self)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.toolLogo)
        layout.addWidget(VLineSeparator(1))
        layout.addSpacing(4)
        layout.addWidget(self.toolBar)
        layout.addSpacing(8)
        layout.addStretch(8)
        layout.addWidget(self.projectLogo)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
