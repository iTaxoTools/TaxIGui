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

from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from pathlib import Path

from ..types import AlignmentType, SequenceReader


@dataclass
class DereplicateResults:
    dereplicated: Path
    excluded: Path


def dereplicate(
    work_dir: Path,
    inputs: List[Path],
    reader_type: SequenceReader,
    alignment_type: AlignmentType,
    similarity_threshold: float,
    length_threshold: Optional[int],
) -> Dict[Path, Tuple[Path, Path]]:

    from itaxotools.taxi3.library.datatypes import CompleteData, ValidFilePath, TabfileReader, XlsxReader, FastaReader, GenbankReader
    from itaxotools.taxi3.library.task import Dereplicate, Alignment
    from itaxotools.taxi3.library.datatypes import Metric

    reader = {
        SequenceReader.TabfileReader: TabfileReader,
        SequenceReader.GenbankReader: GenbankReader,
        SequenceReader.XlsxReader: XlsxReader,
        SequenceReader.FastaReader: FastaReader,
    }[reader_type]

    alignment = {
        AlignmentType.AlignmentFree: Alignment.AlignmentFree,
        AlignmentType.PairwiseAlignment: Alignment.Pairwise,
        AlignmentType.AlreadyAligned: Alignment.AlreadyAligned,
    }[alignment_type]

    excluded_dir = work_dir / 'excluded'
    excluded_dir.mkdir()
    dereplicated_dir = work_dir / 'dereplicated'
    dereplicated_dir.mkdir()

    results = dict()

    for input in inputs:
        dereplicated = dereplicated_dir / f'{input.stem}.dereplicated.tsv'
        excluded = excluded_dir / f'{input.stem}.excluded.tsv'

        dereplicated.unlink(missing_ok=True)
        excluded.unlink(missing_ok=True)

        sequence = CompleteData.from_path(ValidFilePath(input), reader)

        print(f'Dereplicating {input.name}')
        task = Dereplicate(warn=print)
        task.similarity = similarity_threshold
        task.length_threshold = length_threshold
        task._calculate_distances.alignment = alignment
        task._calculate_distances.metrics = [Metric.Uncorrected]
        task.data = sequence
        task.start()

        for output in task.result:
            output.included.append_to_file(dereplicated)
            output.excluded.append_to_file(excluded)

        results[input] = DereplicateResults(dereplicated, excluded)

    return results
