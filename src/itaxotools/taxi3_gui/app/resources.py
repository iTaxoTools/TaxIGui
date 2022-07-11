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
from PySide6 import QtGui

from itaxotools.common import resources
from itaxotools.common.widgets import VectorPixmap, VectorIcon

from . import skin


class ResourceLoader:
    def __init__(self, **kwargs):
        self.attrs = kwargs

    def __dir__(self):
        return super().__dir__() + self.attrs

    def __getattr__(self, attr):
        if attr in self.attrs:
            return self.attrs[attr]()


def _get_common(path):
    return resources.get_common(path)


def _get_local(path):
    root = '.'.join(__package__.split('.')[:-1])
    return resources.get_local(root, path)


pixmaps = ResourceLoader(
    logo_project = lambda: QtGui.QPixmap(
        _get_common('logos/itaxotools-logo-64px.png')),
    logo_tool = lambda: VectorPixmap(
        _get_local('logos/taxi3.svg'),
        size=QtCore.QSize(132, 44),
        colormap=skin.colormap_icon)
)

icons = ResourceLoader(
    arrow = lambda: VectorIcon(
        _get_common('icons/svg/arrow-right.svg'), skin.colormap),
    open = lambda: VectorIcon(
        _get_common('icons/svg/open.svg'), skin.colormap),
    save = lambda: VectorIcon(
        _get_common('icons/svg/save.svg'), skin.colormap),
    home = lambda: VectorIcon(
        _get_local('icons/home.svg'), skin.colormap),
    app = lambda: QtGui.QIcon(
        _get_local('logos/taxi3.ico')),
)
