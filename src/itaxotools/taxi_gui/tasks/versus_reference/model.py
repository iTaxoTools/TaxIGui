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
from itaxotools.taxi_gui.utility import EnumObject, Property, Instance, human_readable_seconds
from itaxotools.taxi_gui.model.common import Task
from itaxotools.taxi_gui.model.sequence import SequenceModel2
from itaxotools.taxi_gui.model.input_file import InputFileModel

from . import process
from .types import VersusReferenceSubtask


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

    bbc_k = Property(int | None, 10)

    def as_list(self):
        return [
            field for field in self.enum
            if self.properties[field.key].value
        ]


class Model(Task):
    task_name = 'Versus Reference'

    input_data = Property(SequenceModel2, None)
    input_reference = Property(SequenceModel2, None)

    alignment_mode = Property(AlignmentMode, AlignmentMode.PairwiseAlignment)
    alignment_write_pairs = Property(bool, True)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int | None, 4)
    distance_missing = Property(str, 'NA')

    pairwise_scores = Property(PairwiseScores, Instance)
    distance_metrics = Property(DistanceMetrics, Instance)
    main_metric = Property(DistanceMetric, None)

    busy_main = Property(bool, False)
    busy_data = Property(bool, False)
    busy_reference = Property(bool, False)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.exec(VersusReferenceSubtask.Initialize, process.initialize)

    def readyTriggers(self):
        return [
            self.properties.input_data,
            self.properties.input_reference,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.distance_metrics.properties.bbc,
            self.distance_metrics.properties.bbc_k,
            self.properties.distance_precision,
        ]

    def isReady(self):
        if self.input_data is None:
            return False
        if self.input_reference is None:
            return False
        if not self.input_data.file_item:
            return False
        if not self.input_reference.file_item:
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
        super().start()
        self.busy_main = True
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            VersusReferenceSubtask.Main,
            process.execute,
            work_dir=work_dir,

            input_data=self.input_data.as_dict(),
            input_reference=self.input_reference.as_dict(),

            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            alignment_pairwise_scores = self.pairwise_scores.as_dict(),

            distance_metrics=self.distance_metrics.as_list(),
            distance_metrics_bbc_k=self.distance_metrics.bbc_k,
            main_metric=self.main_metric,

            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,
        )

    def add_data_file(self, path):
        self.busy = True
        self.busy_data = True
        self.exec(VersusReferenceSubtask.AddDataFile, process.get_file_info, path)

    def add_reference_file(self, path):
        self.busy = True
        self.busy_reference = True
        self.exec(VersusReferenceSubtask.AddReferenceFile, process.get_file_info, path)

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
                },
                InputFileModel.Fasta: {
                    SequenceModel2: SequenceModel2.Fasta,
                },
            }[type(file_item.object)][model_parent]
        except Exception:
            self.notification.emit(Notification.Warn('Unexpected file type.'))
            return None
        return model_type(file_item, *args, **kwargs)

    def set_data_file_from_file_item(self, file_item):
            self.input_data = self.get_model_from_file_item(file_item, SequenceModel2)

    def set_reference_file_from_file_item(self, file_item):
            self.input_reference = self.get_model_from_file_item(file_item, SequenceModel2)

    def onDone(self, report):
        if report.id == VersusReferenceSubtask.Initialize:
            return
        if report.id == VersusReferenceSubtask.Main:
            time_taken = human_readable_seconds(report.result.seconds_taken)
            self.notification.emit(Notification.Info(f'{self.name} completed successfully!\nTime taken: {time_taken}.'))
            self.dummy_results = report.result.output_directory
            self.dummy_time = report.result.seconds_taken
            self.busy_main = False
            self.done = True
        if report.id == VersusReferenceSubtask.AddDataFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_data_file_from_file_item(file_item)
            self.busy_data = False
        if report.id == VersusReferenceSubtask.AddReferenceFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_reference_file_from_file_item(file_item)
            self.busy_reference = False
        self.busy = False

    def onStop(self, report):
        super().onStop(report)
        self.busy_main = False
        self.busy_data = False
        self.busy_reference = False

    def onFail(self, report):
        super().onFail(report)
        self.busy_main = False
        self.busy_data = False
        self.busy_reference = False

    def onError(self, report):
        super().onError(report)
        self.busy_main = False
        self.busy_data = False
        self.busy_reference = False

    def clear(self):
        self.dummy_results = None
        self.dummy_time = None
        self.done = False

    def save(self, destination: Path):
        copytree(self.dummy_results, destination, dirs_exist_ok=True)
        self.notification.emit(Notification.Info('Saved files successfully!'))
