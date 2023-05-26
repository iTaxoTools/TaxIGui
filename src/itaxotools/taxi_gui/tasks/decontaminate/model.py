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

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.model.common import ItemModel
from itaxotools.taxi_gui.model.input_file import InputFileModel
from itaxotools.taxi_gui.model.partition import PartitionModel
from itaxotools.taxi_gui.model.sequence import SequenceModel
from itaxotools.taxi_gui.model.tasks import TaskModel
from itaxotools.taxi_gui.types import FileInfo, Notification
from itaxotools.taxi_gui.utility import human_readable_seconds

from ..common.process import get_file_info
from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from . import process
from .types import DecontaminateMode, DecontaminateSubtask


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


class Model(TaskModel):
    task_name = 'Decontaminate'

    decontaminate_mode = Property(DecontaminateMode, DecontaminateMode.DECONT)

    input_sequences = Property(SequenceModel, None)
    outgroup_sequences = Property(SequenceModel, None)
    ingroup_sequences = Property(SequenceModel, None)

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
    outgroup_weight = Property(float, 1.00)
    ingroup_weight = Property(float, 1.00)

    busy_main = Property(bool, False)
    busy_input = Property(bool, False)
    busy_outgroup = Property(bool, False)
    busy_ingroup = Property(bool, False)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.exec(DecontaminateSubtask.Initialize, process.initialize)
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
            self.properties.outgroup_sequences,
            self.properties.ingroup_sequences,
            self.properties.decontaminate_mode,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.properties.distance_metric,
            self.properties.distance_metric_bbc_k,
            self.properties.distance_precision,
        ]

    def isReady(self):
        if self.input_sequences is None:
            return False
        if not isinstance(self.input_sequences, SequenceModel):
            return False
        if not self.input_sequences.file_item:
            return False
        if self.decontaminate_mode == DecontaminateMode.DECONT:
            if self.outgroup_sequences is None:
                return False
        if self.decontaminate_mode == DecontaminateMode.DECONT2:
            if self.outgroup_sequences is None:
                return False
            if self.ingroup_sequences is None:
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
            DecontaminateSubtask.Main,
            process.execute,
            work_dir=work_dir,

            decontaminate_mode=self.decontaminate_mode,

            input_sequences=self.input_sequences.as_dict(),
            outgroup_sequences=self.outgroup_sequences.as_dict() if self.outgroup_sequences else None,
            ingroup_sequences=self.ingroup_sequences.as_dict() if self.ingroup_sequences else None,

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
            outgroup_weight=self.outgroup_weight,
            ingroup_weight=self.ingroup_weight,
        )

    def add_input_file(self, path):
        self.busy = True
        self.busy_input = True
        self.exec(DecontaminateSubtask.AddInputFile, get_file_info, path)

    def add_outgroup_file(self, path):
        self.busy = True
        self.busy_outgroup = True
        self.exec(DecontaminateSubtask.AddOutgroupFile, get_file_info, path)

    def add_ingroup_file(self, path):
        self.busy = True
        self.busy_ingroup = True
        self.exec(DecontaminateSubtask.AddIngroupFile, get_file_info, path)

    def add_file_item_from_info(self, info):
        if info.type == FileInfo.Tabfile:
            if len(info.headers) < 2:
                self.notification.emit(Notification.Warn('Not enough columns in tabfile.'))
                return
            index = app.model.items.add_file(InputFileModel.Tabfile(info), focus=False)
            return index.data(ItemModel.ItemRole)
        elif info.type == FileInfo.Fasta:
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
                    SequenceModel: SequenceModel.Tabfile,
                    PartitionModel: PartitionModel.Tabfile,
                },
                InputFileModel.Fasta: {
                    SequenceModel: SequenceModel.Fasta,
                },
            }[type(file_item.object)][model_parent]
        except Exception:
            self.notification.emit(Notification.Warn('Unexpected file type.'))
            return None
        return model_type(file_item, *args, **kwargs)

    def set_input_file_from_file_item(self, file_item):
        self.input_sequences = self.get_model_from_file_item(file_item, SequenceModel)

    def set_outgroup_file_from_file_item(self, file_item):
        self.outgroup_sequences = self.get_model_from_file_item(file_item, SequenceModel)

    def set_ingroup_file_from_file_item(self, file_item):
        self.ingroup_sequences = self.get_model_from_file_item(file_item, SequenceModel)

    def onDone(self, report):
        if report.id == DecontaminateSubtask.Initialize:
            return
        if report.id == DecontaminateSubtask.Main:
            time_taken = human_readable_seconds(report.result.seconds_taken)
            self.notification.emit(Notification.Info(f'{self.name} completed successfully!\nTime taken: {time_taken}.'))
            self.dummy_results = report.result.output_directory
            self.dummy_time = report.result.seconds_taken
            self.busy_main = False
            self.done = True
        if report.id == DecontaminateSubtask.AddInputFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_input_file_from_file_item(file_item)
            self.busy_input = False
        if report.id == DecontaminateSubtask.AddOutgroupFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_outgroup_file_from_file_item(file_item)
            self.busy_outgroup = False
        if report.id == DecontaminateSubtask.AddIngroupFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_ingroup_file_from_file_item(file_item)
            self.busy_ingroup = False
        self.busy = False

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
        self.notification.emit(Notification.Info('Saved files successfully!'))
