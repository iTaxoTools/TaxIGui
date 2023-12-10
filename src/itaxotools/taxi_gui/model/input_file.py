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
from typing import Generic, TypeVar

from ..types import FileInfo
from .common import Object, Property

FileInfoType = TypeVar("FileInfoType", bound=FileInfo)


class InputFileModel(Object, Generic[FileInfoType]):
    info = Property(FileInfo, None)
    path = Property(Path)
    size = Property(int)

    def __init__(self, info: FileInfoType):
        super().__init__()
        self.info = info
        self.path = info.path
        self.name = f"{info.path.parent.name}/{info.path.name}"
        self.size = info.size  # bytes

    def __repr__(self):
        return f'{".".join(self._get_name_chain())}({repr(self.name)})'
