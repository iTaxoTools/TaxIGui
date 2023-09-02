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

from typing import Generic, TypeVar

from itaxotools.common.utility import AttrDict, DecoratorDict

from ..types import ColumnFilter, FileFormat, FileInfo
from .common import Object, Property, TreeItem
from .input_file import InputFileModel

FileInfoType = TypeVar('FileInfoType', bound=FileInfo)

models = DecoratorDict[FileInfo, Object]()


class TreeModel(Object, Generic[FileInfoType]):
    info = Property(FileInfo, None)

    def __init__(self, info: FileInfo):
        super().__init__()
        self.info = info
        self.name = f'Tree from {info.path.name}'

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'

    def is_valid(self):
        return True

    def as_dict(self):
        return AttrDict({p.key: p.value for p in self.properties})

    @classmethod
    def from_file_info(cls, info: FileInfoType) -> TreeModel[FileInfoType]:
        if not type(info) in models:
            raise Exception(f'No suitable {cls.__name__} for info: {info}')
        return models[type(info)](info)


@models(FileInfo.Newick)
class Fasta(TreeModel):
    index = Property(int, 0)
    count = Property(int, 0)
    names = Property(set, None)

    def __init__(self, info: FileInfo.Newick):
        super().__init__(info)
        self.count = info.count
        self.names = info.names