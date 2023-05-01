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

from PySide6 import QtWidgets

from sys import exit
from types import ModuleType

from . import config


class Application(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])

    def exec(self):
        exit(super().exec())

    def set_title(self, title: str):
        config.title = title

    def set_tasks(self, tasks: list[ModuleType]):
        config.tasks = tasks

    def set_config(self, config: ModuleType):
        self.set_title(config.title)
        self.set_tasks(config.tasks)

    def set_skin(self, skin: ModuleType):
        skin.apply(self)