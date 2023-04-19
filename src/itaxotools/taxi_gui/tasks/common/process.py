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
# -------------

from __future__ import annotations

from pathlib import Path

from itaxotools.common.utility import AttrDict

from itaxotools.taxi_gui.types import ColumnFilter, FileFormat


def progress_handler(caption, index, total):
    import itaxotools
    itaxotools.progress_handler(
        text=caption,
        value=index,
        maximum=total,
    )


def get_file_info(path: Path):

    from itaxotools.taxi2.files import FileFormat, FileInfo

    from itaxotools.taxi_gui.types import InputFile

    def get_index(items, item):
        return items.index(item) if item else None

    info = FileInfo.from_path(path)
    if info.format == FileFormat.Tabfile:
        return InputFile.Tabfile(
            path = path,
            size = info.size,
            headers = info.headers,
            individuals = info.header_individuals,
            sequences = info.header_sequences,
            organism = info.header_organism,
            species = info.header_species,
            genera = info.header_genus,
        )
    if info.format == FileFormat.Fasta:
        return InputFile.Fasta(
            path = path,
            size = info.size,
            has_subsets = info.has_subsets,
        )
    if info.format == FileFormat.Spart:
        return InputFile.Spart(
            path = path,
            size = info.size,
            spartitions = info.spartitions,
            is_matricial = info.is_matricial,
            is_xml = info.is_xml,
        )
    return InputFile.Unknown(path)


def sequences_from_model(input: AttrDict):
    from itaxotools.taxi2.sequences import SequenceHandler, Sequences

    if input.type == FileFormat.Tabfile:
        return Sequences.fromPath(
            input.path,
            SequenceHandler.Tabfile,
            hasHeader = True,
            idColumn=input.index_column,
            seqColumn=input.sequence_column,
        )
    elif input.type == FileFormat.Fasta:
        return Sequences.fromPath(
            input.path,
            SequenceHandler.Fasta,
            parse_organism=True,
        )
    raise Exception(f'Cannot create sequences from input: {input}')


def partition_from_model(input: AttrDict):
    from itaxotools.taxi2.partitions import Partition, PartitionHandler

    if input.type == FileFormat.Tabfile:
        filter = {
            ColumnFilter.All: None,
            ColumnFilter.First: PartitionHandler.subset_first_word,
        }[input.subset_filter]
        return Partition.fromPath(
            input.path,
            PartitionHandler.Tabfile,
            hasHeader = True,
            idColumn=input.individual_column,
            subColumn=input.subset_column,
            filter=filter,
        )
    elif input.type == FileFormat.Fasta:
        filter = {
            ColumnFilter.All: None,
            ColumnFilter.First: PartitionHandler.subset_first_word,
        }[input.subset_filter]
        return Partition.fromPath(
            input.path,
            PartitionHandler.Fasta,
            filter=filter,
        )
    elif input.type == FileFormat.Spart:
        return Partition.fromPath(
            input.path,
            PartitionHandler.Spart,
            spartition=input.spartition,
        )
    raise Exception(f'Cannot create partition from input: {input}')
