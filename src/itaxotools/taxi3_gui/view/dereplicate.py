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

from PySide6 import QtGui, QtWidgets

from itaxotools.common.utility import AttrDict

from ..types import NotificationType
from .common import (
    Card, ComparisonModeSelector, NoWheelSpinBox, ObjectView, SequenceSelector)


class DereplicateView(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = self.draw_title_card()
        self.cards.input = self.draw_input_card()
        self.cards.distance = self.draw_distance_card()
        self.cards.similarity = self.draw_similarity_card()
        self.cards.length = self.draw_length_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.distance)
        layout.addWidget(self.cards.similarity)
        layout.addWidget(self.cards.length)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_title_card(self):
        card = Card(self)

        title = QtWidgets.QLabel('Dereplicate')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Remove sequences that are identical or similar to other '
            'sequences in the dataset.')
        description.setWordWrap(True)

        progress = QtWidgets.QProgressBar()
        progress.setMaximum(0)
        progress.setMinimum(0)
        progress.setValue(0)

        run = QtWidgets.QPushButton('Run')
        cancel = QtWidgets.QPushButton('Cancel')
        results = QtWidgets.QPushButton('Results')
        remove = QtWidgets.QPushButton('Remove')

        run.clicked.connect(self.handleRun)
        cancel.clicked.connect(self.handleCancel)

        results.setEnabled(False)
        remove.setEnabled(False)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)
        contents.addWidget(progress)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(run)
        buttons.addWidget(cancel)
        buttons.addWidget(results)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        card.addLayout(layout)

        self.controls.title = title
        self.controls.description = description
        self.controls.progress = progress
        self.controls.run = run
        self.controls.cancel = cancel
        self.controls.results = results
        self.controls.remove = remove
        return card

    def draw_input_card(self):
        card = SequenceSelector('Input SequenceModel:', self)
        self.controls.inputItem = card
        return card

    def draw_distance_card(self):
        card = ComparisonModeSelector(self)
        self.controls.comparisonModeSelector = card
        return card

    def draw_similarity_card(self):
        card = Card(self)

        label = QtWidgets.QLabel('Similarity Threshold (%)')
        label.setStyleSheet("""font-size: 16px;""")

        threshold = NoWheelSpinBox()
        threshold.setMinimum(0)
        threshold.setMaximum(100)
        threshold.setSingleStep(1)
        threshold.setValue(7)
        threshold.setFixedWidth(80)

        description = QtWidgets.QLabel(
            'SequenceModel pairs for which the uncorrected distance is below '
            'this threshold will be considered similar and will be truncated.')
        description.setWordWrap(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(threshold, 0, 1)
        layout.addWidget(description, 1, 0)
        layout.setColumnStretch(0, 1)
        layout.setHorizontalSpacing(20)
        layout.setSpacing(8)
        card.addLayout(layout)

        self.controls.similarityThreshold = threshold
        return card

    def draw_length_card(self):
        card = Card(self)

        label = QtWidgets.QLabel('Length Threshold')
        label.setStyleSheet("""font-size: 16px;""")

        threshold = QtWidgets.QLineEdit('0')
        threshold.setFixedWidth(80)

        validator = QtGui.QIntValidator(threshold)
        validator.setBottom(0)
        threshold.setValidator(validator)

        description = QtWidgets.QLabel('Sequences with length below this threshold will be ignored.')
        description.setWordWrap(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(threshold, 0, 1)
        layout.addWidget(description, 1, 0)
        layout.setColumnStretch(0, 1)
        layout.setHorizontalSpacing(20)
        layout.setSpacing(8)
        card.addLayout(layout)

        self.controls.lengthThreshold = threshold
        return card

    def handleBusy(self, busy):
        self.controls.cancel.setVisible(busy)
        self.controls.progress.setVisible(busy)
        self.controls.run.setVisible(not busy)
        self.cards.input.setEnabled(not busy)
        self.cards.distance.setEnabled(not busy)
        self.cards.similarity.setEnabled(not busy)
        self.cards.length.setEnabled(not busy)

    def setObject(self, object):

        if self.object:
            self.object.notification.disconnect(self.showNotification)
        object.notification.connect(self.showNotification)

        self.object = object

        self.unbind_all()

        self.bind(object.properties.name, self.controls.title.setText)
        self.bind(object.properties.ready, self.controls.run.setEnabled)
        self.bind(object.properties.busy, self.handleBusy)

        self.bind(object.properties.similarity_threshold, self.controls.similarityThreshold.setValue, lambda x: round(x * 100))
        self.bind(self.controls.similarityThreshold.valueChanged, object.properties.similarity_threshold, lambda x: x / 100)

        self.bind(object.properties.length_threshold, self.controls.lengthThreshold.setText, lambda x: str(x))
        self.bind(self.controls.lengthThreshold.textChanged, object.properties.length_threshold, lambda x: int(x))

        self.bind(object.properties.comparison_mode, self.controls.comparisonModeSelector.setComparisonMode)
        self.bind(self.controls.comparisonModeSelector.toggled, object.properties.comparison_mode)
        self.bind(self.controls.comparisonModeSelector.edited, object.updateReady)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

    def handleRun(self):
        self.object.start()

    def handleCancel(self):
        self.object.cancel()

    def showNotification(self, type, text, info):

        icon = {
            NotificationType.Info: QtWidgets.QMessageBox.Information,
            NotificationType.Warn: QtWidgets.QMessageBox.Warning,
            NotificationType.Fail: QtWidgets.QMessageBox.Critical,
        }[type]

        msgBox = QtWidgets.QMessageBox(self.window())
        msgBox.setWindowTitle(self.window().title)
        msgBox.setIcon(icon)
        msgBox.setText(text)
        msgBox.setDetailedText(info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
