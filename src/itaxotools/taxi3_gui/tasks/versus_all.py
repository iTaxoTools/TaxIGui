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

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from ..types import ComparisonMode


@dataclass
class VersusAllResults:
    pass


def progress_handler(caption, index, total):
    import itaxotools
    itaxotools.progress_handler(
        text=caption,
        value=index,
        maximum=total,
    )


def initialize():
    import itaxotools
    itaxotools.progress_handler('Initializing...')

    from itaxotools.taxi3.library import config  # noqa
    from itaxotools.taxi3.library import datatypes  # noqa
    from itaxotools.taxi3.library import task  # noqa


def get_file_info(path: Path):

    from itaxotools.taxi3.files import FileInfo, FileFormat
    from ..types import InputFile

    def get_index(items, item):
        return items.index(item) if item else None

    info = FileInfo.from_path(path)
    if info.format == FileFormat.Tabfile:
        return InputFile.Tabfile(
            path = path,
            size = info.size,
            headers = info.headers,
            individuals = get_index(info.headers, info.header_individuals),
            sequences = get_index(info.headers, info.header_sequences),
            organism = get_index(info.headers, info.header_organism),
            species = get_index(info.headers, info.header_species),
            genera = get_index(info.headers, info.header_genus),
        )
    return InputFile.Unknown(path)


def versus_all(work_dir, input_sequences, **kwargs) -> tuple[float, Path]:
    from itaxotools.taxi3.tasks.versus_all import VersusAll

    task = VersusAll()
    task.progress_handler = progress_handler
    task.set_input_sequences_from_path(input_sequences)
    task.set_input_species_from_path(input_sequences)
    task.set_input_genera_from_path(input_sequences)
    task.work_dir = work_dir
    results = task.start()

    return results
