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

from itaxotools.common.bindings import EnumObject, Instance, Property

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.model.common import ItemModel
from itaxotools.taxi_gui.model.input_file import InputFileModel
from itaxotools.taxi_gui.model.partition import PartitionModel
from itaxotools.taxi_gui.model.sequence import SequenceModel
from itaxotools.taxi_gui.model.tasks import TaskModel
from itaxotools.taxi_gui.process.common import get_file_info
from itaxotools.taxi_gui.types import (
    DistanceMetric, InputFile, Notification, StatisticsGroup)
from itaxotools.taxi_gui.utility import human_readable_seconds

from ..common.types import AlignmentMode, PairwiseScore
from . import process
from .types import VersusAllSubtask


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

    pairwise_scores = Property(PairwiseScores, Instance)
    distance_metrics = Property(DistanceMetrics, Instance)
    statistics_groups = Property(StatisticsGroups, Instance)

    plot_histograms = Property(bool, True)
    plot_binwidth = Property(float, 0.05)

    busy_main = Property(bool, False)
    busy_sequence = Property(bool, False)
    busy_species = Property(bool, False)
    busy_genera = Property(bool, False)

    dummy_results = Property(Path, None)
    dummy_time = Property(float, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.exec(VersusAllSubtask.Initialize, process.initialize)

    def readyTriggers(self):
        return [
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
        if self.input_sequences is None:
            return False
        if not isinstance(self.input_sequences, SequenceModel):
            return False
        if not self.input_sequences.file_item:
            return False
        if self.perform_species:
            if not isinstance(self.input_species, PartitionModel):
                return False
            if not self.input_species.file_item:
                return False
        if self.perform_genera:
            if not isinstance(self.input_genera, PartitionModel):
                return False
            if not self.input_genera.file_item:
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
            VersusAllSubtask.Main,
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

            statistics_all=self.statistics_groups.for_all,
            statistics_species=self.statistics_groups.per_species,
            statistics_genus=self.statistics_groups.per_genus,

            plot_histograms=self.plot_histograms,
            plot_binwidth=self.plot_binwidth or self.properties.plot_binwidth.default,
        )

    def add_sequence_file(self, path):
        self.busy = True
        self.busy_sequence = True
        self.exec(VersusAllSubtask.AddSequenceFile, get_file_info, path)

    def add_species_file(self, path):
        self.busy = True
        self.busy_species = True
        self.exec(VersusAllSubtask.AddSpeciesFile, get_file_info, path)

    def add_genera_file(self, path):
        self.busy = True
        self.busy_genera = True
        self.exec(VersusAllSubtask.AddGeneraFile, get_file_info, path)

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
        elif info.type == InputFile.Spart:
            index = app.model.items.add_file(InputFileModel.Spart(info), focus=False)
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
                    PartitionModel: PartitionModel.Fasta,
                },
                InputFileModel.Spart: {
                    PartitionModel: PartitionModel.Spart,
                },
            }[type(file_item.object)][model_parent]
        except Exception:
            self.notification.emit(Notification.Warn('Unexpected file type.'))
            return None
        model = model_type(file_item, *args, **kwargs)
        if model_type == SequenceModel.Fasta:
            model.parse_organism = model.has_subsets
        return model

    def set_sequence_file_from_file_item(self, file_item):
        self.input_sequences = self.get_model_from_file_item(file_item, SequenceModel)
        self.propagate_file_item(file_item)

    def set_species_file_from_file_item(self, file_item):
        try:
            self.input_species = self.get_model_from_file_item(file_item, PartitionModel, 'species')
        except Exception:
            self.notification.emit(Notification.Warn('No partition information found in file.'))
            self.input_species = None
            self.properties.input_species.update()

    def set_genera_file_from_file_item(self, file_item):
        try:
            self.input_genera = self.get_model_from_file_item(file_item, PartitionModel, 'genera')
        except Exception:
            self.notification.emit(Notification.Warn('No partition information found in file.'))
            self.properties.input_genera.update()

    def propagate_file_item(self, file_item):
        if not file_item:
            return
        if isinstance(file_item.object, InputFileModel.Spart):
            return
        if isinstance(file_item.object, InputFileModel.Tabfile):
            info = file_item.object.info
            if info.species is not None or info.organism is not None:
                self.perform_species = True
                self.input_species = self.get_model_from_file_item(file_item, PartitionModel, 'species')
            if info.genera is not None or info.organism is not None:
                self.perform_genera = True
                self.input_genera = self.get_model_from_file_item(file_item, PartitionModel, 'genera')
        if isinstance(file_item.object, InputFileModel.Fasta) and file_item.object.info.has_subsets:
            self.perform_species = True
            self.perform_genera = True
            self.input_species = self.get_model_from_file_item(file_item, PartitionModel, 'species')
            self.input_genera = self.get_model_from_file_item(file_item, PartitionModel, 'genera')

    def onDone(self, report):
        if report.id == VersusAllSubtask.Initialize:
            return
        if report.id == VersusAllSubtask.Main:
            time_taken = human_readable_seconds(report.result.seconds_taken)
            self.notification.emit(Notification.Info(f'{self.name} completed successfully!\nTime taken: {time_taken}.'))
            self.dummy_results = report.result.output_directory
            self.dummy_time = report.result.seconds_taken
            self.busy_main = False
            self.done = True
        if report.id == VersusAllSubtask.AddSequenceFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_sequence_file_from_file_item(file_item)
            self.busy_sequence = False
        if report.id == VersusAllSubtask.AddSpeciesFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_species_file_from_file_item(file_item)
            self.busy_species = False
        if report.id == VersusAllSubtask.AddGeneraFile:
            file_item = self.add_file_item_from_info(report.result)
            self.set_genera_file_from_file_item(file_item)
            self.busy_genera = False
        self.busy = False

    def onStop(self, report):
        super().onStop(report)
        self.busy_main = False
        self.busy_sequence = False
        self.busy_species = False
        self.busy_genera = False

    def onFail(self, report):
        super().onFail(report)
        self.busy_main = False
        self.busy_sequence = False
        self.busy_species = False
        self.busy_genera = False

    def onError(self, report):
        super().onError(report)
        self.busy_main = False
        self.busy_sequence = False
        self.busy_species = False
        self.busy_genera = False

    def clear(self):
        self.dummy_results = None
        self.dummy_time = None
        self.done = False

    def save(self, destination: Path):
        copytree(self.dummy_results, destination, dirs_exist_ok=True)
        self.notification.emit(Notification.Info('Saved files successfully!'))
