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
from itaxotools.taxi_gui.types import Notification
from itaxotools.taxi_gui.utility import type_convert
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.tasks import ScrollTaskView
from itaxotools.taxi_gui.view.widgets import (
    GLineEdit,
    NoWheelComboBox,
    RadioButtonGroup,
)

from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from ..common.view import (
    AlignmentModeSelector,
    DummyResultsCard,
    PartitionSelector,
    ProgressCard,
    SequenceSelector,
    TitleCard,
)
from .types import StatisticsGroup


class OptionalCategory(Card):
    toggled = QtCore.Signal(bool)

    def __init__(self, text, description, parent=None):
        super().__init__(parent)

        title = QtWidgets.QCheckBox(text)
        title.setStyleSheet("""font-size: 16px;""")
        title.toggled.connect(self.toggled)

        description = QtWidgets.QLabel(description)
        description.setWordWrap(True)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)
        contents.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addSpacing(80)
        self.addLayout(layout)

        self.controls.title = title

    def setChecked(self, checked: bool):
        self.controls.title.setChecked(checked)


class DistanceTemplateComboBox(NoWheelComboBox):
    valueChanged = QtCore.Signal(str)
    invalidTemplate = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.currentIndexChanged.connect(self.handleIndexChanged)
        self.setEditable(True)

        self.addItem("mean (minimum-maximum)", "{mean} ({min}-{max})")
        self.addItem("minimum-maximum (mean)", "{min}-{max} ({mean})")
        self.addItem("minimum-maximum", "{min}-{max}")
        self.addItem("mean", "{mean}")

    def handleIndexChanged(self, index):
        if self.itemData(index) is None:
            self.updateIndexValue(index)
        self.valueChanged.emit(self.itemData(index))
        if self.itemText(index) == self.itemData(index):
            self.invalidTemplate.emit(self.itemText(index))

    def updateIndexValue(self, index):
        text = self.itemText(index)
        data = text
        data = data.replace("minimum", "{min}")
        data = data.replace("maximum", "{max}")
        data = data.replace("mean", "{mean}")
        self.setItemData(index, data)

    def setValue(self, value):
        index = self.findData(value)
        if index >= 0:
            self.setCurrentIndex(index)
            return
        text = value.format(min="minimum", max="maximum", mean="mean")
        self.addItem(text, value)
        self.setCurrentIndex(self.count() - 1)

    def focusOutEvent(self, event):
        index = self.findText(self.currentText())
        if index < 0:
            # Text was edited and does not exist, add new item
            index = self.count()
            self.addItem(self.currentText())
            self.updateIndexValue(index)

        self.setCurrentIndex(index)
        super().focusOutEvent(event)


class DistanceMetricSelector(Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_file_type()
        self.draw_format()

    def draw_main(self):
        label = QtWidgets.QLabel("Distance metrics")
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "Select the types of distances that should be calculated for each pair of sequences:"
        )
        description.setWordWrap(True)

        metrics = QtWidgets.QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(8)

        metric_p = QtWidgets.QCheckBox("Uncorrected (p-distance)")
        metric_pg = QtWidgets.QCheckBox("Uncorrected with gaps")
        metric_jc = QtWidgets.QCheckBox("Jukes Cantor (jc)")
        metric_k2p = QtWidgets.QCheckBox("Kimura 2-Parameter (k2p)")
        metrics.addWidget(metric_p, 0, 0)
        metrics.addWidget(metric_pg, 1, 0)
        metrics.setColumnStretch(0, 2)
        metrics.setColumnMinimumWidth(1, 16)
        metrics.setColumnStretch(1, 0)
        metrics.addWidget(metric_jc, 0, 2)
        metrics.addWidget(metric_k2p, 1, 2)
        metrics.setColumnStretch(2, 2)

        metric_ncd = QtWidgets.QCheckBox("Normalized Compression Distance (NCD)")
        metric_bbc = QtWidgets.QCheckBox("Base-Base Correlation (BBC)")

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

        self.controls.metrics = AttrDict()
        self.controls.metrics.p = metric_p
        self.controls.metrics.pg = metric_pg
        self.controls.metrics.jc = metric_jc
        self.controls.metrics.k2p = metric_k2p
        self.controls.metrics.ncd = metric_ncd
        self.controls.metrics.bbc = metric_bbc

        self.controls.bbc_k = metric_bbc_k_field
        self.controls.bbc_k_label = metric_bbc_k_label

        self.addLayout(layout)

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

        template_label = QtWidgets.QLabel("Summary template:")
        precision_label = QtWidgets.QLabel("Decimal precision:")
        missing_label = QtWidgets.QLabel("Not-Available symbol:")

        layout.addWidget(template_label, 0, 0)
        layout.addWidget(precision_label, 1, 0)
        layout.addWidget(missing_label, 2, 0)

        layout.setColumnMinimumWidth(1, 16)
        layout.setColumnStretch(1, 0)

        template = DistanceTemplateComboBox()
        precision = GLineEdit("4")
        missing = GLineEdit("NA")

        layout.addWidget(template, 0, 2)
        layout.addWidget(precision, 1, 2)
        layout.addWidget(missing, 2, 2)
        layout.setColumnStretch(2, 2)

        layout.setColumnMinimumWidth(3, 16)
        layout.setColumnStretch(3, 0)

        unit_radio = QtWidgets.QRadioButton("Distances from 0.0 to 1.0")
        percent_radio = QtWidgets.QRadioButton("Distances as percentages (%)")

        percentile = RadioButtonGroup()
        percentile.add(unit_radio, False)
        percentile.add(percent_radio, True)

        layout.addWidget(unit_radio, 0, 4)
        layout.addWidget(percent_radio, 1, 4)
        layout.setColumnStretch(4, 2)

        self.addLayout(layout)

        self.controls.template = template
        self.controls.precision = precision
        self.controls.missing = missing
        self.controls.percentile = percentile

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


