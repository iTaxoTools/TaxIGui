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

import itertools
from datetime import datetime
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory

from .. import app
from ..tasks import decontaminate
from ..threading import Worker
from ..types import AlignmentType
from .bulk_sequences import BulkSequencesModel
from .common import NotificationType, Property, Task
from .sequence import SequenceModel


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

    def __init__(self, name=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.alignment_type = AlignmentType.AlignmentFree
        self.similarity_threshold = 0.07
        self.mode = DecontaminateMode.DECONT
        self.input_item = None
        self.reference_item_1 = None
        self.reference_item_2 = None
        self.ready = False
        self.busy = False

        self.worker = Worker(eager=True, init=decontaminate.initialize)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)

        self.temporary_directory = TemporaryDirectory(prefix='decontaminate_')
        self.temporary_path = Path(self.temporary_directory.name)

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

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        input = self.input_item.object
        if isinstance(input, SequenceModel):
            input_paths = [input.path]
        elif isinstance(input, BulkSequencesModel):
            input_paths = [sequence.path for sequence in input.sequences]

        if self.mode == DecontaminateMode.DECONT:

            reference = self.reference_item_1.object

            self.worker.exec(
                decontaminate.decontaminate, work_dir,
                input_paths, input.reader,
                reference.path, reference.reader,
                self.alignment_type,
                self.similarity_threshold,
            )

        elif self.mode == DecontaminateMode.DECONT2:

            reference_outgroup = self.reference_item_1.object
            reference_ingroup = self.reference_item_2.object

            self.worker.exec(
                decontaminate.decontaminate2, work_dir,
                input_paths, input.reader,
                reference_outgroup.path, reference_outgroup.reader,
                reference_ingroup.path, reference_ingroup.reader,
                self.alignment_type,
            )

    def cancel(self):
        if self.worker is None:
            return
        self.worker.reset()
        self.notification.emit(NotificationType.Warn, 'Cancelled by user.', '')
        self.onFinished()

    def onDone(self, results):
        decontaminated_bulk = list()
        contaminants_bulk = list()
        summary_bulk = list()
        for input, result in results.items():
            decontaminated_bulk.append(result.decontaminated)
            contaminants_bulk.append(result.contaminants)
            if isinstance(results, decontaminate.DecontaminateResults):
                summary_bulk.append(result.summary)

        if len(results) == 1:
            app.model.items.add_sequence(SequenceModel(result.decontaminated))
            app.model.items.add_sequence(SequenceModel(result.contaminants))
            if isinstance(results, decontaminate.DecontaminateResults):
                app.model.items.add_sequence(SequenceModel(result.summary))
        else:
            basename = self.input_item.object.name
            app.model.items.add_sequence(BulkSequencesModel(decontaminated_bulk, name=f'{basename} decontaminated'))
            app.model.items.add_sequence(BulkSequencesModel(contaminants_bulk, name=f'{basename} contaminants'))
            if isinstance(results, decontaminate.DecontaminateResults):
                app.model.items.add_sequence(BulkSequencesModel(summary_bulk, name=f'{basename} summary'))

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
