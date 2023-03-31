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

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.model import Item, ItemModel, Object
from itaxotools.taxi_gui.types import Notification, InputFile, PairwiseScore, DistanceMetric, AlignmentMode, StatisticsGroup
from itaxotools.taxi_gui.utility import EnumObject, Property, Instance, Binder, human_readable_seconds
from itaxotools.taxi_gui.model.common import Task
from itaxotools.taxi_gui.model.sequence import SequenceModel2
from itaxotools.taxi_gui.model.input_file import InputFileModel
from itaxotools.taxi_gui.model.partition import PartitionModel

from . import process
from .types import DereplicateSubtask


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


class StatisticsGroups(EnumObject):
    enum = StatisticsGroup


class Model(Task):
    task_name = 'Dereplicate'

    input_sequences = Property(SequenceModel2, None)

    alignment_mode = Property(AlignmentMode, AlignmentMode.PairwiseAlignment)
    alignment_write_pairs = Property(bool, True)

    pairwise_scores = Property(PairwiseScores, Instance)

    distance_metric = Property(DistanceMetric, DistanceMetric.Uncorrected)
    distance_metric_bbc_k = Property(int | None, 10)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int | None, 4)
    distance_missing = Property(str, 'NA')

    similarity_threshold = Property(float | None, 0.03)
    length_threshold = Property(int, 0)

    busy_main = Property(bool, False)
    busy_sequence = Property(bool, False)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.exec(DereplicateSubtask.Initialize, process.initialize)
        self.binder = Binder()
        self.binder.bind(self.properties.alignment_mode, self.set_metric_from_mode)
        self.binder.bind(self.properties.alignment_mode, self.set_similarity_from_mode)

    def set_metric_from_mode(self, mode: AlignmentMode):
        if mode == AlignmentMode.AlignmentFree:
            self.distance_metric = DistanceMetric.NCD
        else:
            self.distance_metric = DistanceMetric.Uncorrected

    def set_similarity_from_mode(self, mode: AlignmentMode):
        if mode == AlignmentMode.AlignmentFree:
            self.similarity_threshold = 0.07
        else:
            self.similarity_threshold = 0.03

    def readyTriggers(self):
        return [
            self.properties.input_sequences,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.properties.distance_metric,
            self.properties.distance_metric_bbc_k,
            self.properties.distance_precision,
        ]

    def isReady(self):
        if self.input_sequences is None:
            return False
        if not isinstance(self.input_sequences, SequenceModel2):
            return False
        if not self.input_sequences.file_item:
            return False
        if self.alignment_mode == AlignmentMode.PairwiseAlignment:
            if not self.pairwise_scores.is_valid():
                return False
        if self.distance_metric == DistanceMetric.BBC:
            if self.distance_metric_bbc_k is None:
                return False
        if self.distance_precision is None:
            return False
        return True

    def start(self):
        super().start()
        self.busy_main = True
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            DereplicateSubtask.Main,
            process.execute,
            work_dir=work_dir,

            input_sequences=self.input_sequences.as_dict(),

            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            alignment_pairwise_scores = self.pairwise_scores.as_dict(),

            distance_metric=self.distance_metric,
            distance_metric_bbc_k=self.distance_metric_bbc_k,
            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,

            similarity_threshold=self.similarity_threshold,
            length_threshold=self.length_threshold,
        )

    def add_sequence_file(self, path):
        self.busy = True
        self.busy_sequence = True
        self.exec(DereplicateSubtask.AddSequenceFile, process.get_file_info, path)

    def add_file_item_from_info(self, info):
        if info.type == InputFile.Tabfile:
            if len(info.headers) < 2:
                self.notification.emit(Notification.Warn('Not enough columns in tabfile.'))
                return
            index = app.model.items.add_file(InputFileModel.Tabfile(info), focus=False)
            return index.data(ItemModel.ItemRole)
        elif info.type == InputFile.Fasta:
            index = app.model.items.add_file(InputFileModel.Fasta(info), focus=False)
            return index.data(ItemModel.ItemRole)
        else:
            self.notification.emit(Notification.Warn('Unknown sequence-file format.'))
            return None

    def get_model_from_file_item(self, file_item, model_parent, *args, **kwargs):
        if file_item is None:
            return None
        try:
            model_type = {
                InputFileModel.Tabfile: {
                    SequenceModel2: SequenceModel2.Tabfile,
                    PartitionModel: PartitionModel.Tabfile,
                },
                InputFileModel.Fasta: {
                    SequenceModel2: SequenceModel2.Fasta,
                },
            }[type(file_item.object)][model_parent]
        except Exception:
            self.notification.emit(Notification.Warn('Unexpected file type.'))
            return None
        return model_type(file_item, *args, **kwargs)

    def set_sequence_file_from_file_item(self, file_item):
        self.input_sequences = self.get_model_from_file_item(file_item, SequenceModel2)

    def onDone(self, report):
        if report.id == DereplicateSubtask.Initialize:
            return
        if report.id == DereplicateSubtask.Main:
            time_taken = human_readable_seconds(report.result.seconds_taken)
            self.notification.emit(Notification.Info(f'{self.name} completed successfully!\nTime taken: {time_taken}.'))
            self.dummy_results = report.result.output_directory
            self.dummy_time = report.result.seconds_taken
            self.busy_main = False
            self.done = True
        if report.id == DereplicateSubtask.AddSequenceFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_sequence_file_from_file_item(file_item)
            self.busy_sequence = False
        self.busy = False

    def onStop(self, report):
        super().onStop(report)
        self.busy_main = False
        self.busy_sequence = False

    def onFail(self, report):
        super().onFail(report)
        self.busy_main = False
        self.busy_sequence = False

    def onError(self, report):
        super().onError(report)
        self.busy_main = False
        self.busy_sequence = False

    def clear(self):
        self.dummy_results = None
        self.dummy_time = None
        self.done = False

    def save(self, destination: Path):
        copytree(self.dummy_results, destination, dirs_exist_ok=True)
        self.notification.emit(Notification.Info('Saved files successfully!'))
