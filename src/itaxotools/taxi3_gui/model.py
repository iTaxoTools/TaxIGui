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

from typing import Callable, Optional
from pathlib import Path
from enum import Enum, auto

import itertools

from itaxotools.common.utility import override


class Property():
    """Convenience declaration of Qt Properties"""
    def __init__(
        self,
        type: type = object,
        fget: Optional[Callable] = None,
        fset: Optional[Callable] = None,
        notify: Optional[Callable] = None,
        constant: bool = False,
    ):
        self.type = type
        self.fget = fget
        self.fset = fset
        self.notify = notify
        self.constant = constant


class _ObjectMeta(type(QtCore.QObject)):
    """Translates class Properties to Qt Properties"""
    def __new__(cls, name, bases, classdict):
        properties = {
            key: classdict[key] for key in classdict
            if isinstance(classdict[key], Property)}
        for key, property in properties.items():
            cls._register(classdict, key, property)
        obj = super().__new__(cls, name, bases, classdict)
        return obj

    def _register(classdict, key, property):
        _key = f'_val_{key}'
        _notify = None
        if property.notify:
            _notify = [x for x in classdict if classdict[x] is property.notify][0]

        def getter(self):
            return getattr(self, _key)

        def setter(self, value):
            old = getattr(self, _key, None)
            setattr(self, _key, value)
            if _notify and old != value:
                getattr(self, _notify).emit(value)

        property.fget = property.fget or getter
        property.fset = property.fset or setter
        classdict[key] = QtCore.Property(
            type=property.type,
            fget=property.fget,
            fset=property.fset,
            notify=property.notify,
            constant=property.constant,
            )

class SequenceListModel(QtCore.QAbstractListModel):

    PathRole = QtCore.Qt.UserRole

    def __init__(self, sequences, parent=None):
        super().__init__(parent)
        self.sequences = sequences

    @override
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        sequence = self.sequences[index.row()]

        if role == QtCore.Qt.DisplayRole:
            return sequence.path.name
        elif role == self.PathRole:
            return sequence.path

    @override
    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            return len(self.sequences)

    def add_sequences(self, sequences):
        existing_paths = [seq.path for seq in self.sequences]
        new_sequences = [seq for seq in sequences if seq.path not in existing_paths]
        position = self.rowCount()
        count = len(new_sequences)
        self.beginInsertRows(QtCore.QModelIndex(), position, position + count)
        self.sequences.extend(new_sequences)
        self.endInsertRows()

    def remove_sequences(self, indexes):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.sequences))
        rows = [index.row() for index in indexes]
        rows.sort(reverse=True)
        for row in rows:
            self.sequences.pop(row)
        self.endRemoveRows()


class Object(QtCore.QObject, metaclass=_ObjectMeta):
    """Interface for backend structures"""
    changed = QtCore.Signal(str)
    name = Property(str, notify=changed)

    def __init__(self, name=None):
        super().__init__()
        self.name = name


class Group(Object):
    pass


class Sequence(Object):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.name = path.stem

    def __str__(self):
        return f'Sequence({repr(self.name)})'

    def __repr__(self):
        return str(self)


class BulkSequences(Object):

    def __init__(self, paths):
        super().__init__()
        self.sequences = [Sequence(path) for path in paths]
        self.sequenceModel = SequenceListModel(self.sequences)
        self.name = 'New Bulk Sequences'

    def __str__(self):
        return f'BulkSequences({repr(self.name)})'

    def __repr__(self):
        return str(self)


class Task(Object):
    pass


class AlignmentType(Enum):
    AlignmentFree = 'Alignment-Free'
    PairwiseAlignment = 'Pairwise Alignment'
    AlreadyAligned = 'Already Aligned'

    def __str__(self):
        return self.value


class Dereplicate(Task):
    changed = QtCore.Signal(str)
    alignment_type = Property(AlignmentType, notify=changed)
    similarity_threshold = Property(float, notify=changed)
    length_threshold = Property(int, notify=changed)

    count = itertools.count(1, 1)

    def __init__(self, name=None, input=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.alignment_type = AlignmentType.AlignmentFree
        self.similarity_threshold = 0.07
        self.length_threshold = 0

    def __str__(self):
        return f'Dereplicate({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Dereplicate #{next(cls.count)}'

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

    def _add_entry(self, group, child):
        parent = self.createIndex(group.row, 0, group)
        row = len(group.children)
        self.beginInsertRows(parent, row, row)
        group.add_child(child)

        def entryChanged():
            index = self.index(row, 0, parent)
            self.dataChanged.emit(index, index)

        child.changed.connect(entryChanged)
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

        if row >= len(parentItem.children):
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
