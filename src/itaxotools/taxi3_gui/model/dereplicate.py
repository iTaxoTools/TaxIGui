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

from ..threading import Worker
from ..tasks import dereplicate
from ..types import AlignmentType

from .common import Property, Task, NotificationType
from .sequence import SequenceModel
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

        self.worker = Worker(eager=True, init=dereplicate.initialize)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)

        self.temporary_directory = TemporaryDirectory(prefix='dereplicate_')
        self.temporary_path = Path(self.temporary_directory.name)

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

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        input = self.input_item.object
        if isinstance(input, SequenceModel):
            input_paths = [input.path]
        elif isinstance(input, BulkSequencesModel):
            input_paths = [sequence.path for sequence in input.sequences]

        self.worker.exec(
            dereplicate.dereplicate, work_dir,
            input_paths, input.reader,
            self.alignment_type,
            self.similarity_threshold,
            self.length_threshold or None,
        )

    def cancel(self):
        if self.worker is None:
            return
        self.worker.reset()
        self.notification.emit(NotificationType.Warn, 'Cancelled by user.', '')
        self.onFinished()

    def onDone(self, results):
        dereplicated_bulk = list()
        excluded_bulk = list()
        for input, result in results.items():
            dereplicated_bulk.append(result.dereplicated)
            excluded_bulk.append(result.excluded)

        if len(results) == 1:
            app.model.items.add_sequence(SequenceModel(result.dereplicated))
            app.model.items.add_sequence(SequenceModel(result.excluded))
        else:
            basename = self.input_item.object.name
            app.model.items.add_sequence(BulkSequencesModel(dereplicated_bulk, name=f'{basename} dereplicated'))
            app.model.items.add_sequence(BulkSequencesModel(excluded_bulk, name=f'{basename} excluded'))

        self.notification.emit(NotificationType.Info, f'{self.name} completed successfully!', '')
        self.onFinished()

    def onFail(self, exception, traceback):
        print(str(exception))
        print(traceback)
        self.notification.emit(NotificationType.Fail, str(exception), traceback)
        self.onFinished()

    def onError(self, exitcode):
        self.notification.emit(NotificationType.Fail, f'Process failed with exit code: {exitcode}', '')
        self.onFinished()

    def onFinished(self):
        self.busy = False
