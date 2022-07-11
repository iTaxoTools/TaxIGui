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

from PySide6 import QtCore

from tempfile import TemporaryDirectory
from datetime import datetime
from pathlib import Path
from enum import Enum

import itertools

from itaxotools.taxi3.library.datatypes import (
    CompleteData, SequenceData, ValidFilePath,
    TabfileReader, XlsxReader, FastaReader, GenbankReader)
from itaxotools.taxi3.library.task import (
    Decontaminate as _Decontaminate,
    Alignment as _Alignment)
from itaxotools.taxi3.library.datatypes import Metric as _Metric

from itaxotools.common.threading import WorkerThread

from .common import Property, Task, NotificationType, AlignmentType
from .sequence import SequenceModel, SequenceReader
from .bulk_sequences import BulkSequencesModel


class DecontaminateMode(Enum):
    DECONT = 'DECONT'
    DECONT2 = 'DECONT2'

    def __str__(self):
        return self.value


class DecontaminateModel(Task):
    changed = QtCore.Signal(object)
    notification = QtCore.Signal(NotificationType, str, str)
    alignment_type = Property(AlignmentType)
    similarity_threshold = Property(float)
    mode = Property(DecontaminateMode)
    input_item = Property(object)
    reference_item_1 = Property(object)
    reference_item_2 = Property(object)
    ready = Property(bool)
    busy = Property(bool)

    count = itertools.count(1, 1)

    def __init__(self, name=None, model=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.itemModel = model
        self.alignment_type = AlignmentType.AlignmentFree
        self.similarity_threshold = 0.07
        self.mode = DecontaminateMode.DECONT
        self.input_item = None
        self.reference_item_1 = None
        self.reference_item_2 = None
        self.ready = False
        self.busy = False

        self.temporary_directory = TemporaryDirectory(prefix='decontaminate_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.worker = WorkerThread(self.work)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.cancel.connect(self.onCancel)
        self.worker.finished.connect(self.onFinished)

        self.properties.input_item.notify.connect(self.updateReady)
        self.properties.reference_item_1.notify.connect(self.updateReady)
        self.properties.input_item.notify.connect(self.updateReady)

    def __str__(self):
        return f'Decontaminate({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Decontaminate #{next(cls.count)}'

    def isReady(self):
        if self.input_item is None:
            return False
        if self.reference_item_1 is None:
            return False
        if not isinstance(self.reference_item_1.object, SequenceModel):
            return False
        if self.mode == DecontaminateMode.DECONT2:
            if self.reference_item_2 is None:
                return False
            if not isinstance(self.reference_item_2.object, SequenceModel):
                return False
        return True

    def updateReady(self):
        self.ready = self.isReady()

    def start(self):
        self.busy = True
        self.worker.start()

    def work(self):
        object = self.input_item.object
        if isinstance(object, SequenceModel):
            self.workSingle()
        elif isinstance(object, BulkSequencesModel):
            self.workBulk()

    def workSingle(self):
        alignment = {
            AlignmentType.AlignmentFree: _Alignment.AlignmentFree,
            AlignmentType.PairwiseAlignment: _Alignment.Pairwise,
            AlignmentType.AlreadyAligned: _Alignment.AlreadyAligned,
        }[self.alignment_type]

        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.input_item.object.reader]

        input = self.input_item.object.path
        sequence = CompleteData.from_path(ValidFilePath(input), reader)

        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.reference_item_1.object.reader]

        input = self.reference_item_1.object.path
        reference_1 = SequenceData.from_path(ValidFilePath(input), reader)

        if self.mode == DecontaminateMode.DECONT2:
            reader = {
                SequenceReader.TabfileReader: TabfileReader,
                SequenceReader.GenbankReader: GenbankReader,
                SequenceReader.XlsxReader: XlsxReader,
                SequenceReader.FastaReader: FastaReader,
            }[self.reference_item_2.object.reader]

            input = self.reference_item_2.object.path
            reference_2 = SequenceData.from_path(ValidFilePath(input), reader)

        else:
            reference_2 = None

        task = _Decontaminate(warn=print)
        task.similarity = self.similarity_threshold
        task.alignment = alignment
        task._calculate_distances.metrics = [_Metric.Uncorrected]
        task.data = sequence
        task.reference = reference_1
        task.reference2 = reference_2
        task.start()

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        save_path = self.temporary_path / timestamp
        save_path.mkdir()

        contaminates = save_path / f'{input.stem}.{timestamp}.contaminates.tsv'
        decontaminated = save_path / f'{input.stem}.{timestamp}.decontaminated.tsv'
        if self.mode == DecontaminateMode.DECONT:
            summary = save_path / f'{input.stem}.{timestamp}.summary.txt'

        contaminates.unlink(missing_ok=True)
        decontaminated.unlink(missing_ok=True)
        if self.mode == DecontaminateMode.DECONT:
            summary.unlink(missing_ok=True)

        for output in task.result:
            output.contaminates.append_to_file(contaminates)
            output.decontaminated.append_to_file(decontaminated)
            if self.mode == DecontaminateMode.DECONT:
                output.summary.append_to_file(summary)

        if self.itemModel:
            self.itemModel.add_sequence(SequenceModel(contaminates))
            self.itemModel.add_sequence(SequenceModel(decontaminated))
            if self.mode == DecontaminateMode.DECONT:
                self.itemModel.add_sequence(SequenceModel(summary))

    def workBulk(self):
        alignment = {
            AlignmentType.AlignmentFree: _Alignment.AlignmentFree,
            AlignmentType.PairwiseAlignment: _Alignment.Pairwise,
            AlignmentType.AlreadyAligned: _Alignment.AlreadyAligned,
        }[self.alignment_type]

        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.reference_item_1.object.reader]

        input = self.reference_item_1.object.path
        reference_1 = SequenceData.from_path(ValidFilePath(input), reader)

        if self.mode == DecontaminateMode.DECONT2:
            reader = {
                SequenceReader.TabfileReader: TabfileReader,
                SequenceReader.GenbankReader: GenbankReader,
                SequenceReader.XlsxReader: XlsxReader,
                SequenceReader.FastaReader: FastaReader,
            }[self.reference_item_2.object.reader]

            input = self.reference_item_2.object.path
            reference_2 = SequenceData.from_path(ValidFilePath(input), reader)

        else:
            reference_2 = None

        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.input_item.object.reader]

        paths = [sequence.path for sequence in self.input_item.object.sequences]

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        save_path = self.temporary_path / timestamp
        save_path.mkdir()
        contaminates_path = save_path / 'contaminates'
        contaminates_path.mkdir()
        decontaminated_path = save_path / 'decontaminated'
        decontaminated_path.mkdir()
        summary_path = save_path / 'summary'
        summary_path.mkdir()

        for input in paths:

            sequence = CompleteData.from_path(ValidFilePath(input), reader)

            task = _Decontaminate(warn=print)
            task.similarity = self.similarity_threshold
            task.alignment = alignment
            task._calculate_distances.metrics = [_Metric.Uncorrected]
            task.data = sequence
            task.reference = reference_1
            task.reference2 = reference_2
            task.start()

            contaminates = contaminates_path / f'{input.stem}.{timestamp}.contaminates.tsv'
            decontaminated = decontaminated_path / f'{input.stem}.{timestamp}.decontaminated.tsv'
            if self.mode == DecontaminateMode.DECONT:
                summary = summary_path / f'{input.stem}.{timestamp}.summary.txt'

            contaminates.unlink(missing_ok=True)
            decontaminated.unlink(missing_ok=True)
            if self.mode == DecontaminateMode.DECONT:
                summary.unlink(missing_ok=True)

            for output in task.result:
                output.contaminates.append_to_file(contaminates)
                output.decontaminated.append_to_file(decontaminated)
                if self.mode == DecontaminateMode.DECONT:
                    output.summary.append_to_file(summary)

        if self.itemModel:
            contaminates_bulk = list(contaminates_path.iterdir())
            decontaminated_bulk = list(decontaminated_path.iterdir())
            if self.mode == DecontaminateMode.DECONT:
                summary_bulk = list(summary_path.iterdir())
            print(contaminates_bulk)
            print(decontaminated_bulk)
            if self.mode == DecontaminateMode.DECONT:
                print(summary_bulk)
            basename = self.input_item.object.name
            self.itemModel.add_sequence(BulkSequencesModel(contaminates_bulk, name=f'{basename} contaminates'))
            self.itemModel.add_sequence(BulkSequencesModel(decontaminated_bulk, name=f'{basename} decontaminated'))
            if self.mode == DecontaminateMode.DECONT:
                self.itemModel.add_sequence(BulkSequencesModel(summary_bulk, name=f'{basename} summary'))

    def cancel(self):
        self.worker.terminate()

    def onDone(self, result):
        self.notification.emit(NotificationType.Info, f'{self.name} completed successfully!', '')

    def onFail(self, exception, traceback):
        print(str(exception))
        print(traceback)
        self.notification.emit(NotificationType.Fail, str(exception), traceback)

    def onCancel(self, exception):
        self.notification.emit(NotificationType.Warn, 'Cancelled by user.', '')

    def onFinished(self):
        self.busy = False
