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
from dataclasses import dataclass
from typing import NamedTuple
from enum import Enum, auto
from pathlib import Path

from itaxotools.common.types import Type


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


class FileFormat(Enum):
    Tabfile = auto()
    Fasta = auto()
    Spart = auto()


@dataclass
class InputFile(Type):
    path: Path
    size: int

    def as_dict(self):
        return asdict(self)


@dataclass
class Unknown(InputFile):
    pass


@dataclass
class Fasta(InputFile):
    has_subsets: bool


@dataclass
class Tabfile(InputFile):
    headers: list[str]
    individuals: str = None
    sequences: str = None
    organism: str = None
    species: str = None
    genera: str = None


@dataclass
class Spart(InputFile):
    spartitions: list[str]
    is_matricial: bool
    is_xml: bool


class Entry(NamedTuple):
    label: str
    key: str
    default: int


class PropertyEnum(Enum):
    property_type = lambda: object

    def __init__(self, label, key, default):
        self.label = label
        self.key = key
        self.default = default
        self.type = object

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self._name_}>'


class PairwiseScore(PropertyEnum):
    Match = Entry('Match', 'match_score', 1)
    Mismatch = Entry('Mismatch', 'mismatch_score', -1)
    InternalOpenGap = Entry('Open inner gap', 'internal_open_gap_score', -8)
    InternalExtendGap = Entry('Extend inner gap', 'internal_extend_gap_score', -1)
    EndOpenGap = Entry('Open outer gap', 'end_open_gap_score', -1)
    EndExtendGap = Entry('Extend outer gap', 'end_extend_gap_score', -1)


class DistanceMetric(PropertyEnum):
    property_type = lambda: bool
    Uncorrected = Entry('Uncorrected (p-distance)', 'p', True)
    UncorrectedWithGaps = Entry('Uncorrected with gaps', 'pg', True)
    JukesCantor = Entry('Jukes Cantor (jc)', 'jc', True)
    Kimura2Parameter = Entry('Kimura 2-Parameter (k2p)', 'k2p', True)
    NCD = Entry('Normalized Compression Distance (NCD)', 'ncd', True)
    BBC = Entry('Base-Base Correlation (BBC)', 'bbc', False)


class StatisticsGroup(PropertyEnum):
    property_type = lambda: bool
    All = Entry('For all sequences', 'for_all', True)
    Species = Entry('Per species', 'per_species', True)
    Genus = Entry('Per genus', 'per_genus', True)


class AlignmentMode(Enum):
    NoAlignment = ('Already aligned', 'the sequences will be compared without further alignment')
    PairwiseAlignment = ('Pairwise alignment', 'align each pair of sequences just before calculating distances')
    AlignmentFree = ('Alignment-free', 'calculate pairwise distances using alignment-free metrics')

    def __init__(self, label, description):
        self.label = label
        self.description = description


class ColumnFilter(Enum):
    All = ('*', 'All contents')
    First = ('1', 'First word')

    def __init__(self, abr, text):
        self.abr = abr
        self.text = text
        self.label = f'{text} ({abr})'
