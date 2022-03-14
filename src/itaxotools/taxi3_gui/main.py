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

"""Main dialog window"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from itaxotools import common
import itaxotools.common.widgets
import itaxotools.common.resources # noqa
import itaxotools.common.io # noqa

from .header import Header


class Main(common.widgets.ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)

        self.title = 'Taxi3'

        icon = QtGui.QIcon(common.resources.get(
            'itaxotools.taxi3_gui', 'logos/taxi3.ico'))
        self.setWindowIcon(icon)
        self.setWindowTitle(self.title)
        self.resize(860, 600)

        self.draw()

    def draw(self):
        """Draw all contents"""
        self.header = Header()
        self.sidebar = self.draw_sidebar()
        self.body = self.draw_body()
        self.footer = self.draw_footer()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.header, 0, 0, 1, 2)
        layout.addWidget(self.sidebar, 1, 0, 1, 1)
        layout.addWidget(self.body, 1, 1, 1, 1)
        layout.addWidget(self.footer, 2, 0, 1, 2)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def draw_header(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("background: red;")
        return widget

    def draw_sidebar(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("background: blue;")
        widget.setFixedWidth(256)
        return widget

    def draw_body(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("background: cyan;")
        return widget

    def draw_footer(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("background: magenta;")
        widget.setFixedHeight(24)
        return widget
