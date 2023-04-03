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

from __future__ import annotations


from itaxotools.common.utility import AttrDict

from ..types import ColumnFilter, FileFormat
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


class Fasta(PartitionModel):
    subset_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(self, file_item, preference: 'species' | 'genera' = None):
        assert isinstance(file_item.object, InputFileModel.Fasta)
        super().__init__(file_item)
        info = file_item.object.info
        assert info.has_subsets
        if preference == 'genera':
            self.subset_filter = ColumnFilter.First

    def as_dict(self):
        return AttrDict(
            type = FileFormat.Fasta,
            path = self.file_item.object.path,
            subset_filter = self.subset_filter,
        )


class Tabfile(PartitionModel):
    subset_column = Property(int, -1)
    individual_column = Property(int, -1)
    subset_filter = Property(ColumnFilter, ColumnFilter.All)
    individual_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(self, file_item, preference: 'species' | 'genera' = None):
        assert isinstance(file_item.object, InputFileModel.Tabfile)
        super().__init__(file_item)
        info = file_item.object.info

        subset = {
            'species': info.species,
            'genera': info.genera,
            None: info.organism,
        }[preference]
        self.individual_column = self._header_get(info.headers, info.individuals)
        self.subset_column = self._header_get(info.headers, subset)

        if self.subset_column < 0:
            self.subset_column = self._header_get(info.headers, info.organism)
            if self.subset_column >= 0 and preference == 'genera':
                self.subset_filter = ColumnFilter.First

    @staticmethod
    def _header_get(headers: list[str], field: str):
        try:
            return headers.index(field)
        except ValueError:
            return -1

    def as_dict(self):
        return AttrDict(
            type = FileFormat.Tabfile,
            path = self.file_item.object.path,
            subset_column = self.subset_column,
            individual_column = self.individual_column,
            subset_filter = self.subset_filter,
            individual_filter = self.individual_filter,
        )


class Spart(PartitionModel):
    spartition = Property(str, None)
    is_xml = Property(bool, None)

    def __init__(self, file_item, *args, **kwargs):
        assert isinstance(file_item.object, InputFileModel.Spart)
        super().__init__(file_item)
        info = file_item.object.info
        assert len(info.spartitions) > 0
        self.spartition = info.spartitions[0]
        self.is_xml = info.is_xml

    def as_dict(self):
        return AttrDict(
            type = FileFormat.Spart,
            path = self.file_item.object.path,
            spartition = self.spartition,
            is_xml = self.is_xml,
        )
