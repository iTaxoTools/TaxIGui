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

from itaxotools.common.utility import AttrDict

from ..types import ComparisonMode, ColumnFilter, AlignmentMode, DistanceMetric, FileFormat


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
            individuals = info.header_individuals,
            sequences = info.header_sequences,
            organism = info.header_organism,
            species = info.header_species,
            genera = info.header_genus,
        )
    return InputFile.Unknown(path)


def sequences_from_model(input: SequenceModel2):
    from itaxotools.taxi3.sequences import Sequences, SequenceHandler
    from ..model import SequenceModel2

    if input.type == FileFormat.Tabfile:
        return Sequences.fromPath(
            input.path,
            SequenceHandler.Tabfile,
            hasHeader = True,
            idColumn=input.index_column,
            seqColumn=input.sequence_column,
        )
    raise Exception(f'Cannot create sequences from input: {input}')


def partition_from_model(input: PartitionModel):
    from itaxotools.taxi3.partitions import Partition, PartitionHandler
    from ..model import PartitionModel

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
    raise Exception(f'Cannot create partition from input: {input}')


def versus_all(

    work_dir: Path,

    perform_species: bool,
    perform_genera: bool,

    input_sequences: AttrDict,
    input_species: AttrDict,
    input_genera: AttrDict,

    alignment_mode: AlignmentMode,
    alignment_write_pairs: bool,
    alignment_pairwise_scores: dict,

    distance_metrics: list[DistanceMetric],
    distance_metrics_bbc_k: int,
    distance_linear: bool,
    distance_matricial: bool,
    distance_percentile: bool,
    distance_precision: int,
    distance_missing: str,

    statistics_all: bool,
    statistics_species: bool,
    statistics_genus: bool,

    plot_histograms: bool,
    plot_binwidth: float,

    **kwargs

) -> tuple[Path, float]:

    from itaxotools.taxi3.tasks.versus_all import VersusAll
    from itaxotools.taxi3.distances import DistanceMetric as BackendDistanceMetric
    from itaxotools.taxi3.sequences import Sequences, SequenceHandler
    from itaxotools.taxi3.partitions import Partition, PartitionHandler
    from itaxotools.taxi3.align import Scores

    task = VersusAll()
    task.work_dir = work_dir
    task.progress_handler = progress_handler

    task.input.sequences = sequences_from_model(input_sequences)
    if perform_species:
        task.input.species = partition_from_model(input_species)
    if perform_genera:
        task.input.genera = partition_from_model(input_genera)

    task.params.pairs.align = alignment_mode in [AlignmentMode.PairwiseAlignment]
    task.params.pairs.scores = Scores(**alignment_pairwise_scores)
    task.params.pairs.write = alignment_write_pairs

    metrics_tr = {
        DistanceMetric.Uncorrected: (BackendDistanceMetric.Uncorrected, []),
        DistanceMetric.UncorrectedWithGaps: (BackendDistanceMetric.UncorrectedWithGaps, []),
        DistanceMetric.JukesCantor: (BackendDistanceMetric.JukesCantor, []),
        DistanceMetric.Kimura2Parameter: (BackendDistanceMetric.Kimura2P, []),
        DistanceMetric.NCD: (BackendDistanceMetric.NCD, []),
        DistanceMetric.BBC: (BackendDistanceMetric.BBC, [distance_metrics_bbc_k]),
    }
    metrics = [
        metrics_tr[metric][0](*metrics_tr[metric][1])
        for metric in distance_metrics
    ]
    task.params.distances.metrics = metrics
    task.params.distances.write_linear = distance_linear
    task.params.distances.write_matricial = distance_matricial

    task.params.format.float = f'{{:.{distance_precision}f}}'
    task.params.format.percentage = f'{{:.{distance_precision}f}}%'
    task.params.format.missing = distance_missing
    task.params.format.percentage_multiply = distance_percentile

    task.params.stats.all = statistics_all
    task.params.stats.species = statistics_species
    task.params.stats.genera = statistics_genus

    task.params.plot.histograms = plot_histograms
    task.params.plot.binwidth = plot_binwidth
    task.params.plot.formats = ['pdf']

    results = task.start()

    return results
