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

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from ..types import ComparisonMode


@dataclass
class VersusAllResults:
    pass


def progress_handler(progress):
    import itaxotools
    itaxotools.progress_handler(
        text=progress.operation,
        value=progress.current_step,
        maximum=progress.total_steps,
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
            headers = info.headers,
            individuals = get_index(info.headers, info.header_individuals),
            sequences = get_index(info.headers, info.header_sequences),
            organism = get_index(info.headers, info.header_organism),
            species = get_index(info.headers, info.header_species),
            genera = get_index(info.headers, info.header_genus),
        )
    return InputFile.Unknown(path)


def versus_all(
    work_dir: Path,
    input: Path,
    comparison_mode: ComparisonMode,
) -> Dict[Path, Tuple[Path, Path]]:

    from itaxotools.taxi3.library.config import AlignmentScores, Config
    from itaxotools.taxi3.library.datatypes import (
        Metric, SequenceData, SpeciesPartition, SubspeciesPartition,
        TabfileReader, ValidFilePath, VoucherPartition)
    from itaxotools.taxi3.library.task import (
        Alignment, CalculateDistances, VersusAll)

    from itaxotools import progress_handler

    alignment = {
        ComparisonMode.AlignmentFree: Alignment.AlignmentFree,
        ComparisonMode.PairwiseAlignment: Alignment.Pairwise,
        ComparisonMode.AlreadyAligned: Alignment.AlreadyAligned,
    }[comparison_mode.type]

    config = None
    if comparison_mode.type is ComparisonMode.PairwiseAlignment:
        scores = AlignmentScores._from_scores_dict(comparison_mode.config)
        config = Config(scores)

    metrics = [Metric.Uncorrected]

    progress_handler('Calculating distances...')
    task = CalculateDistances(warn=print)
    task.sequences = SequenceData.from_path(ValidFilePath(input), TabfileReader)
    task.alignment = alignment
    task.metrics = metrics
    task.config = config
    task.start()

    distances = task.result

    progress_handler('Running Versus All analysis...')
    task = VersusAll(warn=print)

    data = TabfileReader.read_data(ValidFilePath(input))
    for table in data:
        if isinstance(table, SequenceData):
            task.sequences = table
        elif isinstance(table, VoucherPartition):
            task.vouchers = table
        elif isinstance(table, SpeciesPartition):
            task.species = table
        elif isinstance(table, SubspeciesPartition):
            task.subspecies = table

    task.distances = distances
    task.alignment = alignment
    task.metrics = metrics
    task.config = config
    task.start()

    progress_handler('Printing results...')
    tables = task.result
    for table in (
        [
            tables.sequence_summary_statistic.total,
            tables.sequence_summary_statistic.by_species,
        ]
        + tables.distances
        + tables.mean_min_max_distances
        + [tables.summary_statistics]
    ):
        if table:
            print(table.get_dataframe().to_string())

    return 42
