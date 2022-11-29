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

from PySide6 import QtCore, QtWidgets, QtGui

from itaxotools.common.utility import AttrDict

from .. import app
from ..types import Notification, AlignmentMode, PairwiseComparisonConfig, StatisticsOption
from .common import Card, NoWheelComboBox, GLineEdit, ObjectView, SequenceSelector as SequenceSelectorLegacy, ComparisonModeSelector as ComparisonModeSelectorLegacy


class RichRadioButton(QtWidgets.QRadioButton):
    def __init__(self, text, desc, parent=None):
        super().__init__(text, parent)
        self.desc = desc
        self.setStyleSheet("""
            RichRadioButton {
                letter-spacing: 1px;
                font-weight: bold;
            }""")
        font = self.font()
        font.setBold(False)
        font.setLetterSpacing(QtGui.QFont.PercentageSpacing, 0)
        self.small_font = font

    def event(self, event):
        if isinstance(event, QtGui.QWheelEvent):
            # Fix scrolling when hovering disabled button
            event.ignore()
            return False
        return super().event(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.setFont(self.small_font)
        width = self.size().width()
        height = self.size().height()
        sofar = super().sizeHint().width()

        rect = QtCore.QRect(sofar, 0, width - sofar, height)
        flags = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        painter.drawText(rect, flags, self.desc)

        painter.end()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        x = event.localPos().x()
        w = self.sizeHint().width()
        if x < w:
            self.setChecked(True)

    def sizeHint(self):
        metrics = QtGui.QFontMetrics(self.small_font)
        extra = metrics.horizontalAdvance(self.desc)
        size = super().sizeHint()
        size += QtCore.QSize(extra, 0)
        return size


class TitleCard(Card):

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QLabel('Versus All')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Derive statistics from the distance betweens all pairs of sequences.')
        description.setWordWrap(True)

        run = QtWidgets.QPushButton('Run')
        remove = QtWidgets.QPushButton('Remove')

        remove.setEnabled(False)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)
        contents.setSpacing(12)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(run)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        self.addLayout(layout)


class InputSelector(Card):

    def __init__(self, text, parent=None, model=app.model.items):
        super().__init__(parent)
        self.draw_main(text)
        self.draw_config()

    def draw_main(self, text):
        label = QtWidgets.QLabel(text + ':')
        label.setStyleSheet("""font-size: 16px;""")

        combo = NoWheelComboBox()

        browse = QtWidgets.QPushButton('Import')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addWidget(combo, 1)
        layout.addWidget(browse)
        self.addLayout(layout)

    def draw_config(self):
        pass


