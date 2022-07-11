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

from itaxotools.common.utility import override

from .common import Object, Property, SequenceReader
from .sequence import SequenceModel


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


class BulkSequencesModel(Object):
    reader = Property(SequenceReader)
    count = itertools.count(1, 1)

    def __init__(self, paths, name=None, reader=SequenceReader.TabfileReader):
        super().__init__()
        self.name = name or self.get_next_name()
        self.sequences = [SequenceModel(path) for path in paths]
        self.model = SequenceListModel(self.sequences)
        self.reader = reader
        self.properties.reader.notify.connect(self.update_members)

    def __str__(self):
        return f'BulkSequences({repr(self.name)})'

    def __repr__(self):
        return str(self)

    @classmethod
    def get_next_name(cls):
        return f'Bulk Sequences #{next(cls.count)}'

    def update_members(self, value):
        self._val_reader = value
        for sequence in self.sequences:
            sequence.reader = value
