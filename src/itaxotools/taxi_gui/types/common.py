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

from collections import namedtuple
from enum import Enum, auto

from ._type import Type


class ComparisonMode(Type):
    label: str

    def is_valid(self):
        return True


class AlignmentFree(ComparisonMode):
    label = 'Alignment-Free (BBC)'


class AlreadyAligned(ComparisonMode):
    label = 'Already Aligned'


class PairwiseAlignment(ComparisonMode):
    label = 'Pairwise Alignment'

    def __init__(self, config=None):
        self.config = config or PairwiseComparisonConfig()

    def is_valid(self):
        return self.config.is_valid()


class Notification(Type):
    def __init__(self, text: str, info: str = ''):
        self.text = text
        self.info = info


class Info(Notification):
    pass


class Warn(Notification):
    pass


class Fail(Notification):
    pass


class PairwiseComparisonConfig(dict):
    Score = namedtuple('Score', ['label', 'default'])
    scores = {
        'match score': Score('Match Score', 1),
        'mismatch score': Score('Mismatch Score', -1),
        'gap penalty': Score('Gap Penalty', -8),
        'gap extend penalty': Score('Gap Extend Penalty', -1),
        'end gap penalty': Score('End Gap Penalty', -1),
        'end gap extend penalty': Score('End Gap Extend Penalty', -1),
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
    DECONT = 'Single Reference'
    DECONT2 = 'Double Reference'

    def __str__(self):
        return self.value


class FileFormat(Enum):
    Tabfile = auto()
    Fasta = auto()
    Spart = auto()
