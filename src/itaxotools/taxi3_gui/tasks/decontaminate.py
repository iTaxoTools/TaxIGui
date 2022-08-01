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
from typing import Dict, List, Tuple

from ..types import ComparisonMode, SequenceReader


@dataclass
class DecontaminateResults:
    decontaminated: Path
    contaminants: Path
    summary: Path


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


def decontaminate(
    work_dir: Path,
    inputs: List[Path],
    input_reader_type: SequenceReader,
    reference_path: Path,
    reference_reader_type: SequenceReader,
    comparison_mode: ComparisonMode,
    similarity_threshold: float,
) -> Dict[Path, Tuple[Path, Path]]:

    import itaxotools
    itaxotools.progress_handler('Decontaminating...')

    from itaxotools.taxi3.library.config import AlignmentScores, Config
    from itaxotools.taxi3.library.datatypes import (
        CompleteData, FastaReader, GenbankReader, Metric, SequenceData,
        TabfileReader, ValidFilePath, XlsxReader)
    from itaxotools.taxi3.library.task import Alignment, Decontaminate

    readers = {
        SequenceReader.TabfileReader: TabfileReader,
        SequenceReader.GenbankReader: GenbankReader,
        SequenceReader.XlsxReader: XlsxReader,
        SequenceReader.FastaReader: FastaReader,
    }
    input_reader = readers[input_reader_type]
    reference_reader = readers[reference_reader_type]

    alignment = {
        ComparisonMode.AlignmentFree: Alignment.AlignmentFree,
        ComparisonMode.PairwiseAlignment: Alignment.Pairwise,
        ComparisonMode.AlreadyAligned: Alignment.AlreadyAligned,
    }[comparison_mode.type]

    config = None
    if comparison_mode.type is ComparisonMode.PairwiseAlignment:
        scores = AlignmentScores._from_scores_dict(comparison_mode.config)
        config = Config(scores)

    reference = SequenceData.from_path(ValidFilePath(reference_path), reference_reader)

    decontaminated_dir = work_dir / 'decontaminated'
    decontaminated_dir.mkdir()
    contaminants_dir = work_dir / 'contaminants'
    contaminants_dir.mkdir()
    summary_dir = work_dir / 'summary'
    summary_dir.mkdir()

    results = dict()

    for input in inputs:
        decontaminated = decontaminated_dir / f'{input.stem}.decontaminated.tsv'
        contaminants = contaminants_dir / f'{input.stem}.contaminants.tsv'
        summary = summary_dir / f'{input.stem}.summary.txt'

        decontaminated.unlink(missing_ok=True)
        contaminants.unlink(missing_ok=True)
        summary.unlink(missing_ok=True)

        sequence = CompleteData.from_path(ValidFilePath(input), input_reader)

        print(f'Decontaminating {input.name}')
        task = Decontaminate(warn=print)
        task.progress_handler = progress_handler
        task.similarity = similarity_threshold
        task.alignment = alignment
        task._calculate_distances.config = config
        task._calculate_distances.metrics = [Metric.Uncorrected]
        task.data = sequence
        task.reference = reference
        task.start()

        for output in task.result:
            output.decontaminated.append_to_file(decontaminated)
            output.contaminates.append_to_file(contaminants)
            output.summary.append_to_file(summary)

        results[input] = DecontaminateResults(decontaminated, contaminants, summary)

    return results


def decontaminate2(
    work_dir: Path,
    inputs: List[Path],
    input_reader_type: SequenceReader,
    reference_outgroup_path: Path,
    reference_outgroup_reader_type: SequenceReader,
    reference_ingroup_path: Path,
    reference_ingroup_reader_type: SequenceReader,
    outgroup_weight: float,
    comparison_mode: ComparisonMode,
) -> Dict[Path, Tuple[Path, Path]]:

    import itaxotools
    itaxotools.progress_handler('Decontaminating...')

    from itaxotools.taxi3.library.config import AlignmentScores, Config
    from itaxotools.taxi3.library.datatypes import (
        CompleteData, FastaReader, GenbankReader, Metric, SequenceData,
        TabfileReader, ValidFilePath, XlsxReader)
    from itaxotools.taxi3.library.task import Alignment, Decontaminate2

    readers = {
        SequenceReader.TabfileReader: TabfileReader,
        SequenceReader.GenbankReader: GenbankReader,
        SequenceReader.XlsxReader: XlsxReader,
        SequenceReader.FastaReader: FastaReader,
    }
    input_reader = readers[input_reader_type]
    reference_outgroup_reader = readers[reference_outgroup_reader_type]
    reference_ingroup_reader = readers[reference_ingroup_reader_type]

    alignment = {
        ComparisonMode.AlignmentFree: Alignment.AlignmentFree,
        ComparisonMode.PairwiseAlignment: Alignment.Pairwise,
        ComparisonMode.AlreadyAligned: Alignment.AlreadyAligned,
    }[type(comparison_mode)]

    config = None
    if comparison_mode.type is ComparisonMode.PairwiseAlignment:
        scores = AlignmentScores._from_scores_dict(comparison_mode.config)
        config = Config(scores)

    reference_outgroup = SequenceData.from_path(ValidFilePath(reference_outgroup_path), reference_outgroup_reader)
    reference_ingroup = SequenceData.from_path(ValidFilePath(reference_ingroup_path), reference_ingroup_reader)

    decontaminated_dir = work_dir / 'decontaminated'
    decontaminated_dir.mkdir()
    contaminants_dir = work_dir / 'contaminants'
    contaminants_dir.mkdir()
    summary_dir = work_dir / 'summary'
    summary_dir.mkdir()

    results = dict()

    for input in inputs:
        decontaminated = decontaminated_dir / f'{input.stem}.decontaminated.tsv'
        contaminants = contaminants_dir / f'{input.stem}.contaminants.tsv'
        summary = summary_dir / f'{input.stem}.summary.txt'

        decontaminated.unlink(missing_ok=True)
        contaminants.unlink(missing_ok=True)
        summary.unlink(missing_ok=True)

        sequence = CompleteData.from_path(ValidFilePath(input), input_reader)

        print(f'Decontaminating {input.name}')
        task = Decontaminate2(warn=print)
        task.progress_handler = progress_handler
        task.alignment = alignment
        task.outgroup_weight = outgroup_weight
        task._calculate_distances.config = config
        task._calculate_distances.metrics = [Metric.Uncorrected]
        task.data = sequence
        task.outgroup = reference_outgroup
        task.ingroup = reference_ingroup
        task.start()

        for output in task.result:
            output.decontaminated.append_to_file(decontaminated)
            output.contaminates.append_to_file(contaminants)
            output.summary.append_to_file(summary)

        results[input] = DecontaminateResults(decontaminated, contaminants, summary)

    return results
