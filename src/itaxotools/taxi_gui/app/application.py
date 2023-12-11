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

from PySide6 import QtGui, QtWidgets

from sys import exit
from types import ModuleType
from typing import Literal

from . import config
from .resources import LazyResource


class Application(QtWidgets.QApplication):
    def __init__(self, argv=None):
        super().__init__(argv or [])

    def exec(self):
        exit(super().exec())

    def set_title(self, title: str):
        config.title = title

    def set_icon(self, icon: LazyResource[QtGui.QIcon]):
        config.icon = icon

    def set_pixmap(self, pixmap: LazyResource[QtGui.QPixmap]):
        config.pixmap = pixmap

    def set_dashboard(self, dashboard: Literal["legacy", "constrained"]):
        config.dashboard = dashboard

    def set_show_open(self, open: bool):
        config.show_open = open

    def set_show_save(self, save: bool):
        config.show_save = save

    def set_tasks(self, tasks: list[ModuleType]):
        config.tasks = tasks

    def set_config(self, config: ModuleType):
        self.set_title(getattr(config, "title", "Application"))
        self.set_icon(getattr(config, "icon", LazyResource(None)))
        self.set_pixmap(getattr(config, "pixmap", LazyResource(None)))
        self.set_dashboard(getattr(config, "dashboard", "legacy"))
        self.set_show_open(getattr(config, "show_open", False))
        self.set_show_save(getattr(config, "show_save", False))
        self.set_tasks(getattr(config, "tasks", []))

    def set_skin(self, skin: ModuleType):
        skin.apply(self)
