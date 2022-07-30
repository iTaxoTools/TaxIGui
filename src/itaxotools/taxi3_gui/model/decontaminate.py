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
from pathlib import Path
from tempfile import TemporaryDirectory

from .. import app
from ..tasks import decontaminate
from ..threading import Worker
from ..types import ComparisonMode, DecontaminateMode, NotificationType
from .bulk_sequences import BulkSequencesModel
from .common import Property, Task
from .sequence import SequenceModel


class DecontaminateModel(Task):
    changed = QtCore.Signal(object)
    notification = QtCore.Signal(NotificationType, str, str)
    comparison_mode = Property(ComparisonMode)
    similarity_threshold = Property(float)
    outgroup_weight = Property(float)
    ingroup_weight = Property(float)
    mode = Property(DecontaminateMode)
    input_item = Property(object)
    outgroup_item = Property(object)
    ingroup_item = Property(object)
    ready = Property(bool)
    busy = Property(bool)

    count = itertools.count(1, 1)

    def __init__(self, name=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.comparison_mode = ComparisonMode.AlignmentFree()
        self.similarity_threshold = 0.07
        self.outgroup_weight = 1.00
        self.ingroup_weight = 1.00
        self.mode = DecontaminateMode.DECONT
        self.input_item = None
        self.outgroup_item = None
        self.ingroup_item = None
        self.ready = False
        self.busy = False

        self.worker = Worker(name=self.name, eager=True, init=decontaminate.initialize)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)

        self.temporary_directory = TemporaryDirectory(prefix='decontaminate_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.properties.mode.notify.connect(self.updateReady)
        self.properties.input_item.notify.connect(self.updateReady)
        self.properties.outgroup_item.notify.connect(self.updateReady)
        self.properties.ingroup_item.notify.connect(self.updateReady)

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
        if self.outgroup_item is None:
            return False
        if not isinstance(self.outgroup_item.object, SequenceModel):
            return False
        if self.mode == DecontaminateMode.DECONT2:
            if self.ingroup_item is None:
                return False
            if not isinstance(self.ingroup_item.object, SequenceModel):
                return False
        if self.comparison_mode.type is ComparisonMode.PairwiseAlignment:
            if not self.comparison_mode.config.is_valid():
                return False
        return True

    def updateReady(self, *args):
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

            reference = self.outgroup_item.object

            self.worker.exec(
                decontaminate.decontaminate, work_dir,
                input_paths, input.reader,
                reference.path, reference.reader,
                self.comparison_mode,
                self.similarity_threshold,
            )

        elif self.mode == DecontaminateMode.DECONT2:

            reference_outgroup = self.outgroup_item.object
            reference_ingroup = self.ingroup_item.object
            outgroup_weight = self.outgroup_weight / self.ingroup_weight

            self.worker.exec(
                decontaminate.decontaminate2, work_dir,
                input_paths, input.reader,
                reference_outgroup.path, reference_outgroup.reader,
                reference_ingroup.path, reference_ingroup.reader,
                outgroup_weight,
                self.comparison_mode,
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
            summary_bulk.append(result.summary)

        if len(results) == 1:
            app.model.items.add_sequence(SequenceModel(result.decontaminated))
            app.model.items.add_sequence(SequenceModel(result.contaminants))
            app.model.items.add_sequence(SequenceModel(result.summary))
        else:
            basename = self.input_item.object.name
            app.model.items.add_sequence(BulkSequencesModel(decontaminated_bulk, name=f'{basename} decontaminated'))
            app.model.items.add_sequence(BulkSequencesModel(contaminants_bulk, name=f'{basename} contaminants'))
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
