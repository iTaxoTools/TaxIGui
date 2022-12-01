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

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from ..tasks import versus_all
from ..types import PairwiseScore, AlignmentMode
from ..utility import EnumObject
from .common import Property, Task
from .sequence import SequenceModel


def dummy_process(**kwargs):
    for k, v in kwargs.items():
        print(k, v)
    import time
    print('...')
    time.sleep(2)
    print('Done!~')
    return 42


class PairwiseScores(EnumObject):
    enum = PairwiseScore

    def is_valid(self):
        return not any(
            not isinstance(self.properties[score.key].value, int)
            for score in self.enum)


class VersusAllModel(Task):
    task_name = 'Versus All'

    input_sequences_item = Property(object, None)
    perform_species = Property(bool, True)
    # todo: species item
    perform_genera = Property(bool, False)
    # todo: genera item

    alignment_mode = Property(AlignmentMode, AlignmentMode.NoAlignment)
    alignment_write_pairs = Property(bool, True)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int, 4)
    distance_missing = Property(str, 'NA')

    pairwise_scores = Property(PairwiseScores)

    def __init__(self, name=None):
        super().__init__(name, init=versus_all.initialize)

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def readyTriggers(self):
        return [
            self.properties.input_sequences_item,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
        ]

    def isReady(self):
        if self.input_sequences_item is None:
            return False
        if not isinstance(self.input_sequences_item.object, SequenceModel):
            return False
        if self.alignment_mode == AlignmentMode.PairwiseAlignment:
            if not self.pairwise_scores.is_valid():
                return False
        if self.distance_precision is None:
            return False
        return True

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            dummy_process,
            work_dir=work_dir,
            input_sequences=self.input_sequences_item.object.path,
            perform_species=self.perform_species,
            perform_genera=self.perform_genera,
            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            **{f'alignment_pairwise_{score.key}': getattr(self.pairwise_scores, score.key) for score in PairwiseScore},
            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,
        )

    def onDone(self, results):
        self.done()
