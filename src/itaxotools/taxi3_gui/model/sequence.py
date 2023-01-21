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
from .common import Object, Property, Item
from .input_file import InputFileModel


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


class SequenceModel2(Object):
    file_item = Property(Item, None)

    def __init__(self, file_item=None):
        super().__init__()
        self.file_item = file_item
        if file_item:
            self.name = f'Sequences from {file_item.object.path.name}'

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'


class Tabfile(SequenceModel2):
    index_column = Property(int, -1)
    sequence_column = Property(int, -1)
    index_filter = Property(ColumnFilter, ColumnFilter.All)
    sequence_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(self, file_item):
        assert isinstance(file_item.object, InputFileModel.Tabfile)
        super().__init__(file_item)
        info = file_item.object.info
        self.index_column = self._header_get(info.headers, info.individuals)
        self.sequence_column = self._header_get(info.headers, info.sequences)

    @staticmethod
    def _header_get(headers: list[str], field: str):
        try:
            return headers.index(field)
        except ValueError:
            return -1
