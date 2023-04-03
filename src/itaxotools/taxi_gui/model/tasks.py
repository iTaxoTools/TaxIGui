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

from PySide6 import QtCore

import itertools
from collections import defaultdict
from typing import Any, Callable, List
from tempfile import TemporaryDirectory
from pathlib import Path

from itaxotools.common.bindings import Property, PropertyRef

from ..threading import ReportProgress, ReportDone, ReportFail, ReportExit, ReportStop, Worker
from ..types import Notification
from .common import Object


class TaskModel(Object):
    task_name = 'Task'

    notification = QtCore.Signal(Notification)
    progression = QtCore.Signal(ReportProgress)

    ready = Property(bool, True)
    busy = Property(bool, False)
    done = Property(bool, False)
    editable = Property(bool, True)

    counters = defaultdict(lambda: itertools.count(1, 1))

    def __init__(self, name=None):
        super().__init__(name or self._get_next_name())

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.worker = Worker(name=self.name, eager=True, log_path=self.temporary_path)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)
        self.worker.stop.connect(self.onStop)
        self.worker.progress.connect(self.onProgress)

        for property in self.readyTriggers():
            property.notify.connect(self.checkIfReady)

        for property in [
            self.properties.busy,
            self.properties.done,
        ]:
            property.notify.connect(self.checkEditable)

    @classmethod
    def _get_next_name(cls):
        # return f'{cls.task_name} #{next(cls.counters[cls.task_name])}'
        return cls.task_name

    def __repr__(self):
        return f'{self.task_name}({repr(self.name)})'

    def onProgress(self, report: ReportProgress):
        self.progression.emit(report)

    def onFail(self, report: ReportFail):
        self.notification.emit(Notification.Fail(str(report.exception), report.traceback))
        self.busy = False

    def onError(self, report: ReportExit):
        self.notification.emit(Notification.Fail(f'Process failed with exit code: {report.exit_code}'))
        self.busy = False

    def onStop(self, report: ReportStop):
        self.notification.emit(Notification.Warn('Cancelled by user.'))
        self.busy = False

    def onDone(self, report: ReportDone):
        """Overload this to handle results"""
        self.notification.emit(Notification.Info(f'{self.name} completed successfully!'))
        self.busy = False
        self.done = True

    def start(self):
        """Slot for starting the task"""
        self.progression.emit(ReportProgress('Preparing for execution...'))
        self.busy = True

    def stop(self):
        """Slot for interrupting the task"""
        if self.worker is None:
            return
        self.worker.reset()

    def save(self):
        """Slot for saving results"""

    def clear(self):
        """Slot for discarding results"""
        self.done = False

    def readyTriggers(self) -> List[PropertyRef]:
        """Overload this to set properties as ready triggers"""
        return []

    def checkIfReady(self, *args):
        """Slot to check if ready"""
        self.ready = self.isReady()

    def isReady(self) -> bool:
        """Overload this to check if ready"""
        return False

    def checkEditable(self):
        self.editable = not (self.busy or self.done)

    def exec(self, id: Any, task: Callable, *args, **kwargs):
        """Call this from start() to execute tasks"""
        self.worker.exec(id, task, *args, **kwargs)
