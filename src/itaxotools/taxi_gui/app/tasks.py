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

from PySide6 import QtGui

from importlib import import_module
from typing import NamedTuple

from itaxotools.taxi_gui.app.resources import LazyResource
from itaxotools.taxi_gui.model.tasks import TaskModel
from itaxotools.taxi_gui.view.tasks import TaskView


class Task(NamedTuple):
    title: str
    description: str
    pixmap: LazyResource[QtGui.QPixmap]
    model: TaskModel
    view: TaskView

    @classmethod
    def from_module(cls, module):
        import_module(".model", module.__package__)
        import_module(".view", module.__package__)
        return cls(
            title=getattr(module, "title", "Task"),
            description=getattr(module, "description", "Description"),
            pixmap=getattr(module, "pixmap", LazyResource(None)),
            model=module.model.Model,
            view=module.view.View,
        )
