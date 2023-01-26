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
from typing import Dict, List, Optional, Tuple

from ..types import ComparisonMode, ColumnFilter, AlignmentMode, DistanceMetric, FileFormat


@dataclass
class DereplicateResults:
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
    if info.format == FileFormat.Fasta:
        return InputFile.Fasta(
            path = path,
            size = info.size,
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
    elif input.type == FileFormat.Fasta:
        return Sequences.fromPath(
            input.path,
            SequenceHandler.Fasta,
        )
    raise Exception(f'Cannot create sequences from input: {input}')


def dereplicate(

    work_dir: Path,

    input_sequences: AttrDict,

    alignment_mode: AlignmentMode,
    alignment_write_pairs: bool,
    alignment_pairwise_scores: dict,

    distance_metric: DistanceMetric,
    distance_metrics_bbc_k: int,
    distance_linear: bool,
    distance_matricial: bool,
    distance_percentile: bool,
    distance_precision: int,
    distance_missing: str,

    similarity_threshold: float,
    length_threshold: int,

    **kwargs

) -> tuple[Path, float]:

    from itaxotools.taxi3.tasks.dereplicate import Dereplicate
    from itaxotools.taxi3.distances import DistanceMetric as BackendDistanceMetric
    from itaxotools.taxi3.sequences import Sequences, SequenceHandler
    from itaxotools.taxi3.partitions import Partition, PartitionHandler
    from itaxotools.taxi3.align import Scores

    task = Dereplicate()
    task.work_dir = work_dir
    task.progress_handler = progress_handler

    task.input = sequences_from_model(input_sequences)
    task.set_output_format_from_path(input_sequences.path)

    task.params.pairs.align = bool(alignment_mode == AlignmentMode.PairwiseAlignment)
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
    metric = metrics_tr[distance_metric][0](*metrics_tr[distance_metric][1])

    task.params.distances.metric = metric
    task.params.distances.write_linear = distance_linear
    task.params.distances.write_matricial = distance_matricial

    task.params.format.float = f'{{:.{distance_precision}f}}'
    task.params.format.percentage = f'{{:.{distance_precision}f}}%'
    task.params.format.missing = distance_missing
    task.params.format.percentage_multiply = distance_percentile

    results = task.start()

    return results
