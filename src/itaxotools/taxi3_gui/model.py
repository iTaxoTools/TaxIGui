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
from tempfile import TemporaryDirectory
from datetime import datetime
from pathlib import Path
from enum import Enum, auto

import itertools

from itaxotools.taxi3.library.datatypes import CompleteData, SequenceData, ValidFilePath, TabfileReader, XlsxReader, FastaReader, GenbankReader
from itaxotools.taxi3.library.task import Dereplicate as _Dereplicate, Decontaminate as _Decontaminate, Alignment as _Alignment
from itaxotools.taxi3.library.datatypes import Metric as _Metric

from itaxotools.common.utility import override
from itaxotools.common.threading import WorkerThread


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
            return str(sequence.path)
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
    changed = QtCore.Signal(object)
    name = Property(str, notify=changed)

    def __init__(self, name=None):
        super().__init__()
        self.name = name


class Group(Object):
    pass


class SequenceReader(Enum):
    TabfileReader = 'Tab-separated'
    GenbankReader = 'Genbank (flat)'
    XlsxReader = 'Excel (xlsx)'
    FastaReader = 'Fasta'

    def __str__(self):
        return self.value


class Sequence(Object):
    changed = QtCore.Signal(object)
    name = Property(str, notify=changed)
    path = Property(Path, notify=changed)
    reader = Property(SequenceReader, notify=changed)

    def __init__(self, path, reader=SequenceReader.TabfileReader):
        super().__init__()
        self.path = path
        self.name = path.stem
        self.reader = reader

    def __str__(self):
        return f'Sequence({repr(self.name)})'

    def __repr__(self):
        return str(self)


class BulkSequences(Object):
    changed = QtCore.Signal(object)
    name = Property(str, notify=changed)

    count = itertools.count(1, 1)

    def __init__(self, paths, name=None, reader=SequenceReader.TabfileReader):
        super().__init__()
        self.name = name or self.get_next_name()
        self.sequences = [Sequence(path) for path in paths]
        self.model = SequenceListModel(self.sequences)
        self.reader = reader

    def __str__(self):
        return f'BulkSequences({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Bulk Sequences #{next(cls.count)}'

    def set_reader(self, value):
        self._val_reader = value
        for sequence in self.sequences:
            sequence.reader = value

    reader = Property(SequenceReader, fset=set_reader, notify=changed)


class Task(Object):
    pass


class AlignmentType(Enum):
    AlignmentFree = 'Alignment-Free'
    PairwiseAlignment = 'Pairwise Alignment'
    AlreadyAligned = 'Already Aligned'

    def __str__(self):
        return self.value


class NotificationType(Enum):
    Info = auto()
    Warn = auto()
    Fail = auto()


class Dereplicate(Task):
    changed = QtCore.Signal(object)
    notification = QtCore.Signal(NotificationType, str, str)
    alignment_type = Property(AlignmentType, notify=changed)
    similarity_threshold = Property(float, notify=changed)
    length_threshold = Property(int, notify=changed)
    input_item = Property(object, notify=changed)
    busy = Property(bool, notify=changed)

    count = itertools.count(1, 1)

    def __init__(self, name=None, model=None):
        super().__init__()
        self.name = name or self.get_next_name()
        self.itemModel = model
        self.alignment_type = AlignmentType.AlignmentFree
        self.similarity_threshold = 0.07
        self.length_threshold = 0
        self.input_item = None
        self.busy = False

        self.temporary_directory = TemporaryDirectory(prefix='dereplicate_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.worker = WorkerThread(self.work)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.cancel.connect(self.onCancel)
        self.worker.finished.connect(self.onFinished)

    def __str__(self):
        return f'Dereplicate({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Dereplicate #{next(cls.count)}'

    @QtCore.Property(object, notify=changed)
    def ready(self):
        return self.input_item is not None

    def start(self):
        self.busy = True
        self.worker.start()

    def work(self):
        object = self.input_item.object
        if isinstance(object, Sequence):
            self.workSingle()
        elif isinstance(object, BulkSequences):
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

        if self.itemModel:
            self.itemModel.add_sequence(Sequence(excluded))
            self.itemModel.add_sequence(Sequence(dereplicated))

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

        if self.itemModel:
            excluded_bulk = list(excluded_path.iterdir())
            dereplicated_bulk = list(dereplicated_path.iterdir())
            print(excluded_bulk)
            print(dereplicated_bulk)
            basename = self.input_item.object.name
            self.itemModel.add_sequence(BulkSequences(excluded_bulk, name=f'{basename} excluded'))
            self.itemModel.add_sequence(BulkSequences(dereplicated_bulk, name=f'{basename} dereplicated'))

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


class DecontaminateMode(Enum):
    DECONT = 'DECONT'
    DECONT2 = 'DECONT2'

    def __str__(self):
        return self.value


class Decontaminate(Task):
    changed = QtCore.Signal(object)
    notification = QtCore.Signal(NotificationType, str, str)
    alignment_type = Property(AlignmentType, notify=changed)
    similarity_threshold = Property(float, notify=changed)
    mode = Property(DecontaminateMode, notify=changed)
    input_item = Property(object, notify=changed)
    reference_item_1 = Property(object, notify=changed)
    reference_item_2 = Property(object, notify=changed)
    busy = Property(bool, notify=changed)

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
        self.busy = False

        self.temporary_directory = TemporaryDirectory(prefix='decontaminate_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.worker = WorkerThread(self.work)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.cancel.connect(self.onCancel)
        self.worker.finished.connect(self.onFinished)

    def __str__(self):
        return f'Decontaminate({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Decontaminate #{next(cls.count)}'

    @QtCore.Property(object, notify=changed)
    def ready(self):
        if self.input_item is None:
            return False
        if self.reference_item_1 is None:
            return False
        if not isinstance(self.reference_item_1.object, Sequence):
            return False
        if self.mode == DecontaminateMode.DECONT2:
            if self.reference_item_2 is None:
                return False
            if not isinstance(self.reference_item_2.object, Sequence):
                return False
        return True

    def start(self):
        self.busy = True
        self.worker.start()

    def work(self):
        object = self.input_item.object
        if isinstance(object, Sequence):
            self.workSingle()
        elif isinstance(object, BulkSequences):
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
            self.itemModel.add_sequence(Sequence(contaminates))
            self.itemModel.add_sequence(Sequence(decontaminated))
            if self.mode == DecontaminateMode.DECONT:
                self.itemModel.add_sequence(Sequence(summary))

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
            self.itemModel.add_sequence(BulkSequences(contaminates_bulk, name=f'{basename} contaminates'))
            self.itemModel.add_sequence(BulkSequences(decontaminated_bulk, name=f'{basename} decontaminated'))
            if self.mode == DecontaminateMode.DECONT:
                self.itemModel.add_sequence(BulkSequences(summary_bulk, name=f'{basename} summary'))

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
