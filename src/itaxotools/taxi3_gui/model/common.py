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
from collections import defaultdict
from typing import Callable, List

from itaxotools.common.utility import override

from ..threading import ProgressReport, Worker
from ..types import Notification
from ..utility import Property, PropertyMeta, PropertyRef


class Object(QtCore.QObject, metaclass=PropertyMeta):
    """Interface for backend structures"""
    name = Property(str)

    def __init__(self, name=None):
        super().__init__()
        self.name = name


class Group(Object):
    pass


class Task(Object):
    task_name = 'Task'

    notification = QtCore.Signal(Notification)
    progression = QtCore.Signal(ProgressReport)

    ready = Property(bool)
    busy = Property(bool)

    counters = defaultdict(lambda: itertools.count(1, 1))

    def __init__(self, name=None, init=None):
        super().__init__(name or self._get_next_name())
        self.ready = False
        self.busy = False

        self.worker = Worker(name=self.name, eager=True, init=init)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)
        self.worker.progress.connect(self.onProgress)

        for property in self.readyTriggers():
            property.notify.connect(self.checkIfReady)

    @classmethod
    def _get_next_name(cls):
        return f'{cls.task_name} #{next(cls.counters[cls.task_name])}'

    def __str__(self):
        return f'{self.task_name}({repr(self.name)})'

    def __repr__(self):
        return str(self)

    def onProgress(self, report: ProgressReport):
        self.progression.emit(report)

    def onFail(self, exception: Exception, traceback: str):
        print(str(exception))
        print(traceback)
        self.notification.emit(Notification.Fail(str(exception), traceback))
        self.busy = False

    def onError(self, exitcode: int):
        self.notification.emit(Notification.Fail(f'Process failed with exit code: {exitcode}'))
        self.busy = False

    def onDone(self, results):
        """Overload this to handle results. Must call done()."""
        self.done()

    def done(self):
        """Call this at the bottom of onDone()"""
        self.notification.emit(Notification.Info(f'{self.name} completed successfully!'))
        self.busy = False

    def start(self):
        """Slot for starting the task"""
        self.busy = True
        self.run()

    def stop(self):
        """Slot for interrupting the task"""
        if self.worker is None:
            return
        self.worker.reset()
        self.notification.emit(Notification.Warn('Cancelled by user.'))
        self.busy = False

    def readyTriggers(self) -> List[PropertyRef]:
        """Overload this to set properties as ready triggers"""
        return []

    def checkIfReady(self, *args):
        """Slot to check if ready"""
        self.ready = self.isReady()

    def isReady(self) -> bool:
        """Overload this to check if ready"""
        return False

    def run(self):
        """Called by start(). Overload this with calls to exec()"""
        self.exec(lambda *args: None)

    def exec(self, task: Callable, *args, **kwargs):
        """Call this from run() to execute tasks"""
        self.worker.exec(task, *args, **kwargs)


class Item:
    """Provides a hierarchical structure for Objects"""
    def __init__(self, object: Object, parent=None):
        self.children = list()
        self.parent = parent
        self.object = object

    def add_child(self, object: Object):
        child = Item(object, self)
        self.children.append(child)
        return child

    @property
    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class ItemModel(QtCore.QAbstractItemModel):
    """The main model that holds all Items"""

    addedEntry = QtCore.Signal(QtCore.QModelIndex)
    ItemRole = QtCore.Qt.UserRole

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = Item('')
        self.tasks = self.root.add_child(Group('Tasks'))
        self.sequences = self.root.add_child(Group('Sequences'))

    @property
    def tasks_index(self):
        group = self.tasks
        return self.createIndex(group.row, 0, group)

    @property
    def sequences_index(self):
        group = self.sequences
        return self.createIndex(group.row, 0, group)

    def _add_entry(self, group, child):
        parent = self.createIndex(group.row, 0, group)
        row = len(group.children)
        self.beginInsertRows(parent, row, row)
        group.add_child(child)

        def entryChanged():
            index = self.index(row, 0, parent)
            self.dataChanged.emit(index, index)

        child.properties.name.notify.connect(entryChanged)
        self.endInsertRows()
        index = self.index(row, 0, parent)
        self.addedEntry.emit(index)

    def add_task(self, task):
        self._add_entry(self.tasks, task)

    def add_sequence(self, sequence):
        self._add_entry(self.sequences, sequence)

    def remove_index(self, index):
        parent = index.parent()
        parentItem = parent.internalPointer()
        row = index.row()
        self.beginRemoveRows(parent, row, row)
        parentItem.children.pop(row)
        self.endRemoveRows()

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.root

    @override
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if parent.isValid() and column != 0:
            return QtCore.QModelIndex()

        parentItem = self.getItem(parent)

        if row < 0 or row >= len(parentItem.children):
            return QtCore.QModelIndex()

        childItem = parentItem.children[row]
        return self.createIndex(row, 0, childItem)

    @override
    def parent(self, index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if item.parent is self.root or item.parent is None:
            return QtCore.QModelIndex()
        return self.createIndex(item.parent.row, 0, item.parent)

    @override
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.root.children)

        parentItem = parent.internalPointer()
        return len(parentItem.children)

    @override
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 1

    @override
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return item.object.name
        if role == self.ItemRole:
            return item
        return None

    @override
    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        item = index.internalPointer()
        flags = super().flags(index)
        if item in self.root.children:
            flags = flags & ~ QtCore.Qt.ItemIsEnabled
        return flags
