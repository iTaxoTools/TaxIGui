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

from pathlib import Path

from ..types import Type, SequenceReader, ColumnFilter
from .common import Object, Property


class InputFileModel(Object):
    path = Property(Path)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.name = path.name

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'


class Tabfile(InputFileModel):
    size = Property(int, 0)
    headers = Property(list)
    smart_columns = Property(dict)

    def __init__(self, path: Path, headers: list[str], size=0, **smart_columns):
        assert len(headers) >= 2
        super().__init__(path)
        self.size = size
        self.headers = headers
        self.smart_columns = smart_columns
