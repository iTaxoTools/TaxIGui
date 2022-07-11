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

import itertools

from itaxotools.taxi3.library.datatypes import CompleteData, ValidFilePath, TabfileReader, XlsxReader, FastaReader, GenbankReader
from itaxotools.taxi3.library.task import Dereplicate as _Dereplicate, Alignment as _Alignment
from itaxotools.taxi3.library.datatypes import Metric as _Metric

from itaxotools.common.threading import WorkerThread

from .common import Property, Task, NotificationType, AlignmentType
from .sequence import SequenceModel, SequenceReader
from .bulk_sequences import BulkSequencesModel

from .. import app


class DereplicateModel(Task):
    notification = QtCore.Signal(NotificationType, str, str)
    alignment_type = Property(AlignmentType)
    similarity_threshold = Property(float)
    length_threshold = Property(int)
    input_item = Property(object)
    ready = Property(bool)
    busy = Property(bool)

    count = itertools.count(1, 1)

    def __init__(self, name=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.alignment_type = AlignmentType.AlignmentFree
        self.similarity_threshold = 0.07
        self.length_threshold = 0
        self.input_item = None
        self.ready = True
        self.busy = False

        self.temporary_directory = TemporaryDirectory(prefix='dereplicate_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.worker = WorkerThread(self.work)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.cancel.connect(self.onCancel)
        self.worker.finished.connect(self.onFinished)

        self.properties.input_item.notify.connect(self.checkReady)

    def __str__(self):
        return f'Dereplicate({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Dereplicate #{next(cls.count)}'

    def checkReady(self, value):
        self.ready = bool(value is not None)

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
        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.input_item.object.reader]

        alignment = {
            AlignmentType.AlignmentFree: _Alignment.AlignmentFree,
            AlignmentType.PairwiseAlignment: _Alignment.Pairwise,
            AlignmentType.AlreadyAligned: _Alignment.AlreadyAligned,
        }[self.alignment_type]

        input = self.input_item.object.path
        sequence = CompleteData.from_path(ValidFilePath(input), reader)

        task = _Dereplicate(warn=print)
        task.similarity = self.similarity_threshold
        task.length_threshold = self.length_threshold or None
        task._calculate_distances.alignment = alignment
        task._calculate_distances.metrics = [_Metric.Uncorrected]
        task.data = sequence
        task.start()

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        save_path = self.temporary_path / timestamp
        save_path.mkdir()

        excluded = save_path / f'{input.stem}.{timestamp}.excluded.tsv'
        dereplicated = save_path / f'{input.stem}.{timestamp}.dereplicated.tsv'

        excluded.unlink(missing_ok=True)
        dereplicated.unlink(missing_ok=True)

        for output in task.result:
            output.excluded.append_to_file(excluded)
            output.included.append_to_file(dereplicated)

        app.model.items.add_sequence(SequenceModel(excluded))
        app.model.items.add_sequence(SequenceModel(dereplicated))

    def workBulk(self):
        reader = {
            SequenceReader.TabfileReader: TabfileReader,
            SequenceReader.GenbankReader: GenbankReader,
            SequenceReader.XlsxReader: XlsxReader,
            SequenceReader.FastaReader: FastaReader,
        }[self.input_item.object.reader]

        alignment = {
            AlignmentType.AlignmentFree: _Alignment.AlignmentFree,
            AlignmentType.PairwiseAlignment: _Alignment.Pairwise,
            AlignmentType.AlreadyAligned: _Alignment.AlreadyAligned,
        }[self.alignment_type]

        paths = [sequence.path for sequence in self.input_item.object.sequences]

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        save_path = self.temporary_path / timestamp
        save_path.mkdir()
        excluded_path = save_path / 'excluded'
        excluded_path.mkdir()
        dereplicated_path = save_path / 'dereplicated'
        dereplicated_path.mkdir()

        for input in paths:

            sequence = CompleteData.from_path(ValidFilePath(input), reader)

            task = _Dereplicate(warn=print)
            task.similarity = self.similarity_threshold
            task.length_threshold = self.length_threshold or None
            task._calculate_distances.alignment = alignment
            task._calculate_distances.metrics = [_Metric.Uncorrected]
            task.data = sequence
            task.start()

            excluded = excluded_path / f'{input.stem}.{timestamp}.excluded.tsv'
            dereplicated = dereplicated_path / f'{input.stem}.{timestamp}.dereplicated.tsv'

            excluded.unlink(missing_ok=True)
            dereplicated.unlink(missing_ok=True)

            for output in task.result:
                output.excluded.append_to_file(excluded)
                output.included.append_to_file(dereplicated)

        excluded_bulk = list(excluded_path.iterdir())
        dereplicated_bulk = list(dereplicated_path.iterdir())
        print(excluded_bulk)
        print(dereplicated_bulk)
        basename = self.input_item.object.name
        app.model.items.add_sequence(BulkSequencesModel(excluded_bulk, name=f'{basename} excluded'))
        app.model.items.add_sequence(BulkSequencesModel(dereplicated_bulk, name=f'{basename} dereplicated'))

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
