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

from itaxotools.common.utility import AttrDict
from itaxotools.taxi_gui.utility import type_convert
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.tasks import ScrollTaskView
from itaxotools.taxi_gui.view.widgets import (
    GLineEdit,
    GSpinBox,
    NoWheelRadioButton,
    RadioButtonGroup,
)

from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from ..common.view import (
    CrossAlignmentModeSelector,
    DummyResultsCard,
    ProgressCard,
    SequenceSelector,
    TitleCard,
)
from .types import DecontaminateMode


class DecontaminateModeSelector(Card):
    toggled = QtCore.Signal(DecontaminateMode)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel("Decontamination Mode")
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "Decontamination is performed either against a single or a double reference. "
            "The first reference defines the outgroup: sequences closest to this are considered contaminants. "
            "If a second reference is given, it defines the ingroup: sequences closer to this are preserved."
        )
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addSpacing(4)
        layout.setSpacing(8)

        texts = {
            DecontaminateMode.DECONT: "(outgroup only)",
            DecontaminateMode.DECONT2: "(outgroup && ingroup)",
        }

        self.radio_buttons = list()
        for mode in DecontaminateMode:
            button = QtWidgets.QRadioButton(f"{str(mode)}\t\t{texts[mode]}")
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

        label = QtWidgets.QLabel("Reference Weights")
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "In order to determine whether a sequence is a contaminant or not, "
            "its distance from the outgroup and ingroup reference databases are compared. "
            "Each distance is first multiplied by a weight. "
            "If the outgroup distance is the shortest of the two, "
            "the sequence is treated as a contaminant."
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
        label_outgroup = QtWidgets.QLabel("Outgroup weight:")
        label_ingroup = QtWidgets.QLabel("Ingroup weight:")
        field_outgroup = GLineEdit("")
        field_ingroup = GLineEdit("")

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
        return self.locale.toString(number, "f", 2)


