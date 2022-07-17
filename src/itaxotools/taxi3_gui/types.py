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

from collections import namedtuple
from enum import Enum, auto


class TypeMeta(type):
    _inheritors = dict()

    def __new__(cls, name, bases, attrs):
        obj = super().__new__(cls, name, bases, attrs)
        cls._inheritors[obj] = dict()
        for base in bases:
            if issubclass(base, Type):
                cls._inheritors[base][name] = obj
        return obj

    def __dir__(self):
        return super().__dir__() + [x for x in self._inheritors[self].keys()]

    def __getattr__(self, attr):
        if attr in self._inheritors[self]:
            return self._inheritors[self][attr]
        raise AttributeError(f'{repr(self.__name__)} has no subtype {repr(attr)}')

    def __iter__(self):
        return iter(self._inheritors[self].values())


class Type(metaclass=TypeMeta):
    """All subclasses are added as class attributes"""

    @property
    def type(self):
        return type(self)


class ComparisonMode(Type):
    label: str


class AlignmentFree(ComparisonMode):
    label = 'Alignment-Free'


class AlreadyAligned(ComparisonMode):
    label = 'Already Aligned'


class PairwiseAlignment(ComparisonMode):
    label = 'Pairwise Alignment'

    def __init__(self, config=None):
        self.config = config or PairwiseComparisonConfig()


class PairwiseComparisonConfig(dict):
    Score = namedtuple('Score', ['label', 'default'])
    scores = {
        'gap penalty': Score('Gap Penalty', -8),
        'gap extend penalty': Score('Gap Extend Penalty', -1),
        'end gap penalty': Score('End Gap Penalty', -1),
        'end gap extend penalty': Score('End Gap Extend Penalty', -1),
        'match score': Score('Match Score', 1),
        'mismatch score': Score('Mismatch Score', -1),
    }

    def __init__(self):
        for key, score in self.scores.items():
            self[key] = score.default

    @classmethod
    def label(cls, key):
        return cls.scores[key].label

    def is_valid(self):
        return all(isinstance(x, int) for x in self.values())


class SequenceReader(Enum):
    TabfileReader = 'Tab-separated'
    GenbankReader = 'Genbank (flat)'
    XlsxReader = 'Excel (xlsx)'
    FastaReader = 'Fasta'

    def __str__(self):
        return self.value


class DecontaminateMode(Enum):
    DECONT = 'DECONT'
    DECONT2 = 'DECONT2'

    def __str__(self):
        return self.value


class NotificationType(Enum):
    Info = auto()
    Warn = auto()
    Fail = auto()
