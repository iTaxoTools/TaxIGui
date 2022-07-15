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

from typing import Tuple, List, Dict
from dataclasses import dataclass
from pathlib import Path

from ..types import AlignmentType, SequenceReader


@dataclass
class DecontaminateResults:
    decontaminated: Path
    contaminants: Path
    summary: Path


@dataclass
class Decontaminate2Results:
    decontaminated: Path
    contaminants: Path


def initialize():
    from itaxotools.taxi3.library import datatypes  # noqa
    from itaxotools.taxi3.library import task  # noqa


def decontaminate(
    work_dir: Path,
    inputs: List[Path],
    input_reader_type: SequenceReader,
    reference_path: Path,
    reference_reader_type: SequenceReader,
    alignment_type: AlignmentType,
    similarity_threshold: float,
) -> Dict[Path, Tuple[Path, Path]]:

    from itaxotools.taxi3.library.datatypes import (
        CompleteData, SequenceData, ValidFilePath, Metric,
        TabfileReader, XlsxReader, FastaReader, GenbankReader)
    from itaxotools.taxi3.library.task import Decontaminate, Alignment

    readers = {
        SequenceReader.TabfileReader: TabfileReader,
        SequenceReader.GenbankReader: GenbankReader,
        SequenceReader.XlsxReader: XlsxReader,
        SequenceReader.FastaReader: FastaReader,
    }
    input_reader = readers[input_reader_type]
    reference_reader = readers[reference_reader_type]

    alignment = {
        AlignmentType.AlignmentFree: Alignment.AlignmentFree,
        AlignmentType.PairwiseAlignment: Alignment.Pairwise,
        AlignmentType.AlreadyAligned: Alignment.AlreadyAligned,
    }[alignment_type]

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

        sequence = CompleteData.from_path(ValidFilePath(input), input_reader)

        print(f'Decontaminating {input.name}')
        task = Decontaminate(warn=print)
        task.similarity = similarity_threshold
        task.alignment = alignment
        task._calculate_distances.metrics = [Metric.Uncorrected]
        task.data = sequence
        task.reference = reference
        task.reference2 = None
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
    alignment_type: AlignmentType,
) -> Dict[Path, Tuple[Path, Path]]:

    from itaxotools.taxi3.library.datatypes import (
        CompleteData, SequenceData, ValidFilePath, Metric,
        TabfileReader, XlsxReader, FastaReader, GenbankReader)
    from itaxotools.taxi3.library.task import Decontaminate, Alignment

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
        AlignmentType.AlignmentFree: Alignment.AlignmentFree,
        AlignmentType.PairwiseAlignment: Alignment.Pairwise,
        AlignmentType.AlreadyAligned: Alignment.AlreadyAligned,
    }[alignment_type]

    reference_outgroup = SequenceData.from_path(ValidFilePath(reference_outgroup_path), reference_outgroup_reader)
    reference_ingroup = SequenceData.from_path(ValidFilePath(reference_ingroup_path), reference_ingroup_reader)

    decontaminated_dir = work_dir / 'decontaminated'
    decontaminated_dir.mkdir()
    contaminants_dir = work_dir / 'contaminants'
    contaminants_dir.mkdir()

    results = dict()

    for input in inputs:
        decontaminated = decontaminated_dir / f'{input.stem}.decontaminated.tsv'
        contaminants = contaminants_dir / f'{input.stem}.contaminants.tsv'

        decontaminated.unlink(missing_ok=True)
        contaminants.unlink(missing_ok=True)

        sequence = CompleteData.from_path(ValidFilePath(input), input_reader)

        print(f'Decontaminating {input.name}')
        task = Decontaminate(warn=print)
        task.alignment = alignment
        task._calculate_distances.metrics = [Metric.Uncorrected]
        task.data = sequence
        task.reference = reference_outgroup
        task.reference2 = reference_ingroup
        task.start()

        for output in task.result:
            output.decontaminated.append_to_file(decontaminated)
            output.contaminates.append_to_file(contaminants)

        results[input] = Decontaminate2Results(decontaminated, contaminants)

    return results