class DistanceMetricSelector(Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_file_type()
        self.draw_format()

    def draw_main(self):
        label = QtWidgets.QLabel("Distance metric")
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "Select the type of distances that should be calculated for each pair of sequences:"
        )
        description.setWordWrap(True)

        metrics = QtWidgets.QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(8)

        metric_p = NoWheelRadioButton("Uncorrected (p-distance)")
        metric_pg = NoWheelRadioButton("Uncorrected with gaps")
        metric_jc = NoWheelRadioButton("Jukes Cantor (jc)")
        metric_k2p = NoWheelRadioButton("Kimura 2-Parameter (k2p)")
        metrics.addWidget(metric_p, 0, 0)
        metrics.addWidget(metric_pg, 1, 0)
        metrics.setColumnStretch(0, 2)
        metrics.setColumnMinimumWidth(1, 16)
        metrics.setColumnStretch(1, 0)
        metrics.addWidget(metric_jc, 0, 2)
        metrics.addWidget(metric_k2p, 1, 2)
        metrics.setColumnStretch(2, 2)

        metric_ncd = NoWheelRadioButton("Normalized Compression Distance (NCD)")
        metric_bbc = NoWheelRadioButton("Base-Base Correlation (BBC)")

        metric_bbc_k_label = QtWidgets.QLabel("BBC k parameter:")
        metric_bbc_k_field = GLineEdit("10")

        metric_bbc_k = QtWidgets.QHBoxLayout()
        metric_bbc_k.setContentsMargins(0, 0, 0, 0)
        metric_bbc_k.setSpacing(8)
        metric_bbc_k.addWidget(metric_bbc_k_label)
        metric_bbc_k.addSpacing(16)
        metric_bbc_k.addWidget(metric_bbc_k_field, 1)

        metrics_free = QtWidgets.QGridLayout()
        metrics_free.setContentsMargins(0, 0, 0, 0)
        metrics_free.setSpacing(8)

        metrics_free.addWidget(metric_ncd, 0, 0)
        metrics_free.addWidget(metric_bbc, 1, 0)
        metrics_free.setColumnStretch(0, 2)
        metrics_free.setColumnMinimumWidth(1, 16)
        metrics_free.setColumnStretch(1, 0)
        metrics_free.addLayout(metric_bbc_k, 1, 2)
        metrics_free.setColumnStretch(2, 2)

        metrics_all = QtWidgets.QVBoxLayout()
        metrics_all.addLayout(metrics)
        metrics_all.addLayout(metrics_free)
        metrics_all.setContentsMargins(0, 0, 0, 0)
        metrics_all.setSpacing(8)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addLayout(metrics_all)
        layout.setSpacing(16)

        group = RadioButtonGroup()
        group.add(metric_p, DistanceMetric.Uncorrected)
        group.add(metric_pg, DistanceMetric.UncorrectedWithGaps)
        group.add(metric_jc, DistanceMetric.JukesCantor)
        group.add(metric_k2p, DistanceMetric.Kimura2Parameter)
        group.add(metric_ncd, DistanceMetric.NCD)
        group.add(metric_bbc, DistanceMetric.BBC)

        self.controls.group = group
        self.controls.metrics = AttrDict()
        self.controls.metrics.p = metric_p
        self.controls.metrics.pg = metric_pg
        self.controls.metrics.jc = metric_jc
        self.controls.metrics.k2p = metric_k2p
        self.controls.metrics.ncd = metric_ncd
        self.controls.metrics.bbc = metric_bbc

        self.controls.bbc_k = metric_bbc_k_field
        self.controls.bbc_k_label = metric_bbc_k_label

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

    def draw_file_type(self):
        write_linear = QtWidgets.QCheckBox(
            "Write distances in linear format (all metrics in the same file)"
        )
        write_matricial = QtWidgets.QCheckBox(
            "Write distances in matricial format (one metric per matrix file)"
        )

        self.controls.write_linear = write_linear
        self.controls.write_matricial = write_matricial

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(write_linear)
        layout.addWidget(write_matricial)
        layout.setSpacing(8)
        self.addLayout(layout)

    def draw_format(self):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        unit_radio = QtWidgets.QRadioButton("Distances from 0.0 to 1.0")
        percent_radio = QtWidgets.QRadioButton("Distances as percentages (%)")

        percentile = RadioButtonGroup()
        percentile.add(unit_radio, False)
        percentile.add(percent_radio, True)

        layout.addWidget(unit_radio, 0, 0)
        layout.addWidget(percent_radio, 1, 0)
        layout.setColumnStretch(0, 2)

        layout.setColumnMinimumWidth(1, 16)
        layout.setColumnStretch(1, 0)

        precision_label = QtWidgets.QLabel("Decimal precision:")
        missing_label = QtWidgets.QLabel("Not-Available symbol:")

        layout.addWidget(precision_label, 0, 2)
        layout.addWidget(missing_label, 1, 2)

        layout.setColumnMinimumWidth(3, 16)

        precision = GLineEdit("4")
        missing = GLineEdit("NA")

        self.controls.percentile = percentile
        self.controls.precision = precision
        self.controls.missing = missing

        layout.addWidget(precision, 0, 4)
        layout.addWidget(missing, 1, 4)
        layout.setColumnStretch(4, 2)

        self.addLayout(layout)

    def setAlignmentMode(self, mode):
        pairwise = bool(mode == AlignmentMode.PairwiseAlignment)
        self.controls.metrics.ncd.setVisible(not pairwise)
        self.controls.metrics.bbc.setVisible(not pairwise)
        self.controls.bbc_k.setVisible(not pairwise)
        self.controls.bbc_k_label.setVisible(not pairwise)
        free = bool(mode == AlignmentMode.AlignmentFree)
        self.controls.metrics.p.setVisible(not free)
        self.controls.metrics.pg.setVisible(not free)
        self.controls.metrics.jc.setVisible(not free)
        self.controls.metrics.k2p.setVisible(not free)