class StatisticSelector(Card):
    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QLabel("Calculate simple sequence statistics")
        title.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "Includes information about sequence length, N50/L50 and nucleotide distribution."
        )
        description.setWordWrap(True)

        contents = QtWidgets.QHBoxLayout()
        contents.setSpacing(8)

        for group in StatisticsGroup:
            widget = QtWidgets.QCheckBox(group.label)
            contents.addWidget(widget)
            self.controls[group.key] = widget

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(contents)
        layout.setSpacing(8)

        self.addLayout(layout)


class PlotSelector(Card):
    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QCheckBox("Generate histogram plots")
        title.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            "Plot histograms of the distribution of sequence distances across species/genera. "
            "You may customize the width of the bins across the horizontal axis (from 0.0 to 1.0)."
        )
        description.setWordWrap(True)

        label = QtWidgets.QLabel("Bin width:")
        binwidth = GLineEdit("")
        binwidth.setValidator(QtGui.QDoubleValidator())
        binwidth.setPlaceholderText("0.05")

        contents = QtWidgets.QHBoxLayout()
        contents.addWidget(label)
        contents.addWidget(binwidth)
        contents.addStretch(1)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(contents)
        layout.setSpacing(8)

        self.addLayout(layout)

        self.controls.plot = title
        self.controls.binwidth = binwidth


