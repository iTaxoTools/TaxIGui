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

from .. import app
from ..tasks import versus_all
from ..model import Item, ItemModel, Object, SequenceModel
from ..types import Notification, SequenceFile, PairwiseScore, DistanceMetric, AlignmentMode, StatisticsGroup, VersusAllSubtask
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


def dummy_get_sequence_file_info(path):
    import time
    print('...')
    time.sleep(1)
    if path.suffix in ['.tsv', '.tab']:
        return SequenceFile.Tabfile(path, ['seqid', 'sequences'])
    return SequenceFile.Unknown(path)


class PairwiseScores(EnumObject):
    enum = PairwiseScore

    def as_dict(self):
        return {
            score.key: self.properties[score.key].value
            for score in self.enum
        }

    def is_valid(self):
        return not any(
            self.properties[score.key].value is None
            for score in self.enum
        )


class DistanceMetrics(EnumObject):
    enum = DistanceMetric

    bbc_k = Property(object, 10)

    def as_list(self):
        return [
            field for field in self.enum
            if self.properties[field.key].value
        ]


class StatisticsGroups(EnumObject):
    enum = StatisticsGroup


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
    distance_precision = Property(object, 4)
    distance_missing = Property(str, 'NA')

    pairwise_scores = Property(PairwiseScores)
    distance_metrics = Property(DistanceMetrics)
    statistics_groups = Property(StatisticsGroups)

    busy_main = Property(bool, False)
    busy_sequence = Property(bool, False)

    def __init__(self, name=None):
        super().__init__(name, init=versus_all.initialize)

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def readyTriggers(self):
        return [
            self.properties.input_sequences_item,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.distance_metrics.properties.bbc,
            self.distance_metrics.properties.bbc_k,
            self.properties.distance_precision,
        ]

    def isReady(self):
        if self.input_sequences_item is None:
            return False
        if not isinstance(self.input_sequences_item.object, SequenceModel):
            return False
        if self.alignment_mode == AlignmentMode.PairwiseAlignment:
            if not self.pairwise_scores.is_valid():
                return False
        if self.distance_metrics.bbc:
            if self.distance_metrics.bbc_k is None:
                return False
        if self.distance_precision is None:
            return False
        return True

    def start(self):
        self.busy = True
        self.busy_main = True
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            VersusAllSubtask.Main,
            dummy_process,
            work_dir=work_dir,
            input_sequences=self.input_sequences_item.object.path,
            input_sequences_index_column=self.input_sequences_item.object.index_column,
            input_sequences_sequence_column=self.input_sequences_item.object.sequence_column,
            perform_species=self.perform_species,
            perform_genera=self.perform_genera,
            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            alignment_pairwise_scores = self.pairwise_scores.as_dict(),
            distance_metrics=self.distance_metrics.as_list(),
            distance_metrics_bbc_k=self.distance_metrics.bbc_k,
            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,
            statistics_all=self.statistics_groups.for_all,
            statistics_species=self.statistics_groups.per_species,
            statistics_genus=self.statistics_groups.per_genus,
        )

    def add_sequence_file(self, path):
        self.busy_sequence = True
        self.exec(VersusAllSubtask.AddSequenceFile, dummy_get_sequence_file_info, path)

    def add_sequence_file_from_info(self, info):
        if info.type == SequenceFile.Tabfile:
            index = app.model.items.add_sequence(SequenceModel.Tabfile(info), focus=False)
            self.input_sequences_item = index.data(ItemModel.ItemRole)
        else:
            self.notification.emit(Notification.Warn('Unknown sequence-file format.'))

    def onDone(self, report):
        if report.id == VersusAllSubtask.Main:
            self.notification.emit(Notification.Info(f'{self.name} completed successfully!'))
            self.busy_main = False
        if report.id == VersusAllSubtask.AddSequenceFile:
            self.add_sequence_file_from_info(report.result)
            self.busy_sequence = False
        self.busy = False

    def onFail(self, report):
        super().onFail(report)
        self.busy_main = False
        self.busy_sequence = False

    def onError(self, report):
        super().onError(report)
        self.busy_main = False
        self.busy_sequence = False
