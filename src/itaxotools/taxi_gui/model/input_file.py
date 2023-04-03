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

from pathlib import Path

from ..types import InputFile
from .common import Object, Property


class InputFileModel(Object):
    path = Property(Path)
    size = Property(int)

    def __init__(self, path, size):
        super().__init__()
        self.path = path
        self.name = f'{path.parent.name}/{path.name}'
        self.size = size  # bytes

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'


class Fasta(InputFileModel):
    info = Property(InputFile.Fasta, None)

    def __init__(self, info: InputFile.Fasta):
        super().__init__(info.path, info.size)
        self.info = info


class Tabfile(InputFileModel):
    info = Property(InputFile.Tabfile, None)

    def __init__(self, info: InputFile.Tabfile):
        assert len(info.headers) >= 2
        super().__init__(info.path, info.size)
        self.info = info


class Spart(InputFileModel):
    info = Property(InputFile.Spart, None)

    def __init__(self, info: InputFile.Spart):
        super().__init__(info.path, info.size)
        self.info = info
