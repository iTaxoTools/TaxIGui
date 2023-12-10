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
from shutil import copytree

from itaxotools.common.bindings import Binder, EnumObject, Instance, Property
from itaxotools.taxi_gui.model.sequence import SequenceModel
from itaxotools.taxi_gui.model.tasks import SubtaskModel, TaskModel
from itaxotools.taxi_gui.types import Notification
from itaxotools.taxi_gui.utility import human_readable_seconds

from ..common.model import FileInfoSubtaskModel, ImportedInputModel
from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from . import process


class PairwiseScores(EnumObject):
    enum = PairwiseScore

    def as_dict(self):
        return {score.key: self.properties[score.key].value for score in self.enum}

    def is_valid(self):
        return not any(self.properties[score.key].value is None for score in self.enum)


class DistanceMetrics(EnumObject):
    enum = DistanceMetric

    bbc_k = Property(int | None, 10)

    def as_list(self):
        return [field for field in self.enum if self.properties[field.key].value]


class Model(TaskModel):
    task_name = "Versus Reference"

    input_data = Property(ImportedInputModel, ImportedInputModel(SequenceModel))
    input_reference = Property(ImportedInputModel, ImportedInputModel(SequenceModel))

    alignment_mode = Property(AlignmentMode, AlignmentMode.PairwiseAlignment)
    alignment_write_pairs = Property(bool, True)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int | None, 4)
    distance_missing = Property(str, "NA")

    pairwise_scores = Property(PairwiseScores, Instance)
    distance_metrics = Property(DistanceMetrics, Instance)
    main_metric = Property(DistanceMetric, None)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.binder = Binder()

        self.subtask_init = SubtaskModel(self, bind_busy=False)
        self.subtask_data = FileInfoSubtaskModel(self)
        self.subtask_reference = FileInfoSubtaskModel(self)

        self.binder.bind(self.subtask_data.done, self.onDoneInfoData)
        self.binder.bind(self.subtask_reference.done, self.onDoneInfoReference)

        self.binder.bind(self.input_data.notification, self.notification)
        self.binder.bind(self.input_reference.notification, self.notification)

        for handle in [
            self.properties.busy_subtask,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.distance_metrics.properties.bbc,
            self.distance_metrics.properties.bbc_k,
            self.properties.distance_precision,
            self.input_data.updated,
            self.input_reference.updated,
        ]:
            self.binder.bind(handle, self.checkReady)

        self.subtask_init.start(process.initialize)

    def isReady(self):
        if self.busy_subtask:
            return False
        if not self.input_data.is_valid():
            return False
        if not self.input_reference.is_valid():
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
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            process.execute,
            work_dir=work_dir,
            input_data=self.input_data.as_dict(),
            input_reference=self.input_reference.as_dict(),
            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            alignment_pairwise_scores=self.pairwise_scores.as_dict(),
            distance_metrics=self.distance_metrics.as_list(),
            distance_metrics_bbc_k=self.distance_metrics.bbc_k,
            main_metric=self.main_metric,
            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,
        )

    def onDone(self, report):
        time_taken = human_readable_seconds(report.result.seconds_taken)
        self.notification.emit(
            Notification.Info(
                f"{self.name} completed successfully!\nTime taken: {time_taken}."
            )
        )
        self.dummy_results = report.result.output_directory
        self.dummy_time = report.result.seconds_taken
        self.busy = False
        self.done = True

    def onDoneInfoData(self, info):
        self.input_data.add_info(info)

    def onDoneInfoReference(self, info):
        self.input_reference.add_info(info)

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
        self.notification.emit(Notification.Info("Saved files successfully!"))
