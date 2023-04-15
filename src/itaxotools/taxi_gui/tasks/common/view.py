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

from PySide6 import QtCore, QtGui, QtWidgets

from itaxotools.taxi_gui.view.animations import VerticalRollAnimation
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.widgets import (
    GLineEdit, RadioButtonGroup, RichRadioButton)

from .types import AlignmentMode, PairwiseScore


class AlignmentModeSelector(Card):
    resetScores = QtCore.Signal()
    modes = list(AlignmentMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_pairwise_config()

    def draw_main(self):
        label = QtWidgets.QLabel('Sequence alignment')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'You may optionally align sequences before calculating distances.')
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.setSpacing(8)

        group = RadioButtonGroup()
        group.valueChanged.connect(self.handleModeChanged)
        self.controls.mode = group

        radios = QtWidgets.QVBoxLayout()
        radios.setSpacing(8)
        for mode in self.modes:
            button = RichRadioButton(f'{mode.label}:', mode.description, self)
            radios.addWidget(button)
            group.add(button, mode)
        layout.addLayout(radios)
        layout.setContentsMargins(0, 0, 0, 0)

        self.addLayout(layout)

    def draw_pairwise_config(self):
        write_pairs = QtWidgets.QCheckBox('Write file with all aligned sequence pairs')
        self.controls.write_pairs = write_pairs

        self.controls.score_fields = dict()
        scores = QtWidgets.QGridLayout()
        validator = QtGui.QIntValidator()
        for i, score in enumerate(PairwiseScore):
            label = QtWidgets.QLabel(f'{score.label}:')
            field = GLineEdit()
            field.setValidator(validator)
            field.scoreKey = score.key
            scores.addWidget(label, i // 2, (i % 2) * 4)
            scores.addWidget(field, i // 2, (i % 2) * 4 + 2)
            self.controls.score_fields[score.key] = field
        scores.setColumnMinimumWidth(1, 16)
        scores.setColumnMinimumWidth(2, 80)
        scores.setColumnMinimumWidth(5, 16)
        scores.setColumnMinimumWidth(6, 80)
        scores.setColumnStretch(2, 2)
        scores.setColumnStretch(3, 1)
        scores.setColumnStretch(6, 2)
        scores.setContentsMargins(0, 0, 0, 0)
        scores.setSpacing(8)

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('You may configure the pairwise comparison scores below:')
        reset = QtWidgets.QPushButton('Reset to default scores')
        reset.clicked.connect(self.resetScores)
        layout.addWidget(write_pairs)
        layout.addWidget(label)
        layout.addLayout(scores)
        layout.addWidget(reset)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)
        widget.roll = VerticalRollAnimation(widget)

        self.controls.pairwise_config = widget

    def handleToggle(self, checked):
        if not checked:
            return
        for button in self.controls.radio_buttons:
            if button.isChecked():
                self.toggled.emit(button.alignmentMode)

    def handleModeChanged(self, mode):
        self.controls.pairwise_config.roll.setAnimatedVisible(mode == AlignmentMode.PairwiseAlignment)


class CrossAlignmentModeSelector(AlignmentModeSelector):
    modes = [AlignmentMode.PairwiseAlignment, AlignmentMode.AlignmentFree]
