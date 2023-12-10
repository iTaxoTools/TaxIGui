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

from __future__ import annotations

from PySide6 import QtGui

from typing import Callable, Generic, TypeVar

from itaxotools.common import resources
from itaxotools.common.widgets import VectorIcon

from . import skin

ResourceType = TypeVar("ResourceType")


class LazyResource(Generic[ResourceType]):
    def __init__(self, loader: Callable[[], ResourceType] = None):
        self._loader = loader

    @property
    def resource(self) -> ResourceType | None:
        if self._loader is None:
            return None
        return self._loader()


class LazyResourceCollection(Generic[ResourceType]):
    def __init__(self, **kwargs: dict[str, Callable[[], ResourceType]]):
        super().__setattr__("attrs", kwargs)

    def __dir__(self):
        return super().__dir__() + self.attrs

    def __getattr__(self, attr) -> LazyResource[ResourceType]:
        if attr in self.attrs:
            return LazyResource(self.attrs[attr])

    def __setattr__(self, attr, value: Callable[[], ResourceType]):
        self.attrs[attr] = value


def _get_common(path):
    return resources.get_common(path)


pixmaps = LazyResourceCollection(
    logo_project=lambda: QtGui.QPixmap(_get_common("logos/itaxotools-logo-64px.png")),
)


icons = LazyResourceCollection(
    arrow=lambda: VectorIcon(_get_common("icons/svg/arrow-right.svg"), skin.colormap),
    open=lambda: VectorIcon(_get_common("icons/svg/open.svg"), skin.colormap),
    save=lambda: VectorIcon(_get_common("icons/svg/save.svg"), skin.colormap),
    run=lambda: VectorIcon(_get_common("icons/svg/run.svg"), skin.colormap),
    stop=lambda: VectorIcon(_get_common("icons/svg/stop.svg"), skin.colormap),
    clear=lambda: VectorIcon(_get_common("icons/svg/clear.svg"), skin.colormap),
    home=lambda: VectorIcon(_get_common("icons/svg/home.svg"), skin.colormap),
)