class View(ScrollTaskView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(
            "Versus All",
            "Derive statistics from the distance betweens all pairs of sequences.",
            self,
        )
        self.cards.dummy_results = DummyResultsCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_sequences = SequenceSelector("Input sequences", self)
        self.cards.perform_species = OptionalCategory(
            "Perform species analysis",
            "Calculate various metrics betweens all pairs of species (mean/min/max), "
            "based on the distances between their member specimens.",
            self,
        )
        self.cards.input_species = PartitionSelector(
            "Species partition", "Species", "Individuals", self
        )
        self.cards.perform_genera = OptionalCategory(
            "Perform genus analysis",
            "Calculate various metrics betweens all pairs of genera (mean/min/max), "
            "based on the distances between their member specimens.",
            self,
        )
        self.cards.input_genera = PartitionSelector(
            "Genera partition", "Genera", "Individuals", self
        )
        self.cards.alignment_mode = AlignmentModeSelector(self)
        self.cards.distance_metrics = DistanceMetricSelector(self)
        self.cards.stats_options = StatisticSelector(self)
        self.cards.plot_options = PlotSelector(self)

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
            object.subtask_sequences.properties.busy,
            self.cards.input_sequences.set_busy,
        )
        self.binder.bind(
            object.subtask_species.properties.busy, self.cards.input_species.set_busy
        )
        self.binder.bind(
            object.subtask_genera.properties.busy, self.cards.input_genera.set_busy
        )

        self.binder.bind(
            self.cards.perform_species.toggled, object.properties.perform_species
        )
        self.binder.bind(
            object.properties.perform_species, self.cards.perform_species.setChecked
        )
        self.binder.bind(
            object.properties.perform_species,
            self.cards.input_species.roll_animation.setAnimatedVisible,
        )

        self.binder.bind(
            self.cards.perform_genera.toggled, object.properties.perform_genera
        )
        self.binder.bind(
            object.properties.perform_genera, self.cards.perform_genera.setChecked
        )
        self.binder.bind(
            object.properties.perform_genera,
            self.cards.input_genera.roll_animation.setAnimatedVisible,
        )

        self._bind_input_selector(
            self.cards.input_sequences, object.input_sequences, object.subtask_sequences
        )
        self._bind_input_selector(
            self.cards.input_species, object.input_species, object.subtask_species
        )
        self._bind_input_selector(
            self.cards.input_genera, object.input_genera, object.subtask_genera
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

        for key in (metric.key for metric in DistanceMetric):
            self.binder.bind(
                self.cards.distance_metrics.controls.metrics[key].toggled,
                object.distance_metrics.properties[key],
            )
            self.binder.bind(
                object.distance_metrics.properties[key],
                self.cards.distance_metrics.controls.metrics[key].setChecked,
            )

        self.binder.bind(
            self.cards.distance_metrics.controls.bbc_k.textEditedSafe,
            object.distance_metrics.properties.bbc_k,
            lambda x: type_convert(x, int, None),
        )
        self.binder.bind(
            object.distance_metrics.properties.bbc_k,
            self.cards.distance_metrics.controls.bbc_k.setText,
            lambda x: str(x) if x is not None else "",
        )
        self.binder.bind(
            object.distance_metrics.properties.bbc,
            self.cards.distance_metrics.controls.bbc_k.setEnabled,
        )
        self.binder.bind(
            object.distance_metrics.properties.bbc,
            self.cards.distance_metrics.controls.bbc_k_label.setEnabled,
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
            self.cards.distance_metrics.controls.template.valueChanged,
            object.properties.distance_stats_template,
        )
        self.binder.bind(
            self.cards.distance_metrics.controls.template.invalidTemplate,
            self.handleInvalidTemplate,
        )
        self.binder.bind(
            object.properties.distance_stats_template,
            self.cards.distance_metrics.controls.template.setValue,
        )

        self.binder.bind(
            object.properties.alignment_mode,
            self.cards.distance_metrics.setAlignmentMode,
        )

        for group in StatisticsGroup:
            self.binder.bind(
                self.cards.stats_options.controls[group.key].toggled,
                object.statistics_groups.properties[group.key],
            )
            self.binder.bind(
                object.statistics_groups.properties[group.key],
                self.cards.stats_options.controls[group.key].setChecked,
            )

        self.binder.bind(
            object.properties.plot_histograms,
            self.cards.plot_options.controls.plot.setChecked,
        )
        self.binder.bind(
            object.properties.plot_binwidth,
            self.cards.plot_options.controls.binwidth.setText,
            lambda x: str(x) if x is not None else "",
        )
        self.binder.bind(
            self.cards.plot_options.controls.plot.toggled,
            object.properties.plot_histograms,
        )
        self.binder.bind(
            self.cards.plot_options.controls.binwidth.textEditedSafe,
            object.properties.plot_binwidth,
            lambda x: type_convert(x, float, None),
        )

        self.binder.bind(
            object.properties.dummy_results, self.cards.dummy_results.setPath
        )
        self.binder.bind(
            object.properties.dummy_results,
            self.cards.dummy_results.roll_animation.setAnimatedVisible,
            lambda x: x is not None,
        )

        self.binder.bind(object.properties.editable, self.setEditable)

    def _bind_input_selector(self, card, object, subtask):
        self.binder.bind(card.addInputFile, subtask.start)
        self.binder.bind(card.indexChanged, object.set_index)
        self.binder.bind(object.properties.model, card.set_model)
        self.binder.bind(object.properties.index, card.set_index)
        self.binder.bind(object.properties.object, card.bind_object)

    def setEditable(self, editable: bool):
        for card in self.cards:
            card.setEnabled(editable)
        self.cards.title.setEnabled(True)
        self.cards.dummy_results.setEnabled(True)
        self.cards.progress.setEnabled(True)

    def handleInvalidTemplate(self, text):
        notification = Notification.Warn(
            f"No values included in template: {repr(text)}"
        )
        self.showNotification(notification)

    def save(self):
        path = self.getExistingDirectory("Save All")
        if path:
            self.object.save(path)