class SequenceSelector(InputSelector):

    def draw_config(self):

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        column = 0

        type_label = QtWidgets.QLabel('File format:')
        size_label = QtWidgets.QLabel('File size:')

        layout.addWidget(type_label, 0, column)
        layout.addWidget(size_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        type_label_value = QtWidgets.QLabel('Tabfile')
        size_label_value = QtWidgets.QLabel('42 MB')

        layout.addWidget(type_label_value, 0, column)
        layout.addWidget(size_label_value, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 32)
        column += 1

        index_label = QtWidgets.QLabel('Indices:')
        sequence_label = QtWidgets.QLabel('Sequences:')

        layout.addWidget(index_label, 0, column)
        layout.addWidget(sequence_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        index_combo = NoWheelComboBox()
        sequence_combo = NoWheelComboBox()

        layout.addWidget(index_combo, 0, column)
        layout.addWidget(sequence_combo, 1, column)
        layout.setColumnStretch(column, 1)
        column += 1

        index_filter = NoWheelComboBox()
        index_filter.setFixedWidth(40)
        sequence_filter = NoWheelComboBox()
        sequence_filter.setFixedWidth(40)

        layout.addWidget(index_filter, 0, column)
        layout.addWidget(sequence_filter, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 16)
        column += 1

        view = QtWidgets.QPushButton('View')

        layout.addWidget(view, 0, column)
        column += 1

        self.addLayout(layout)


class PartitionSelector(InputSelector):

    def draw_config(self):

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        column = 0

        type_label = QtWidgets.QLabel('File format:')
        size_label = QtWidgets.QLabel('File size:')

        layout.addWidget(type_label, 0, column)
        layout.addWidget(size_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        type_label_value = QtWidgets.QLabel('Tabfile')
        size_label_value = QtWidgets.QLabel('42 MB')

        layout.addWidget(type_label_value, 0, column)
        layout.addWidget(size_label_value, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 32)
        column += 1

        index_label = QtWidgets.QLabel('Individuals:')
        sequence_label = QtWidgets.QLabel('Subsets:')

        layout.addWidget(index_label, 0, column)
        layout.addWidget(sequence_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        index_combo = NoWheelComboBox()
        sequence_combo = NoWheelComboBox()

        layout.addWidget(index_combo, 0, column)
        layout.addWidget(sequence_combo, 1, column)
        layout.setColumnStretch(column, 1)
        column += 1

        index_filter = NoWheelComboBox()
        index_filter.setFixedWidth(40)
        sequence_filter = NoWheelComboBox()
        sequence_filter.setFixedWidth(40)

        layout.addWidget(index_filter, 0, column)
        layout.addWidget(sequence_filter, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 16)
        column += 1

        view = QtWidgets.QPushButton('View')

        layout.addWidget(view, 0, column)
        column += 1

        self.addLayout(layout)


class OptionalCategory(Card):

    def __init__(self, text, description, parent=None):
        super().__init__(parent)

        title = QtWidgets.QCheckBox(text)
        title.setStyleSheet("""font-size: 16px;""")

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


class AlignmentModeSelector(Card):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_pairwise_config()
        # self.mode = AlignmentMode()

    def draw_main(self):
        label = QtWidgets.QLabel('Sequence alignment')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'You may optionally align sequences before calculating distances.')
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.setSpacing(16)

        radios = QtWidgets.QVBoxLayout()
        radios.setSpacing(8)
        self.radio_buttons = list()
        for mode in AlignmentMode:
            button = RichRadioButton(f'{mode.label}:', mode.description, self)
            button.alignmentMode = mode
            button.setEnabled(mode != AlignmentMode.MSA)
            # button.toggled.connect(self.handleToggle)
            self.radio_buttons.append(button)
            radios.addWidget(button)

        layout.addLayout(radios)
        self.addLayout(layout)

    def draw_pairwise_config(self):
        self.pairwise_config_panel = QtWidgets.QWidget()

        self.score_fields = dict()
        scores = QtWidgets.QGridLayout()
        validator = QtGui.QIntValidator()
        for i, (key, score) in enumerate(PairwiseComparisonConfig.scores.items()):
            label = QtWidgets.QLabel(f'{score.label}:')
            field = GLineEdit()
            # field.textEdited.connect(self.handleEdit)
            # field.setFixedWidth(80)
            field.setValidator(validator)
            scores.addWidget(label, i // 2, (i % 2) * 4)
            scores.addWidget(field, i // 2, (i % 2) * 4 + 2)
            self.score_fields[key] = field
            field.scoreKey = key
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
        label = QtWidgets.QLabel('You may configure the pairwise comparison scores below.')
        reset = QtWidgets.QPushButton('Reset to default scores')
        # reset.clicked.connect(self.handlePairwiseReset)
        layout.addWidget(label)
        layout.addLayout(scores)
        layout.addWidget(reset)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        self.pairwise_config_panel.setLayout(layout)
        self.addWidget(self.pairwise_config_panel)


class DistanceMetricSelector(Card):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_file_type()
        self.draw_format()

    def draw_main(self):
        label = QtWidgets.QLabel('Distance Metrics')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Select the types of distances that should be calculated for each pair of sequences:')
        description.setWordWrap(True)

        metrics = QtWidgets.QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(8)

        metric_p = QtWidgets.QCheckBox('Uncorrected (p-distance)')
        metric_pg = QtWidgets.QCheckBox('Uncorrected with gaps')
        metric_jc = QtWidgets.QCheckBox('Jukes Cantor (jc)')
        metric_k2p = QtWidgets.QCheckBox('Kimura 2-Parameter (k2p)')
        metrics.addWidget(metric_p, 0, 0)
        metrics.addWidget(metric_pg, 1, 0)
        metrics.setColumnStretch(0, 2)
        metrics.setColumnMinimumWidth(1, 16)
        metrics.setColumnStretch(1, 0)
        metrics.addWidget(metric_jc, 0, 2)
        metrics.addWidget(metric_k2p, 1, 2)
        metrics.setColumnStretch(2, 2)

        description_free = QtWidgets.QLabel(
            'The following alignment-free metrics are also available:')
        description_free.setWordWrap(True)

        metric_ncd = QtWidgets.QCheckBox('Normalized Compression Distance (NCD)')
        metric_bbc = QtWidgets.QCheckBox('Base-Base Correlation (BBC)')

        metric_bbc_k_label = QtWidgets.QLabel('BBC k parameter:')
        metric_bbc_k_field = GLineEdit('10')

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

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addLayout(metrics)
        layout.addWidget(description_free)
        layout.addLayout(metrics_free)
        layout.setSpacing(16)

        self.addLayout(layout)

    def draw_file_type(self):

        linear_check = QtWidgets.QCheckBox('Write distances in linear format (all metrics in the same file)')
        matrix_check = QtWidgets.QCheckBox('Write distances in matricial format (one metric per matrix file)')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(linear_check)
        layout.addWidget(matrix_check)
        layout.setSpacing(8)
        self.addLayout(layout)

    def draw_format(self):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        unit_radio = QtWidgets.QRadioButton('Distances from 0.0 to 1.0')
        percent_radio = QtWidgets.QRadioButton('Distances as percentages (%)')

        layout.addWidget(unit_radio, 0, 0)
        layout.addWidget(percent_radio, 1, 0)
        layout.setColumnStretch(0, 2)

        layout.setColumnMinimumWidth(1, 16)
        layout.setColumnStretch(1, 0)

        precision_label = QtWidgets.QLabel('Decimal precision:')
        missing_label = QtWidgets.QLabel('Not-Available symbol:')

        layout.addWidget(precision_label, 0, 2)
        layout.addWidget(missing_label, 1, 2)

        layout.setColumnMinimumWidth(3, 16)

        precision_field = GLineEdit('4')
        missing_field = GLineEdit('NA')

        layout.addWidget(precision_field, 0, 4)
        layout.addWidget(missing_field, 1, 4)
        layout.setColumnStretch(4, 2)

        self.addLayout(layout)


class StatisticSelector(Card):

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QLabel('Calculate simple sequence statistics')
        title.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Includes information about sequence length, N50/L50 and nucleotide distribution.')
        description.setWordWrap(True)

        contents = QtWidgets.QHBoxLayout()
        contents.setSpacing(8)

        for option in StatisticsOption:
            widget = QtWidgets.QCheckBox(str(option))
            contents.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(contents)
        layout.setSpacing(8)

        self.addLayout(layout)


class VersusAllView(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.input_sequences = SequenceSelector('Input Sequences', self)
        self.cards.perform_species = OptionalCategory(
            'Perform Species Analysis',
            'Calculate various metrics betweens all pairs of species (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_species = PartitionSelector('Species Partition', self)
        self.cards.perform_genera = OptionalCategory(
            'Perform Species Analysis',
            'Calculate various metrics betweens all pairs of genera (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_genera = PartitionSelector('Genera Partition', self)
        self.cards.alignment_mode = AlignmentModeSelector(self)
        self.cards.distance_metrics = DistanceMetricSelector(self)
        self.cards.stats_options = StatisticSelector(self)

        layout = QtWidgets.QVBoxLayout()
        for card in self.cards:
            layout.addWidget(card)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def setObject(self, object):
        self.object = object
        self.unbind_all()


class VersusAllViewLegacy(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = self.draw_title_card()
        self.cards.input = self.draw_input_card()
        self.cards.comparison = self.draw_comparison_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.comparison)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_title_card(self):
        card = Card(self)

        title = QtWidgets.QLabel('Versus All')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Analyze a sequence file using the distances between all samples.')
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
        card = SequenceSelectorLegacy('Input Sequence:', self)
        self.controls.inputItem = card
        return card

    def draw_comparison_card(self):
        card = ComparisonModeSelectorLegacy(self)
        self.controls.comparisonModeSelector = card
        return card

    def handleBusy(self, busy):
        self.controls.cancel.setVisible(busy)
        self.controls.progress.setVisible(busy)
        self.controls.run.setVisible(not busy)
        self.cards.input.setEnabled(not busy)
        self.cards.comparison.setEnabled(not busy)

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

        self.bind(object.properties.comparison_mode, self.controls.comparisonModeSelector.setComparisonMode)
        self.bind(self.controls.comparisonModeSelector.toggled, object.properties.comparison_mode)
        self.bind(self.controls.comparisonModeSelector.edited, object.checkIfReady)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

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
        msgBox.setWindowTitle(app.title)
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
