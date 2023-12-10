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
from .types import DecontaminateMode


class PairwiseScores(EnumObject):
    enum = PairwiseScore

    def as_dict(self):
        return {score.key: self.properties[score.key].value for score in self.enum}

    def is_valid(self):
        return not any(self.properties[score.key].value is None for score in self.enum)


class Model(TaskModel):
    task_name = "Decontaminate"

    decontaminate_mode = Property(DecontaminateMode, DecontaminateMode.DECONT)

    input_sequences = Property(ImportedInputModel, ImportedInputModel(SequenceModel))
    outgroup_sequences = Property(ImportedInputModel, ImportedInputModel(SequenceModel))
    ingroup_sequences = Property(ImportedInputModel, ImportedInputModel(SequenceModel))

    alignment_mode = Property(AlignmentMode, AlignmentMode.PairwiseAlignment)
    alignment_write_pairs = Property(bool, True)

    pairwise_scores = Property(PairwiseScores, Instance)

    distance_metric = Property(DistanceMetric, DistanceMetric.Uncorrected)
    distance_metric_bbc_k = Property(int | None, 10)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int | None, 4)
    distance_missing = Property(str, "NA")

    similarity_threshold = Property(float | None, 0.03)
    outgroup_weight = Property(float, 1.00)
    ingroup_weight = Property(float, 1.00)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.binder = Binder()

        self.subtask_init = SubtaskModel(self, bind_busy=False)
        self.subtask_input = FileInfoSubtaskModel(self)
        self.subtask_outgroup = FileInfoSubtaskModel(self)
        self.subtask_ingroup = FileInfoSubtaskModel(self)

        self.binder.bind(self.subtask_input.done, self.onDoneInfoInput)
        self.binder.bind(self.subtask_outgroup.done, self.onDoneInfoOutgroup)
        self.binder.bind(self.subtask_ingroup.done, self.onDoneInfoIngroup)
        self.binder.bind(self.properties.alignment_mode, self.set_metric_from_mode)
        self.binder.bind(self.properties.alignment_mode, self.set_similarity_from_mode)

        self.binder.bind(self.input_sequences.notification, self.notification)
        self.binder.bind(self.outgroup_sequences.notification, self.notification)
        self.binder.bind(self.ingroup_sequences.notification, self.notification)

        for handle in [
            self.properties.busy_subtask,
            self.properties.decontaminate_mode,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.properties.distance_metric,
            self.properties.distance_metric_bbc_k,
            self.properties.distance_precision,
            self.input_sequences.updated,
            self.outgroup_sequences.updated,
            self.ingroup_sequences.updated,
        ]:
            self.binder.bind(handle, self.checkReady)

        self.subtask_init.start(process.initialize)

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

    def isReady(self):
        if self.busy_subtask:
            return False
        if not self.input_sequences.is_valid():
            return False
        if self.decontaminate_mode == DecontaminateMode.DECONT:
            if not self.outgroup_sequences.is_valid():
                return False
        if self.decontaminate_mode == DecontaminateMode.DECONT2:
            if not self.outgroup_sequences.is_valid():
                return False
            if not self.ingroup_sequences.is_valid():
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
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            process.execute,
            work_dir=work_dir,
            decontaminate_mode=self.decontaminate_mode,
            input_sequences=self.input_sequences.as_dict(),
            outgroup_sequences=self.outgroup_sequences.as_dict(),
            ingroup_sequences=self.ingroup_sequences.as_dict(),
            alignment_mode=self.alignment_mode,
            alignment_write_pairs=self.alignment_write_pairs,
            alignment_pairwise_scores=self.pairwise_scores.as_dict(),
            distance_metric=self.distance_metric,
            distance_metric_bbc_k=self.distance_metric_bbc_k,
            distance_linear=self.distance_linear,
            distance_matricial=self.distance_matricial,
            distance_percentile=self.distance_percentile,
            distance_precision=self.distance_precision,
            distance_missing=self.distance_missing,
            similarity_threshold=self.similarity_threshold,
            outgroup_weight=self.outgroup_weight,
            ingroup_weight=self.ingroup_weight,
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

    def onDoneInfoInput(self, info):
        self.input_sequences.add_info(info)

    def onDoneInfoOutgroup(self, info):
        self.outgroup_sequences.add_info(info)

    def onDoneInfoIngroup(self, info):
        self.ingroup_sequences.add_info(info)

    def onStop(self, report):
        super().onStop(report)
        self.busy_main = False
        self.busy_input = False
        self.busy_outgroup = False
        self.busy_ingroup = False

    def onFail(self, report):
        super().onFail(report)
        self.busy_main = False
        self.busy_input = False
        self.busy_outgroup = False
        self.busy_ingroup = False

    def onError(self, report):
        super().onError(report)
        self.busy_main = False
        self.busy_input = False
        self.busy_outgroup = False
        self.busy_ingroup = False

    def clear(self):
        self.dummy_results = None
        self.dummy_time = None
        self.done = False

    def save(self, destination: Path):
        copytree(self.dummy_results, destination, dirs_exist_ok=True)
        self.notification.emit(Notification.Info("Saved files successfully!"))
