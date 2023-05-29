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

from PySide6 import QtCore

from typing import Generic, Literal, TypeVar

from itaxotools.common.utility import AttrDict, DecoratorDict

from ..types import ColumnFilter, FileFormat, FileInfo
from .common import Object, Property, TreeItem
from .input_file import InputFileModel

FileInfoType = TypeVar('FileInfoType', bound=FileInfo)

models = DecoratorDict[FileInfo, Object]()


class PartitionModel(Object, Generic[FileInfoType]):
    file_item = Property(TreeItem, None)
    updated = QtCore.Signal()

    def __init__(self, file_item: TreeItem[InputFileModel[FileInfoType]]):
        super().__init__()
        self.file_item = file_item
        self.name = f'Partition from {file_item.object.path.name}'

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'

    def is_valid(self):
        return True

    def as_dict(self):
        return AttrDict(
            path = self.file_item.object.path,
        )

    @classmethod
    def from_input_file(
        cls,
        file_item: TreeItem[InputFileModel[FileInfoType]],
        preference: Literal['species', 'genera'] = None,
    ) -> PartitionModel[FileInfoType]:

        info = file_item.object.info
        if not type(info) in models:
            raise Exception(f'No suitable {cls.__name__} for info: {info}')
        return models[type(info)](file_item, preference)


@models(FileInfo.Fasta)
class Fasta(PartitionModel[FileInfo.Fasta]):
    subset_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(
        self,
        file_item: TreeItem[InputFileModel[FileInfo.Fasta]],
        preference: Literal['species', 'genera'] = None
    ):
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


@models(FileInfo.Tabfile)
class Tabfile(PartitionModel[FileInfo.Tabfile]):
    subset_column = Property(int, -1)
    individual_column = Property(int, -1)
    subset_filter = Property(ColumnFilter, ColumnFilter.All)
    individual_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(
        self,
        file_item: TreeItem[InputFileModel[FileInfo.Tabfile]],
        preference: Literal['species', 'genera'] = None
    ):
        super().__init__(file_item)
        info = file_item.object.info

        subset = {
            'species': info.header_species,
            'genera': info.header_genus,
            None: info.header_organism,
        }[preference]
        self.individual_column = self._header_get(info.headers, info.header_individuals)
        self.subset_column = self._header_get(info.headers, subset)

        if self.subset_column < 0:
            self.subset_column = self._header_get(info.headers, info.header_organism)
            if self.subset_column >= 0 and preference == 'genera':
                self.subset_filter = ColumnFilter.First

        self.properties.subset_column.notify.connect(self.updated)
        self.properties.individual_column.notify.connect(self.updated)
        self.properties.subset_filter.notify.connect(self.updated)
        self.properties.individual_filter.notify.connect(self.updated)

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

    def is_valid(self):
        if self.subset_column < 0:
            return False
        if self.individual_column < 0:
            return False
        if self.subset_column == self.individual_column:
            if self.subset_filter == self.individual_filter:
                return False
        return True


@models(FileInfo.Spart)
class Spart(PartitionModel[FileInfo.Spart]):
    spartition = Property(str, None)
    is_xml = Property(bool, None)

    def __init__(
        self,
        file_item: TreeItem[InputFileModel[FileInfo.Spart]],
        *args, **kwargs
    ):
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
