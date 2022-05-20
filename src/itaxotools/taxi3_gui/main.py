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

from PySide6 import QtWidgets
from PySide6 import QtGui

from pathlib import Path

from itaxotools import common
import itaxotools.common.widgets
import itaxotools.common.resources # noqa
import itaxotools.common.utility # noqa
import itaxotools.common.io # noqa

from .header import Header
from .body import Body
from .footer import Footer
from .sidebar import SideBar
from .model import Task, Sequence, ItemModel


def get_icon(path):
    return common.resources.get_common(Path('icons/svg') / path)


def get_local_icon(path):
    return common.resources.get_local(__package__, Path('icons') / path)


class Main(common.widgets.ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)

        self.title = 'Taxi3'

        icon = QtGui.QIcon(common.resources.get(
            'itaxotools.taxi3_gui', 'logos/taxi3.ico'))
        self.setWindowIcon(icon)
        self.setWindowTitle(self.title)
        self.resize(800, 500)

        self.skin()
        self.draw()
        self.act()

    def skin(self):
        """Configure widget appearance"""
        color = {
            'white':  '#ffffff',
            'light':  '#eff1ee',
            'beige':  '#e1e0de',
            'gray':   '#abaaa8',
            'iron':   '#8b8d8a',
            'black':  '#454241',
            'red':    '#ee4e5f',
            'pink':   '#eb9597',
            'orange': '#eb6a4a',
            'brown':  '#655c5d',
            'green':  '#00ff00',
            }
        # using green for debugging
        palette = QtGui.QGuiApplication.palette()
        scheme = {
            QtGui.QPalette.Active: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'black',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'brown',
                QtGui.QPalette.Text: 'black',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'black',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'red',
                QtGui.QPalette.HighlightedText: 'white',
                # These work on linux only?
                QtGui.QPalette.ToolTipBase: 'beige',
                QtGui.QPalette.ToolTipText: 'brown',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.Link: 'red',
                QtGui.QPalette.LinkVisited: 'pink',
                },
            QtGui.QPalette.Disabled: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'iron',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'green',
                QtGui.QPalette.Text: 'iron',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'gray',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'pink',
                QtGui.QPalette.HighlightedText: 'white',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.ToolTipBase: 'green',
                QtGui.QPalette.ToolTipText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            }
        scheme[QtGui.QPalette.Inactive] = scheme[QtGui.QPalette.Active]
        for group in scheme:
            for role in scheme[group]:
                palette.setColor(
                    group, role, QtGui.QColor(color[scheme[group][role]]))
        QtGui.QGuiApplication.setPalette(palette)

        self.colormap = {
            common.widgets.VectorIcon.Normal: {
                '#000': color['brown'],
                '#f00': color['red'],
                },
            common.widgets.VectorIcon.Disabled: {
                '#000': color['gray'],
                '#f00': color['orange'],
                },
            }
        self.colormap_icon = {
            '#000': color['black'],
            '#f00': color['red'],
            '#f88': color['pink'],
            }
        self.colormap_icon_light = {
            '#000': color['iron'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }

    def draw(self):
        """Draw all contents"""
        self._test_sequence = Sequence('Unchanged')
        self.model = ItemModel()
        self.model.add_task(Task('DEREP #1'))
        self.model.add_task(Task('DECONT #1'))
        self.model.add_task(Task('DECONT #2'))
        self.model.add_sequence(Sequence('Frog Samples'))
        self.model.add_sequence(Sequence('Finch Samples'))
        self.model.add_sequence(self._test_sequence)

        self.widgets = common.utility.AttrDict()
        self.widgets.header = Header(self)
        self.widgets.sidebar = SideBar(self.model, self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

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

    def act(self):
        """Populate dialog actions"""
        self.actions = {}

        self.actions['home'] = QtGui.QAction('&Home', self)
        self.actions['home'].setIcon(common.widgets.VectorIcon(get_local_icon('home.svg'), self.colormap))
        self.actions['home'].setStatusTip('Open the dashboard')
        self.actions['home'].triggered.connect(self.handleHome)

        self.actions['open'] = QtGui.QAction('&Open', self)
        self.actions['open'].setIcon(common.widgets.VectorIcon(get_icon('open.svg'), self.colormap))
        self.actions['open'].setShortcut(QtGui.QKeySequence.Open)
        self.actions['open'].setStatusTip('Open an existing file')
        self.actions['open'].triggered.connect(self.handleOpen)

        self.actions['save'] = QtGui.QAction('&Save', self)
        self.actions['save'].setIcon(common.widgets.VectorIcon(get_icon('save.svg'), self.colormap))
        self.actions['save'].setShortcut(QtGui.QKeySequence.Save)
        self.actions['save'].setStatusTip('Save results')
        self.actions['save'].triggered.connect(self.handleSave)

        self.widgets.header.toolBar.addAction(self.actions['home'])
        self.widgets.header.toolBar.addAction(self.actions['open'])
        self.widgets.header.toolBar.addAction(self.actions['save'])

    def handleHome(self):
        self.widgets.body.showDashboard()

    def handleOpen(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, self.title)
        for filename in filenames:
            path = Path(filename)
            self.model.add_sequence(Sequence(path.stem))

    def handleSave(self):
        self._test_sequence.name = 'Modified'
        pass
