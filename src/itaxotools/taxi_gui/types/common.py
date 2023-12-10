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

from enum import Enum
from typing import NamedTuple


class Entry(NamedTuple):
    label: str
    key: str
    default: int


class PropertyEnum(Enum):
    def __init__(self, label, key, default):
        self.label = label
        self.key = key
        self.default = default
        self.type = object

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"


class ColumnFilter(Enum):
    All = ("*", "All contents")
    First = ("1", "First word")

    def __init__(self, abr, text):
        self.abr = abr
        self.text = text
        self.label = f"{text} ({abr})"
