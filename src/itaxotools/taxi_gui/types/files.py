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

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

from itaxotools.common.types import Type


class FileFormat(Enum):
    Tabfile = auto()
    Fasta = auto()
    Spart = auto()


@dataclass
class InputFile(Type):
    path: Path
    size: int


@dataclass
class Unknown(InputFile):
    pass


@dataclass
class Fasta(InputFile):
    has_subsets: bool


@dataclass
class Tabfile(InputFile):
    headers: list[str]
    individuals: str = None
    sequences: str = None
    organism: str = None
    species: str = None
    genera: str = None


@dataclass
class Spart(InputFile):
    spartitions: list[str]
    is_matricial: bool
    is_xml: bool


class Entry(NamedTuple):
    label: str
    key: str
    default: int
