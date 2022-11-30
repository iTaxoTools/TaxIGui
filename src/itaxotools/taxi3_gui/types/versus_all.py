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

from enum import Enum
from typing import NamedTuple

from ._type import Type


class Score(NamedTuple):
    label: str
    key: str
    default: int


class PairwiseScore(Enum):
    Match = Score('Match', 'match_score', 1)
    Mismatch = Score('Mismatch', 'mismatch_score', -1)
    InternalOpenGap = Score('Open inner gap', 'internal_open_gap_score', -8)
    InternalExtendGap = Score('Extend inner gap', 'internal_extend_gap_score', -1)
    EndOpenGap = Score('Open outer gap', 'end_open_gap_score', -1)
    EndExtendGap = Score('Extend outer gap', 'end_extend_gap_score', -1)

    def __init__(self, label, key, default):
        self.label = label
        self.key = key
        self.default = default
        self.type = int


class AlignmentMode(Type):
    label: str

    def is_valid(self):
        return True


class NoAlignment(AlignmentMode):
    label = 'No alignment'
    description = 'for already aligned sequences or alignment-free metrics'


class PairwiseAlignment(AlignmentMode):
    label = 'Pairwise Alignment'
    description = 'align each pair of sequences just before calculating distances'

    def __init__(self, config=None):
        self.config = config or PairwiseComparisonConfig()

    def is_valid(self):
        return self.config.is_valid()


class MSA(AlignmentMode):
    label = 'Multiple Sequence Alignment'
    description = 'uses MAFFT to align all sequences in advance'


class StatisticsOption(Enum):
    All = 'For all sequences'
    Species = 'Per species'
    Genera = 'Per genus'

    def __str__(self):
        return self.value
