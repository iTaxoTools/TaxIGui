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

from importlib import import_module
from typing import NamedTuple


class Task(NamedTuple):
    title: str
    description: str
    model: object
    view: object

    @classmethod
    def from_module(cls, module):
        import_module('.model', module.__package__)
        import_module('.view', module.__package__)
        return cls(
            title = module.title,
            description = module.description,
            model = module.model.Model,
            view = module.view.View,
        )