class SimilarityThresholdCard(Card):
    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel("Similarity Threshold")
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
            "Sequence pairs for which the computed distance is below "
            "this threshold will be considered similar and will be truncated."
        )
        description.setWordWrap(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(threshold, 0, 1)
        layout.addWidget(description, 1, 0)
        layout.setColumnStretch(0, 1)
        layout.setHorizontalSpacing(20)
        layout.setSpacing(8)
        self.addLayout(layout)

        self.controls.similarityThreshold = threshold


class IdentityThresholdCard(Card):
    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel("Identity Threshold")
        label.setStyleSheet("""font-size: 16px;""")

        threshold = GSpinBox()
        threshold.setMinimum(0)
        threshold.setMaximum(100)
        threshold.setSingleStep(1)
        threshold.setSuffix("%")
        threshold.setValue(97)
        threshold.setFixedWidth(80)

        description = QtWidgets.QLabel(
            "Sequence pairs with an identity above "
            "this threshold will be considered similar and will be truncated."
        )
        description.setWordWrap(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(threshold, 0, 1)
        layout.addWidget(description, 1, 0)
        layout.setColumnStretch(0, 1)
        layout.setHorizontalSpacing(20)
        layout.setSpacing(8)
        self.addLayout(layout)

        self.controls.identityThreshold = threshold


class View(ScrollTaskView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(
            "Decontaminate",
            "For each sequence in the input dataset, find the closest match in the reference database.",
            self,
        )
        self.cards.dummy_results = DummyResultsCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_sequences = SequenceSelector("Input sequence", self)
        self.cards.mode_selector = DecontaminateModeSelector(self)
        self.cards.outgroup_sequences = SequenceSelector("Outgroup reference", self)
        self.cards.ingroup_sequences = SequenceSelector("Ingroup reference", self)
        self.cards.weight_selector = ReferenceWeightSelector(self)
        self.cards.alignment_mode = CrossAlignmentModeSelector(self)
        self.cards.distance_metrics = DistanceMetricSelector(self)
        self.cards.similarity = SimilarityThresholdCard(self)
        self.cards.identity = IdentityThresholdCard(self)

        layout = QtWidgets.QVBoxLayout()
        for card in self.cards:
            layout.addWidget(card)
        layout.addStretch(1)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(layout)

    def setObject(self, object):
        self.object = object
        self.binder.unbind_all()

        self.binder.bind(object.notification, self.showNotification)
        self.binder.bind(object.progression, self.cards.progress.showProgress)

        self.binder.bind(object.properties.name, self.cards.title.setTitle)
        self.binder.bind(object.properties.busy, self.cards.title.setBusy)
        self.binder.bind(object.properties.busy, self.cards.progress.setEnabled)
        self.binder.bind(object.properties.busy, self.cards.progress.setVisible)
        self.binder.bind(
            object.subtask_input.properties.busy, self.cards.input_sequences.set_busy
        )
        self.binder.bind(
            object.subtask_outgroup.properties.busy,
            self.cards.outgroup_sequences.set_busy,
        )
        self.binder.bind(
            object.subtask_ingroup.properties.busy,
            self.cards.ingroup_sequences.set_busy,
        )

        self.binder.bind(
            self.cards.mode_selector.toggled, self.object.properties.decontaminate_mode
        )
        self.binder.bind(
            self.object.properties.decontaminate_mode,
            self.cards.mode_selector.setDecontaminateMode,
        )

        self._bind_input_selector(
            self.cards.input_sequences, object.input_sequences, object.subtask_input
        )
        self._bind_input_selector(
            self.cards.outgroup_sequences,
            object.outgroup_sequences,
            object.subtask_outgroup,
        )
        self._bind_input_selector(
            self.cards.ingroup_sequences,
            object.ingroup_sequences,
            object.subtask_ingroup,
        )

        self.binder.bind(
            self.cards.alignment_mode.controls.mode.valueChanged,
            object.properties.alignment_mode,
        )
        self.binder.bind(
            object.properties.alignment_mode,
            self.cards.alignment_mode.controls.mode.setValue,
        )
        self.binder.bind(
            self.cards.alignment_mode.controls.write_pairs.toggled,
            object.properties.alignment_write_pairs,
        )
        self.binder.bind(
            object.properties.alignment_write_pairs,
            self.cards.alignment_mode.controls.write_pairs.setChecked,
        )
        self.binder.bind(
            self.cards.alignment_mode.resetScores, object.pairwise_scores.reset
        )
        for score in PairwiseScore:
            self.binder.bind(
                self.cards.alignment_mode.controls.score_fields[
                    score.key
                ].textEditedSafe,
                object.pairwise_scores.properties[score.key],
                lambda x: type_convert(x, int, None),
            )
            self.binder.bind(
                object.pairwise_scores.properties[score.key],
                self.cards.alignment_mode.controls.score_fields[score.key].setText,
                lambda x: str(x) if x is not None else "",
            )

        self.binder.bind(
            object.properties.distance_metric,
            self.cards.distance_metrics.controls.group.setValue,
        )
        self.binder.bind(
            self.cards.distance_metrics.controls.group.valueChanged,
            object.properties.distance_metric,
        )

        self.binder.bind(
            self.cards.distance_metrics.controls.bbc_k.textEditedSafe,
            object.properties.distance_metric_bbc_k,
            lambda x: type_convert(x, int, None),
        )
        self.binder.bind(
            object.properties.distance_metric_bbc_k,
            self.cards.distance_metrics.controls.bbc_k.setText,
            lambda x: str(x) if x is not None else "",
        )
        self.binder.bind(
            object.properties.distance_metric,
            self.cards.distance_metrics.controls.bbc_k.setEnabled,
            lambda x: x == DistanceMetric.BBC,
        )
        self.binder.bind(
            object.properties.distance_metric,
            self.cards.distance_metrics.controls.bbc_k_label.setEnabled,
            lambda x: x == DistanceMetric.BBC,
        )

        self.binder.bind(
            self.cards.distance_metrics.controls.write_linear.toggled,
            object.properties.distance_linear,
        )
        self.binder.bind(
            object.properties.distance_linear,
            self.cards.distance_metrics.controls.write_linear.setChecked,
        )
        self.binder.bind(
            self.cards.distance_metrics.controls.write_matricial.toggled,
            object.properties.distance_matricial,
        )
        self.binder.bind(
            object.properties.distance_matricial,
            self.cards.distance_metrics.controls.write_matricial.setChecked,
        )

        self.binder.bind(
            self.cards.distance_metrics.controls.percentile.valueChanged,
            object.properties.distance_percentile,
        )
        self.binder.bind(
            object.properties.distance_percentile,
            self.cards.distance_metrics.controls.percentile.setValue,
        )

        self.binder.bind(
            self.cards.distance_metrics.controls.precision.textEditedSafe,
            object.properties.distance_precision,
            lambda x: type_convert(x, int, None),
        )
        self.binder.bind(
            object.properties.distance_precision,
            self.cards.distance_metrics.controls.precision.setText,
            lambda x: str(x) if x is not None else "",
        )
        self.binder.bind(
            self.cards.distance_metrics.controls.missing.textEditedSafe,
            object.properties.distance_missing,
        )
        self.binder.bind(
            object.properties.distance_missing,
            self.cards.distance_metrics.controls.missing.setText,
        )

        self.binder.bind(
            object.properties.alignment_mode,
            self.cards.distance_metrics.setAlignmentMode,
        )

        self.binder.bind(
            object.properties.similarity_threshold,
            self.cards.similarity.controls.similarityThreshold.setText,
            lambda x: f"{x:.2f}",
        )
        self.binder.bind(
            self.cards.similarity.controls.similarityThreshold.textEditedSafe,
            object.properties.similarity_threshold,
            lambda x: type_convert(x, float, None),
        )

        self.binder.bind(
            object.properties.similarity_threshold,
            self.cards.identity.controls.identityThreshold.setValue,
            lambda x: 100 - round(x * 100),
        )
        self.binder.bind(
            self.cards.identity.controls.identityThreshold.valueChangedSafe,
            object.properties.similarity_threshold,
            lambda x: (100 - x) / 100,
        )

        self.binder.bind(
            object.properties.outgroup_weight,
            self.cards.weight_selector.setOutgroupWeight,
        )
        self.binder.bind(
            object.properties.ingroup_weight,
            self.cards.weight_selector.setIngroupWeight,
        )
        self.binder.bind(
            self.cards.weight_selector.edited_outgroup,
            object.properties.outgroup_weight,
        )
        self.binder.bind(
            self.cards.weight_selector.edited_ingroup, object.properties.ingroup_weight
        )

        self.binder.bind(
            object.properties.dummy_results, self.cards.dummy_results.setPath
        )
        self.binder.bind(
            object.properties.dummy_results,
            self.cards.dummy_results.roll_animation.setAnimatedVisible,
            lambda x: x is not None,
        )

        self.binder.bind(object.properties.distance_metric, self.update_visible_cards)
        self.binder.bind(
            object.properties.decontaminate_mode, self.update_visible_cards
        )

        self.binder.bind(object.properties.editable, self.setEditable)

    def _bind_input_selector(self, card, object, subtask):
        self.binder.bind(card.addInputFile, subtask.start)
        self.binder.bind(card.indexChanged, object.set_index)
        self.binder.bind(object.properties.model, card.set_model)
        self.binder.bind(object.properties.index, card.set_index)
        self.binder.bind(object.properties.object, card.bind_object)

    def update_visible_cards(self, *args, **kwargs):
        uncorrected = any(
            (
                self.object.distance_metric == DistanceMetric.Uncorrected,
                self.object.distance_metric == DistanceMetric.UncorrectedWithGaps,
            )
        )
        if self.object.decontaminate_mode == DecontaminateMode.DECONT:
            self.cards.ingroup_sequences.roll_animation.setAnimatedVisible(False)
            self.cards.weight_selector.roll_animation.setAnimatedVisible(False)
            self.cards.identity.roll_animation.setAnimatedVisible(uncorrected)
            self.cards.similarity.roll_animation.setAnimatedVisible(not uncorrected)
        elif self.object.decontaminate_mode == DecontaminateMode.DECONT2:
            self.cards.ingroup_sequences.roll_animation.setAnimatedVisible(True)
            self.cards.weight_selector.roll_animation.setAnimatedVisible(True)
            self.cards.identity.roll_animation.setAnimatedVisible(False)
            self.cards.similarity.roll_animation.setAnimatedVisible(False)

    def setEditable(self, editable: bool):
        for card in self.cards:
            card.setEnabled(editable)
        self.cards.title.setEnabled(True)
        self.cards.dummy_results.setEnabled(True)
        self.cards.progress.setEnabled(True)

    def save(self):
        path = self.getExistingDirectory("Save All")
        if path:
            self.object.save(path)
