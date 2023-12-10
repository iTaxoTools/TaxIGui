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

from ..types import ColumnFilter, FileInfo
from .common import Object, Property

FileInfoType = TypeVar("FileInfoType", bound=FileInfo)

models = DecoratorDict[FileInfo, Object]()


class PartitionModel(Object, Generic[FileInfoType]):
    info = Property(FileInfo, None)
    updated = QtCore.Signal()

    def __init__(
        self,
        info: FileInfo,
        preference: Literal["species", "genera"] = None,
    ):
        super().__init__()
        self.info = info
        self.name = f"Partition from {info.path.name}"

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'

    def is_valid(self):
        return True

    def as_dict(self):
        return AttrDict(
            {p.key: p.value for p in self.properties}
            | dict(partition_name=self.partition_name)
        )

    @classmethod
    def from_file_info(
        cls,
        info: FileInfoType,
        preference: Literal["species", "genera"] = None,
    ) -> PartitionModel[FileInfoType]:
        if type(info) not in models:
            raise Exception(f"No suitable {cls.__name__} for info: {info}")
        return models[type(info)](info, preference)

    @property
    def partition_name(self):
        return "unknown"


@models(FileInfo.Fasta)
class Fasta(PartitionModel):
    subset_filter = Property(ColumnFilter, ColumnFilter.All)
    subset_separator = Property(str, "|")

    def __init__(
        self,
        info: FileInfo.Fasta,
        preference: Literal["species", "genera"] = None,
    ):
        super().__init__(info)
        assert info.has_subsets
        self.subset_separator = info.subset_separator
        if preference == "genera":
            self.subset_filter = ColumnFilter.First

    @property
    def partition_name(self):
        return "from fasta"


@models(FileInfo.Tabfile)
class Tabfile(PartitionModel):
    subset_column = Property(int, -1)
    individual_column = Property(int, -1)
    subset_filter = Property(ColumnFilter, ColumnFilter.All)
    individual_filter = Property(ColumnFilter, ColumnFilter.All)

    def __init__(
        self,
        info: FileInfo.Tabfile,
        preference: Literal["species", "genera"] = None,
    ):
        super().__init__(info)

        subset = {
            "species": info.header_species,
            "genera": info.header_genus,
            None: info.header_organism,
        }[preference]
        self.individual_column = self._header_get(info.headers, info.header_individuals)
        self.subset_column = self._header_get(info.headers, subset)

        if self.subset_column < 0:
            self.subset_column = self._header_get(info.headers, info.header_organism)
            if self.subset_column >= 0 and preference == "genera":
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

    def is_valid(self):
        if self.subset_column < 0:
            return False
        if self.individual_column < 0:
            return False
        if self.subset_column == self.individual_column:
            if self.subset_filter == self.individual_filter:
                return False
        return True

    @property
    def partition_name(self):
        return self.info.headers[self.subset_column]


@models(FileInfo.Spart)
class Spart(PartitionModel):
    spartition = Property(str, None)
    is_xml = Property(bool, None)

    def __init__(
        self,
        info: FileInfo.Spart,
        preference: Literal["species", "genera"] = None,
    ):
        super().__init__(info)
        assert len(info.spartitions) > 0
        self.spartition = info.spartitions[0]
        self.is_xml = info.is_xml

    @property
    def partition_name(self):
        return self.spartition
