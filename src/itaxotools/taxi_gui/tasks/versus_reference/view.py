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

from PySide6 import QtWidgets

from itaxotools.common.utility import AttrDict
from itaxotools.taxi_gui.utility import type_convert
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.tasks import ScrollTaskView
from itaxotools.taxi_gui.view.widgets import GLineEdit, RadioButtonGroup

from ..common.types import AlignmentMode, DistanceMetric, PairwiseScore
from ..common.view import (
    CrossAlignmentModeSelector,
    DummyResultsCard,
    ProgressCard,
    SequenceSelector,
    TitleCard,
)


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


class View(ScrollTaskView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(
            "Versus Reference",
            "For each sequence in the input dataset, find the closest match in the reference database.",
            self,
        )
        self.cards.dummy_results = DummyResultsCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_data = SequenceSelector("Input data", self)
        self.cards.input_reference = SequenceSelector("Reference", self)
        self.cards.alignment_mode = CrossAlignmentModeSelector(self)
        self.cards.distance_metrics = DistanceMetricSelector(self)

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
            object.subtask_data.properties.busy, self.cards.input_data.set_busy
        )
        self.binder.bind(
            object.subtask_reference.properties.busy,
            self.cards.input_reference.set_busy,
        )

        self._bind_input_selector(
            self.cards.input_data, object.input_data, object.subtask_data
        )
        self._bind_input_selector(
            self.cards.input_reference, object.input_reference, object.subtask_reference
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
            object.properties.alignment_mode,
            self.cards.distance_metrics.setAlignmentMode,
        )

        self.binder.bind(
            object.properties.dummy_results, self.cards.dummy_results.setPath
        )
        self.binder.bind(
            object.properties.dummy_results,
            self.cards.dummy_results.setVisible,
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

    def save(self):
        path = self.getExistingDirectory("Save All")
        if path:
            self.object.save(path)
