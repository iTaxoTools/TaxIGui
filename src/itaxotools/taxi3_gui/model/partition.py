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

from ..types import ColumnFilter
from .common import Object, Property, Item
from .input_file import InputFileModel


class PartitionModel(Object):
    file_item = Property(Item, None)

    def __init__(self, file_item=None):
        super().__init__()
        self.file_item = file_item
        if file_item:
            self.name = f'Partition from {file_item.object.path.name}'

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'


class Tabfile(PartitionModel):
    subset_column = Property(str, '')
    individual_column = Property(str, '')
    subset_filter = Property(ColumnFilter, ColumnFilter.All)
    individual_filter = Property(ColumnFilter, ColumnFilter.All)

    @staticmethod
    def _find_first(dictionary, items, default):
        for item in items:
            if dictionary.get(item) is not None:
                return dictionary[item]
        return default

    def __init__(self, file_item, subset: str):
        assert isinstance(file_item.object, InputFileModel.Tabfile)
        super().__init__(file_item)
        headers = file_item.object.headers
        smart_columns = file_item.object.smart_columns

        subset_index = self._find_first(smart_columns, [subset, 'organism'], 0) or 0
        individuals_index = smart_columns.get('individuals', 0)
        self.subset_column = headers[subset_index]
        self.individual_column = headers[individuals_index]

        if subset == 'genera' and subset_index == smart_columns.get('organism', -1):
            self.subset_filter = ColumnFilter.First
