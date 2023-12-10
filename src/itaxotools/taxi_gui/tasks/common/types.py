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

from enum import Enum

from itaxotools.taxi_gui.types import Entry, PropertyEnum


class AlignmentMode(Enum):
    NoAlignment = (
        "Already aligned",
        "the sequences will be compared without further alignment",
    )
    PairwiseAlignment = (
        "Pairwise alignment",
        "align each pair of sequences just before calculating distances",
    )
    AlignmentFree = (
        "Alignment-free",
        "calculate pairwise distances using alignment-free metrics",
    )

    def __init__(self, label, description):
        self.label = label
        self.description = description


class PairwiseScore(PropertyEnum):
    Match = Entry("Match", "match_score", 1)
    Mismatch = Entry("Mismatch", "mismatch_score", -1)
    InternalOpenGap = Entry("Open inner gap", "internal_open_gap_score", -8)
    InternalExtendGap = Entry("Extend inner gap", "internal_extend_gap_score", -1)
    EndOpenGap = Entry("Open outer gap", "end_open_gap_score", -1)
    EndExtendGap = Entry("Extend outer gap", "end_extend_gap_score", -1)


class DistanceMetric(PropertyEnum):
    Uncorrected = Entry("Uncorrected (p-distance)", "p", True)
    UncorrectedWithGaps = Entry("Uncorrected with gaps", "pg", True)
    JukesCantor = Entry("Jukes Cantor (jc)", "jc", True)
    Kimura2Parameter = Entry("Kimura 2-Parameter (k2p)", "k2p", True)
    NCD = Entry("Normalized Compression Distance (NCD)", "ncd", True)
    BBC = Entry("Base-Base Correlation (BBC)", "bbc", False)
