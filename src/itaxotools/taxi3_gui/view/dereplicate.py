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

from PySide6 import QtCore, QtGui, QtWidgets

from itaxotools.common.utility import AttrDict

from ..types import ComparisonMode, Notification
from .common import (
    Card, ComparisonModeSelector, GLineEdit, GSpinBox, ObjectView,
    SequenceSelector)


class DereplicateView(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = self.draw_title_card()
        self.cards.input = self.draw_input_card()
        self.cards.comparison = self.draw_comparison_card()
        self.cards.similarity = self.draw_similarity_card()
        self.cards.identity = self.draw_identity_card()
        self.cards.length = self.draw_length_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.comparison)
        layout.addWidget(self.cards.similarity)
        layout.addWidget(self.cards.identity)
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
        card = SequenceSelector('Input Sequence(s):', self)
        self.controls.inputItem = card
        return card

    def draw_comparison_card(self):
        card = ComparisonModeSelector(self)
        self.controls.comparisonModeSelector = card
        return card

    def draw_similarity_card(self):
        card = Card(self)

        label = QtWidgets.QLabel('Similarity Threshold')
        label.setStyleSheet("""font-size: 16px;""")

        threshold = GLineEdit()
        threshold.setFixedWidth(80)

        validator = QtGui.QDoubleValidator(threshold)
        locale = QtCore.QLocale.c()
        locale.setNumberOptions(QtCore.QLocale.RejectGroupSeparator)
        validator.setLocale(locale)
        validator.setBottom(0)
        validator.setTop(1)
        validator.setDecimals(2)
        threshold.setValidator(validator)

        description = QtWidgets.QLabel(
            'Sequence pairs for which the computed distance is below '
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

    def draw_identity_card(self):
        card = Card(self)

        label = QtWidgets.QLabel('Identity Threshold')
        label.setStyleSheet("""font-size: 16px;""")

        threshold = GSpinBox()
        threshold.setMinimum(0)
        threshold.setMaximum(100)
        threshold.setSingleStep(1)
        threshold.setSuffix('%')
        threshold.setValue(97)
        threshold.setFixedWidth(80)

        description = QtWidgets.QLabel(
            'Sequence pairs with an identity above '
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

        self.controls.identityThreshold = threshold
        return card

    def draw_length_card(self):
        card = Card(self)

        label = QtWidgets.QLabel('Length Threshold')
        label.setStyleSheet("""font-size: 16px;""")

        threshold = GLineEdit('0')
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
        self.cards.comparison.setEnabled(not busy)
        self.cards.similarity.setEnabled(not busy)
        self.cards.identity.setEnabled(not busy)
        self.cards.length.setEnabled(not busy)

    def handleMode(self, mode):
        self.cards.similarity.setVisible(mode.type is ComparisonMode.AlignmentFree)
        self.cards.identity.setVisible(mode.type is not ComparisonMode.AlignmentFree)

    def setObject(self, object):

        if self.object:
            self.object.notification.disconnect(self.showNotification)
            self.object.progression.disconnect(self.showProgress)
        object.notification.connect(self.showNotification)
        object.progression.connect(self.showProgress)

        self.object = object

        self.unbind_all()

        self.bind(object.properties.name, self.controls.title.setText)
        self.bind(object.properties.ready, self.controls.run.setEnabled)
        self.bind(object.properties.busy, self.handleBusy)

        self.bind(object.properties.similarity_threshold, self.controls.similarityThreshold.setText, lambda x: f'{x:.2f}')
        self.bind(self.controls.similarityThreshold.textEditedSafe, object.properties.similarity_threshold, lambda x: float(x))

        self.bind(object.properties.similarity_threshold, self.controls.identityThreshold.setValue, lambda x: 100 - round(x * 100))
        self.bind(self.controls.identityThreshold.valueChangedSafe, object.properties.similarity_threshold, lambda x: (100 - x) / 100)

        self.bind(object.properties.length_threshold, self.controls.lengthThreshold.setText, lambda x: str(x))
        self.bind(self.controls.lengthThreshold.textEditedSafe, object.properties.length_threshold, lambda x: int(x) if x else 0)

        self.bind(object.properties.comparison_mode, self.controls.comparisonModeSelector.setComparisonMode)
        self.bind(object.properties.comparison_mode, self.handleMode)
        self.bind(self.controls.comparisonModeSelector.toggled, self.resetSimilarityThreshold)
        self.bind(self.controls.comparisonModeSelector.toggled, object.properties.comparison_mode)
        self.bind(self.controls.comparisonModeSelector.edited, object.checkIfReady)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

    def resetSimilarityThreshold(self, mode):
        if mode.type is ComparisonMode.AlignmentFree:
            self.object.similarity_threshold = 0.07
        else:
            self.object.similarity_threshold = 0.03

    def handleRun(self):
        self.object.start()

    def handleCancel(self):
        self.object.stop()

    def showNotification(self, notification):
        icon = {
            Notification.Info: QtWidgets.QMessageBox.Information,
            Notification.Warn: QtWidgets.QMessageBox.Warning,
            Notification.Fail: QtWidgets.QMessageBox.Critical,
        }[notification.type]

        msgBox = QtWidgets.QMessageBox(self.window())
        msgBox.setWindowTitle(self.window().title)
        msgBox.setIcon(icon)
        msgBox.setText(notification.text)
        msgBox.setDetailedText(notification.info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()

    def showProgress(self, report):
        progress = self.controls.progress
        progress.setMaximum(report.maximum)
        progress.setMinimum(report.minimum)
        progress.setValue(report.value)
