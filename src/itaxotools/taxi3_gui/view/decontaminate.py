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
from PySide6 import QtWidgets
from PySide6 import QtGui

from itaxotools.common.utility import AttrDict

from ..model import (
    DecontaminateMode, NotificationType)

from .common import (
    ObjectView, Card,
    SequenceSelector, AlignmentTypeSelector, NoWheelSpinBox)


class DecontaminateModeSelector(Card):

    toggled = QtCore.Signal(DecontaminateMode)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('Decontaminate Mode')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel("For DECONT2 mode, `reference 1` is outgroup (sequences closer to it are contaminates) and `reference 2` is ingroup (sequences closer to it are not contaminates)")
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.setSpacing(8)

        self.radio_buttons = list()
        for mode in DecontaminateMode:
            button = QtWidgets.QRadioButton(str(mode))
            button.decontaminate_mode = mode
            button.toggled.connect(self.handleToggle)
            self.radio_buttons.append(button)
            layout.addWidget(button)

        self.addLayout(layout)

    def handleToggle(self, checked):
        if not checked:
            return
        for button in self.radio_buttons:
            if button.isChecked():
                self.toggled.emit(button.decontaminate_mode)

    def setDecontaminateMode(self, mode):
        for button in self.radio_buttons:
            button.setChecked(button.decontaminate_mode == mode)


class DecontaminateView(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = self.draw_title_card()
        self.cards.input = self.draw_input_card()
        self.cards.mode = self.draw_mode_card()
        self.cards.ref1 = self.draw_ref1_card()
        self.cards.ref2 = self.draw_ref2_card()
        self.cards.distance = self.draw_distance_card()
        self.cards.similarity = self.draw_similarity_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.mode)
        layout.addWidget(self.cards.ref1)
        layout.addWidget(self.cards.ref2)
        layout.addWidget(self.cards.similarity)
        layout.addWidget(self.cards.distance)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_title_card(self):
        card = Card(self)

        title = QtWidgets.QLabel('Decontaminate')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Compare input sequences to one or several reference databases '
            'and remove sequences matching possible contaminants.')
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
        card = SequenceSelector('Input SequenceModel(s):', self)
        self.controls.inputItem = card
        return card

    def draw_mode_card(self):
        card = DecontaminateModeSelector(self)
        self.controls.mode = card
        return card

    def draw_ref1_card(self):
        card = SequenceSelector('Reference 1 (outgroup):', self)
        self.controls.referenceItem1 = card
        return card

    def draw_ref2_card(self):
        card = SequenceSelector('Reference 2 (ingroup):', self)
        self.controls.referenceItem2 = card
        return card

    def draw_distance_card(self):
        card = AlignmentTypeSelector(self)
        self.controls.alignmentTypeSelector = card
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
            'Input sequences for which the uncorrected distance to any member of the reference database is within this threshold ' +
            'will be considered contaminants and will be removed from the decontaminated output file.')
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
        self.cards.mode.setEnabled(not busy)
        self.cards.ref1.setEnabled(not busy)
        self.cards.ref2.setEnabled(not busy)
        self.cards.distance.setEnabled(not busy)
        self.cards.similarity.setEnabled(not busy)

    def handleMode(self, mode):
        self.cards.similarity.setVisible(mode == DecontaminateMode.DECONT)
        self.cards.ref2.setVisible(mode == DecontaminateMode.DECONT2)

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

        self.bind(object.properties.alignment_type, self.controls.alignmentTypeSelector.setAlignmentType)
        self.bind(self.controls.alignmentTypeSelector.toggled, object.properties.alignment_type)

        self.bind(object.properties.mode, self.controls.mode.setDecontaminateMode)
        self.bind(self.controls.mode.toggled, object.properties.mode)
        self.bind(object.properties.mode, self.handleMode)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

        self.bind(object.properties.reference_item_1, self.controls.referenceItem1.setSequenceItem)
        self.bind(self.controls.referenceItem1.sequenceChanged, object.properties.reference_item_1)

        self.bind(object.properties.reference_item_2, self.controls.referenceItem2.setSequenceItem)
        self.bind(self.controls.referenceItem2.sequenceChanged, object.properties.reference_item_2)

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
