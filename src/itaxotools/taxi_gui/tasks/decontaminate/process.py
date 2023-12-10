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

from dataclasses import dataclass
from pathlib import Path

from itaxotools.common.utility import AttrDict

from ..common.process import progress_handler, sequences_from_model
from ..common.types import AlignmentMode, DistanceMetric
from .types import DecontaminateMode


@dataclass
class DecontaminateResults:
    pass


def initialize():
    import itaxotools

    itaxotools.progress_handler("Initializing...")
    from itaxotools.taxi2.tasks.decontaminate import Decontaminate  # noqa
    from itaxotools.taxi2.tasks.decontaminate2 import Decontaminate2  # noqa


def execute(
    work_dir: Path,
    decontaminate_mode: DecontaminateMode,
    input_sequences: AttrDict,
    outgroup_sequences: AttrDict,
    ingroup_sequences: AttrDict,
    alignment_mode: AlignmentMode,
    alignment_write_pairs: bool,
    alignment_pairwise_scores: dict,
    distance_metric: DistanceMetric,
    distance_metric_bbc_k: int,
    distance_linear: bool,
    distance_matricial: bool,
    distance_percentile: bool,
    distance_precision: int,
    distance_missing: str,
    similarity_threshold: float,
    outgroup_weight: int,
    ingroup_weight: int,
    **kwargs,
) -> tuple[Path, float]:
    from itaxotools.taxi2.align import Scores
    from itaxotools.taxi2.distances import DistanceMetric as BackendDistanceMetric
    from itaxotools.taxi2.tasks.decontaminate import Decontaminate
    from itaxotools.taxi2.tasks.decontaminate2 import Decontaminate2

    if decontaminate_mode == DecontaminateMode.DECONT:
        task = Decontaminate()
        task.params.thresholds.similarity = similarity_threshold
    elif decontaminate_mode == DecontaminateMode.DECONT2:
        task = Decontaminate2()
        task.ingroup = sequences_from_model(ingroup_sequences)
        task.params.weights.outgroup = outgroup_weight
        task.params.weights.ingroup = ingroup_weight

    task.work_dir = work_dir
    task.progress_handler = progress_handler

    task.input = sequences_from_model(input_sequences)
    task.set_output_format_from_path(input_sequences.info.path)
    task.outgroup = sequences_from_model(outgroup_sequences)

    task.params.pairs.align = bool(alignment_mode == AlignmentMode.PairwiseAlignment)
    task.params.pairs.scores = Scores(**alignment_pairwise_scores)
    task.params.pairs.write = alignment_write_pairs

    metrics_tr = {
        DistanceMetric.Uncorrected: (BackendDistanceMetric.Uncorrected, []),
        DistanceMetric.UncorrectedWithGaps: (
            BackendDistanceMetric.UncorrectedWithGaps,
            [],
        ),
        DistanceMetric.JukesCantor: (BackendDistanceMetric.JukesCantor, []),
        DistanceMetric.Kimura2Parameter: (BackendDistanceMetric.Kimura2P, []),
        DistanceMetric.NCD: (BackendDistanceMetric.NCD, []),
        DistanceMetric.BBC: (BackendDistanceMetric.BBC, [distance_metric_bbc_k]),
    }
    metric = metrics_tr[distance_metric][0](*metrics_tr[distance_metric][1])

    task.params.distances.metric = metric
    task.params.distances.write_linear = distance_linear
    task.params.distances.write_matricial = distance_matricial

    task.params.format.float = f"{{:.{distance_precision}f}}"
    task.params.format.percentage = f"{{:.{distance_precision}f}}%"
    task.params.format.missing = distance_missing
    task.params.format.percentage_multiply = distance_percentile

    results = task.start()

    return results
