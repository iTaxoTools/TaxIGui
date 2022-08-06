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

from ..types import ComparisonMode, DecontaminateMode, Notification
from .common import (
    Card, ComparisonModeSelector, GLineEdit, GSpinBox, ObjectView,
    SequenceSelector)


class DecontaminateModeSelector(Card):

    toggled = QtCore.Signal(DecontaminateMode)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('Decontamination Mode')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Decontamination is performed either against a single or a double reference. '
            'The first reference defines the outgroup: sequences closest to this are considered contaminants. '
            'If a second reference is given, it defines the ingroup: sequences closer to this are preserved.'
        )
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addSpacing(4)
        layout.setSpacing(8)

        texts = {
            DecontaminateMode.DECONT: '(outgroup only)',
            DecontaminateMode.DECONT2: '(outgroup && ingroup)',
        }

        self.radio_buttons = list()
        for mode in DecontaminateMode:
            button = QtWidgets.QRadioButton(f'{str(mode)}\t\t{texts[mode]}')
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


class ReferenceWeightSelector(Card):

    edited_outgroup = QtCore.Signal(float)
    edited_ingroup = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('Reference Weights')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'In order to determine whether a sequence is a contaminant or not, '
            'its distance from the outgroup and ingroup reference databases are compared. '
            'Each distance is first multiplied by a weight. '
            'If the outgroup distance is the shortest of the two, '
            'the sequence is treated as a contaminant.'
        )
        description.setWordWrap(True)

        fields = self.draw_fields()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addLayout(fields)
        layout.setSpacing(8)

        self.addLayout(layout)

    def draw_fields(self):
        label_outgroup = QtWidgets.QLabel('Outgroup weight:')
        label_ingroup = QtWidgets.QLabel('Ingroup weight:')
        field_outgroup = GLineEdit('')
        field_ingroup = GLineEdit('')

        field_outgroup.setFixedWidth(80)
        field_ingroup.setFixedWidth(80)

        field_outgroup.textEditedSafe.connect(self.handleOutgroupEdit)
        field_ingroup.textEditedSafe.connect(self.handleIngroupEdit)

        validator = QtGui.QDoubleValidator(self)
        locale = QtCore.QLocale.c()
        locale.setNumberOptions(QtCore.QLocale.RejectGroupSeparator)
        validator.setLocale(locale)
        validator.setBottom(0)
        validator.setDecimals(2)
        field_outgroup.setValidator(validator)
        field_ingroup.setValidator(validator)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(label_outgroup, 0, 0)
        layout.addWidget(label_ingroup, 1, 0)
        layout.addWidget(field_outgroup, 0, 1)
        layout.addWidget(field_ingroup, 1, 1)
        layout.setColumnStretch(2, 1)

        self.outgroup = field_outgroup
        self.ingroup = field_ingroup
        self.locale = locale
        return layout

    def handleOutgroupEdit(self, text):
        weight = self.toFloat(text)[0]
        self.edited_outgroup.emit(weight)

    def handleIngroupEdit(self, text):
        weight = self.toFloat(text)[0]
        self.edited_ingroup.emit(weight)

    def setOutgroupWeight(self, weight):
        self.outgroup.setText(self.toString(weight))

    def setIngroupWeight(self, weight):
        self.ingroup.setText(self.toString(weight))

    def toFloat(self, text):
        return self.locale.toFloat(text)

    def toString(self, number):
        return self.locale.toString(number, 'f', 2)


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
        self.cards.outgroup = self.draw_outgroup_card()
        self.cards.ingroup = self.draw_ingroup_card()
        self.cards.comparison = self.draw_comparison_card()
        self.cards.similarity = self.draw_similarity_card()
        self.cards.identity = self.draw_identity_card()
        self.cards.weights = self.draw_weights_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.mode)
        layout.addWidget(self.cards.outgroup)
        layout.addWidget(self.cards.ingroup)
        layout.addWidget(self.cards.similarity)
        layout.addWidget(self.cards.identity)
        layout.addWidget(self.cards.weights)
        layout.addWidget(self.cards.comparison)
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
        card = SequenceSelector('Input Sequence(s):', self)
        self.controls.inputItem = card
        return card

    def draw_mode_card(self):
        card = DecontaminateModeSelector(self)
        self.controls.mode = card
        return card

    def draw_outgroup_card(self):
        card = SequenceSelector('Outgroup Reference:', self)
        self.controls.outgroupItem = card
        return card

    def draw_ingroup_card(self):
        card = SequenceSelector('Ingroup Reference:', self)
        self.controls.ingroupItem = card
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
            'Input sequences for which the calculated distance to any member of the reference database is below this threshold '
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
            'Input sequences for which the identity to any member of the reference database is above this threshold '
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

        self.controls.identityThreshold = threshold
        return card

    def draw_weights_card(self):
        card = ReferenceWeightSelector(self)
        self.controls.weightSelector = card
        return card

    def handleBusy(self, busy):
        self.controls.cancel.setVisible(busy)
        self.controls.progress.setVisible(busy)
        self.controls.run.setVisible(not busy)
        self.cards.input.setEnabled(not busy)
        self.cards.mode.setEnabled(not busy)
        self.cards.outgroup.setEnabled(not busy)
        self.cards.ingroup.setEnabled(not busy)
        self.cards.comparison.setEnabled(not busy)
        self.cards.similarity.setEnabled(not busy)
        self.cards.identity.setEnabled(not busy)
        self.cards.weights.setEnabled(not busy)

    def handleMode(self, *args):
        single_reference = bool(self.object.mode == DecontaminateMode.DECONT)
        similarity_over_identity = bool(self.object.comparison_mode.type is ComparisonMode.AlignmentFree)
        self.cards.similarity.setVisible(single_reference and similarity_over_identity)
        self.cards.identity.setVisible(single_reference and not similarity_over_identity)
        self.cards.ingroup.setVisible(not single_reference)
        self.cards.weights.setVisible(not single_reference)

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

        self.bind(object.properties.comparison_mode, self.controls.comparisonModeSelector.setComparisonMode)
        self.bind(object.properties.comparison_mode, self.handleMode)
        self.bind(self.controls.comparisonModeSelector.toggled, self.resetSimilarityThreshold)
        self.bind(self.controls.comparisonModeSelector.toggled, object.properties.comparison_mode)
        self.bind(self.controls.comparisonModeSelector.edited, object.checkIfReady)

        self.bind(object.properties.outgroup_weight, self.controls.weightSelector.setOutgroupWeight)
        self.bind(object.properties.ingroup_weight, self.controls.weightSelector.setIngroupWeight)
        self.bind(self.controls.weightSelector.edited_outgroup, object.properties.outgroup_weight)
        self.bind(self.controls.weightSelector.edited_ingroup, object.properties.ingroup_weight)

        self.bind(object.properties.mode, self.controls.mode.setDecontaminateMode)
        self.bind(self.controls.mode.toggled, object.properties.mode)
        self.bind(object.properties.mode, self.handleMode)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

        self.bind(object.properties.outgroup_item, self.controls.outgroupItem.setSequenceItem)
        self.bind(self.controls.outgroupItem.sequenceChanged, object.properties.outgroup_item)

        self.bind(object.properties.ingroup_item, self.controls.ingroupItem.setSequenceItem)
        self.bind(self.controls.ingroupItem.sequenceChanged, object.properties.ingroup_item)

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
