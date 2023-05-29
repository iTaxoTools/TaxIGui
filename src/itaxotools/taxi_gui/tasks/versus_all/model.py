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
from itaxotools.taxi_gui.model.tasks import TaskModel, SubtaskModel
from itaxotools.taxi_gui.types import FileInfo, Notification
from itaxotools.taxi_gui.utility import human_readable_seconds

from ..common.model import FileInfoSubtaskModel
from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from . import process
from .types import StatisticsGroup


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


class StatisticsGroups(EnumObject):
    enum = StatisticsGroup


class Model(TaskModel):
    task_name = 'Versus All'

    perform_species = Property(bool, False)
    perform_genera = Property(bool, False)

    input_sequences = Property(SequenceModel, None)
    input_species = Property(PartitionModel, None)
    input_genera = Property(PartitionModel, None)

    alignment_mode = Property(AlignmentMode, AlignmentMode.PairwiseAlignment)
    alignment_write_pairs = Property(bool, True)

    distance_linear = Property(bool, True)
    distance_matricial = Property(bool, True)

    distance_percentile = Property(bool, False)
    distance_precision = Property(int | None, 4)
    distance_missing = Property(str, 'NA')
    distance_stats_template = Property(str, '{mean} ({min}-{max})')

    pairwise_scores = Property(PairwiseScores, Instance)
    distance_metrics = Property(DistanceMetrics, Instance)
    statistics_groups = Property(StatisticsGroups, Instance)

    plot_histograms = Property(bool, True)
    plot_binwidth = Property(float, 0.05)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.binder = Binder()

        self.subtask_init = SubtaskModel(self, bind_busy=False)
        self.subtask_sequences = FileInfoSubtaskModel(self)
        self.subtask_species = FileInfoSubtaskModel(self)
        self.subtask_genera = FileInfoSubtaskModel(self)

        self.binder.bind(self.subtask_sequences.done, self.onDoneInfoSequences)
        self.binder.bind(self.subtask_species.done, self.onDoneInfoSpecies)
        self.binder.bind(self.subtask_genera.done, self.onDoneInfoGenera)

        self.subtask_init.start(process.initialize)

    def readyTriggers(self):
        return [
            self.properties.busy_subtask,
            self.properties.input_sequences,
            self.properties.input_species,
            self.properties.input_genera,
            self.properties.perform_species,
            self.properties.perform_genera,
            self.properties.alignment_mode,
            *(property for property in self.pairwise_scores.properties),
            self.distance_metrics.properties.bbc,
            self.distance_metrics.properties.bbc_k,
            self.properties.distance_precision,
        ]

    def isReady(self):
        if self.busy_subtask:
            return False
        if self.input_sequences is None:
            return False
        if not isinstance(self.input_sequences, SequenceModel):
            return False
        if not self.input_sequences.file_item:
            return False
        if not self.input_sequences.is_valid():
            return False
        if self.perform_species:
            if not isinstance(self.input_species, PartitionModel):
                return False
            if not self.input_species.file_item:
                return False
            if not self.input_species.is_valid():
                return False
        if self.perform_genera:
            if not isinstance(self.input_genera, PartitionModel):
                return False
            if not self.input_genera.file_item:
                return False
            if not self.input_genera.is_valid():
                return False
        if self.perform_species and self.perform_genera:
            if self.input_species == self.input_genera:
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

            perform_species=self.perform_species,
            perform_genera=self.perform_genera,

            input_sequences=self.input_sequences.as_dict(),
            input_species=self.input_species.as_dict() if self.input_species else None,
            input_genera=self.input_genera.as_dict() if self.input_genera else None,

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
            distance_stats_template=self.distance_stats_template,

            statistics_all=self.statistics_groups.for_all,
            statistics_species=self.statistics_groups.per_species,
            statistics_genus=self.statistics_groups.per_genus,

            plot_histograms=self.plot_histograms,
            plot_binwidth=self.plot_binwidth or self.properties.plot_binwidth.default,
        )

    def add_sequence_file(self, path):
        self.subtask_sequences.start(path)

    def add_species_file(self, path):
        self.subtask_species.start(path)

    def add_genera_file(self, path):
        self.subtask_genera.start(path)

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
        elif info.type == FileInfo.Spart:
            index = app.model.items.add_file(InputFileModel.Spart(info), focus=False)
            return index.data(ItemModel.ItemRole)
        else:
            self.notification.emit(Notification.Warn('Unknown sequence-file format.'))
            return None

    def get_model_from_file_item(self, file_item, model_parent, *args, **kwargs):
        if file_item is None:
            return None
        try:
            return model_parent.from_input_file(file_item, *args, **kwargs)
        except Exception:
            self.notification.emit(Notification.Warn('Unexpected file type.'))
            return None

    def set_sequence_file_from_file_item(self, file_item):
        if self.input_sequences is not None:
            self.input_sequences.updated.disconnect(self.checkIfReady)
        self.input_sequences = self.get_model_from_file_item(file_item, SequenceModel)
        if self.input_sequences is not None:
            self.input_sequences.updated.connect(self.checkIfReady)
        self.propagate_file_item(file_item)

    def _set_species_file_from_file_item(self, file_item):
        if self.input_species is not None:
            self.input_species.updated.disconnect(self.checkIfReady)
        self.input_species = self.get_model_from_file_item(file_item, PartitionModel, 'species')
        if self.input_species is not None:
            self.input_species.updated.connect(self.checkIfReady)

    def set_species_file_from_file_item(self, file_item):
        try:
            self._set_species_file_from_file_item(file_item)
        except Exception:
            self.notification.emit(Notification.Warn('No partition information found in file.'))
            self.input_species = None
            self.properties.input_species.update()

    def _set_genera_file_from_file_item(self, file_item):
        if self.input_genera is not None:
            self.input_genera.updated.disconnect(self.checkIfReady)
        self.input_genera = self.get_model_from_file_item(file_item, PartitionModel, 'genera')
        if self.input_genera is not None:
            self.input_genera.updated.connect(self.checkIfReady)

    def set_genera_file_from_file_item(self, file_item):
        try:
            self._set_genera_file_from_file_item(file_item)
        except Exception:
            self.notification.emit(Notification.Warn('No partition information found in file.'))
            self.input_genera = None
            self.properties.input_genera.update()

    def propagate_file_item(self, file_item):
        if not file_item:
            return
        if isinstance(file_item.object, InputFileModel.Spart):
            return
        if isinstance(file_item.object, InputFileModel.Tabfile):
            info = file_item.object.info
            if info.header_species is not None or info.header_organism is not None:
                self.perform_species = True
                self._set_species_file_from_file_item(file_item)
            if info.header_genus is not None or info.header_organism is not None:
                self.perform_genera = True
                self._set_genera_file_from_file_item(file_item)
        if isinstance(file_item.object, InputFileModel.Fasta) and file_item.object.info.has_subsets:
            self.perform_species = True
            self.perform_genera = True
            self._set_species_file_from_file_item(file_item)
            self._set_genera_file_from_file_item(file_item)

    def onDone(self, report):
        time_taken = human_readable_seconds(report.result.seconds_taken)
        self.notification.emit(Notification.Info(f'{self.name} completed successfully!\nTime taken: {time_taken}.'))
        self.dummy_results = report.result.output_directory
        self.dummy_time = report.result.seconds_taken
        self.busy = False
        self.done = True

    def onDoneInfoSequences(self, info):
        file_item = self.add_file_item_from_info(info)
        self.set_sequence_file_from_file_item(file_item)

    def onDoneInfoSpecies(self, info):
        file_item = self.add_file_item_from_info(info)
        self.set_species_file_from_file_item(file_item)

    def onDoneInfoGenera(self, info):
        file_item = self.add_file_item_from_info(info)
        self.set_genera_file_from_file_item(file_item)

    def clear(self):
        self.dummy_results = None
        self.dummy_time = None
        self.done = False

    def save(self, destination: Path):
        copytree(self.dummy_results, destination, dirs_exist_ok=True)
        self.notification.emit(Notification.Info('Saved files successfully!'))
