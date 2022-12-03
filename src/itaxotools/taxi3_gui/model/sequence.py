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

from ..types import Type, SequenceReader, SequenceFile
from .common import Object, Property


class SequenceModel(Object):
    path = Property(Path)
    reader = Property(SequenceReader)

    def __init__(self, path, reader=SequenceReader.TabfileReader):
        super().__init__()
        self.path = path
        self.name = path.name
        self.reader = reader

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'


class Tabfile(SequenceModel):
    index_column = Property(str)
    sequence_column = Property(str)

    def __init__(self, info):
        assert info.type == SequenceFile.Tabfile
        assert len(info.headers) >= 2
        super().__init__(info.path, SequenceReader.TabfileReader)
        self.headers = info.headers
        self.index_column = self.headers[0]
        self.sequence_column = self.headers[1]
