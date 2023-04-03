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

from pathlib import Path

from itaxotools.common.utility import AttrDict, override, Guard
from itaxotools.common.bindings import Binder

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.utility import type_convert, human_readable_size
from itaxotools.taxi_gui.types import ColumnFilter, AlignmentMode, AlignmentMode, PairwiseScore, DistanceMetric
from itaxotools.taxi_gui.types import ComparisonMode
from itaxotools.taxi_gui.view.widgets import GLineEdit, GSpinBox, NoWheelComboBox, NoWheelRadioButton, MinimumStackedWidget, RadioButtonGroup, RichRadioButton
from itaxotools.taxi_gui.view.cards import Card, CardCustom
from itaxotools.taxi_gui.view.tasks import TaskView
from itaxotools.taxi_gui.view.animations import VerticalRollAnimation
from itaxotools.taxi_gui.model.common import Item, ItemModel
from itaxotools.taxi_gui.model.sequence import SequenceModel
from .types import DecontaminateMode


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


class ItemProxyModel(QtCore.QAbstractProxyModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = None
        self.unselected = '---'

    def sourceDataChanged(self, topLeft, bottomRight):
        self.dataChanged.emit(self.mapFromSource(topLeft), self.mapFromSource(bottomRight))

    @override
    def setSourceModel(self, model, root):
        super().setSourceModel(model)
        self.root = root
        model.dataChanged.connect(self.sourceDataChanged)

    @override
    def mapFromSource(self, sourceIndex):
        item = sourceIndex.internalPointer()
        if not item or item.parent != self.root:
            return QtCore.QModelIndex()
        return self.createIndex(item.row + 1, 0, item)

    @override
    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return QtCore.QModelIndex()
        if proxyIndex.row() == 0:
            return QtCore.QModelIndex()
        item = proxyIndex.internalPointer()
        source = self.sourceModel()
        return source.createIndex(item.row, 0, item)

    @override
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if parent.isValid() or column != 0:
            return QtCore.QModelIndex()
        if row < 0 or row > len(self.root.children):
            return QtCore.QModelIndex()
        if row == 0:
            return self.createIndex(0, 0)
        return self.createIndex(row, 0, self.root.children[row - 1])

    @override
    def parent(self, index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        return QtCore.QModelIndex()

    @override
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.root.children) + 1

    @override
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 1

    @override
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None
        if index.row() == 0:
            if role == QtCore.Qt.DisplayRole:
                return self.unselected
            return None
        return super().data(index, role)

    @override
    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.row() == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return super().flags(index)


class ColumnFilterDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if not index.isValid():
            return

        self.initStyleOption(option, index)
        option.text = index.data(ColumnFilterCombobox.LabelRole)
        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter)

    def sizeHint(self, option, index):
        height = self.parent().sizeHint().height()
        return QtCore.QSize(100, height)


class ColumnFilterCombobox(NoWheelComboBox):
    valueChanged = QtCore.Signal(ColumnFilter)

    DataRole = QtCore.Qt.UserRole
    LabelRole = QtCore.Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = QtGui.QStandardItemModel()
        for filter in ColumnFilter:
            item = QtGui.QStandardItem()
            item.setData(filter.abr, QtCore.Qt.DisplayRole)
            item.setData(filter.label, self.LabelRole)
            item.setData(filter, self.DataRole)
            model.appendRow(item)
        self.setModel(model)

        delegate = ColumnFilterDelegate(self)
        self.setItemDelegate(delegate)

        self.view().setMinimumWidth(100)

        self.currentIndexChanged.connect(self.handleIndexChanged)

    def handleIndexChanged(self, index):
        self.valueChanged.emit(self.itemData(index, self.DataRole))

    def setValue(self, value):
        index = self.findData(value, self.DataRole)
        self.setCurrentIndex(index)


class TitleCard(Card):
    run = QtCore.Signal()
    cancel = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QLabel('Decontaminate')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'For each sequence in the input dataset, find the closest match in the reference database.')
        description.setWordWrap(True)

        run = QtWidgets.QPushButton('Run')
        run.clicked.connect(self.handleRun)
        run.setVisible(False)

        cancel = QtWidgets.QPushButton('Cancel')
        cancel.clicked.connect(self.handleCancel)
        cancel.setVisible(False)

        remove = QtWidgets.QPushButton('Remove')
        remove.setEnabled(False)
        remove.setVisible(False)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)
        contents.setSpacing(6)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(run)
        buttons.addWidget(cancel)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 10, 0, 10)
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        self.addLayout(layout)

        self.controls.run = run
        self.controls.cancel = cancel
        self.controls.title = title

    def handleRun(self):
        self.run.emit()

    def handleCancel(self):
        self.cancel.emit()

    def setTitle(self, text):
        self.controls.title.setText(text)

    def setReady(self, ready: bool):
        # self.controls.run.setEnabled(ready)
        pass

    def setBusy(self, busy: bool):
        self.setEnabled(True)
        # self.controls.run.setVisible(not busy)
        # self.controls.cancel.setVisible(busy)


class DummyResultsCard(Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.path = Path()

        title = QtWidgets.QLabel('Results: ')
        title.setStyleSheet("""font-size: 16px;""")
        title.setMinimumWidth(120)

        path = QtWidgets.QLineEdit()
        path.setReadOnly(True)

        browse = QtWidgets.QPushButton('Browse')
        browse.clicked.connect(self.handleBrowse)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(title)
        layout.addWidget(path, 1)
        layout.addWidget(browse)
        layout.setSpacing(16)
        self.addLayout(layout)

        self.controls.path = path
        self.controls.browse = browse

    def handleBrowse(self):
        url = QtCore.QUrl.fromLocalFile(str(self.path))
        QtGui.QDesktopServices.openUrl(url)

    def setPath(self, path: Path):
        if path is None:
            path = Path()
        self.path = path
        self.controls.path.setText(str(path))


class ProgressCard(QtWidgets.QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximum(0)
        self.setMinimum(0)
        self.setValue(0)
        self.setVisible(False)

    def showProgress(self, report):
        self.setMaximum(report.maximum)
        self.setMinimum(report.minimum)
        self.setValue(report.value)


class InputSelector(Card):
    itemChanged = QtCore.Signal(Item)
    addInputFile = QtCore.Signal(Path)

    def __init__(self, text, parent=None, model=app.model.items):
        super().__init__(parent)
        self.binder = Binder()
        self._guard = Guard()
        self.draw_main(text, model)
        self.draw_config()

    def draw_main(self, text, model):
        label = QtWidgets.QLabel(text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setMinimumWidth(120)

        combo = NoWheelComboBox()
        combo.currentIndexChanged.connect(self.handleItemChanged)
        self.set_model(combo, model)

        wait = NoWheelComboBox()
        wait.addItem('Scanning file, please wait...')
        wait.setEnabled(False)
        wait.setVisible(False)

        browse = QtWidgets.QPushButton('Import')
        browse.clicked.connect(self.handleBrowse)

        loading = QtWidgets.QPushButton('Loading')
        loading.setEnabled(False)
        loading.setVisible(False)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(combo, 1)
        layout.addWidget(wait, 1)
        layout.addWidget(browse)
        layout.addWidget(loading)
        layout.setSpacing(16)
        self.addLayout(layout)

        self.controls.label = label
        self.controls.combo = combo
        self.controls.wait = wait
        self.controls.browse = browse
        self.controls.loading = loading

    def draw_config(self):
        self.controls.config = None

    def set_model(self, combo, model):
        combo.setModel(model)

    def handleItemChanged(self, row):
        if self._guard:
            return
        if row > 0:
            item = self.controls.combo.itemData(row, ItemModel.ItemRole)
        else:
            item = None
        self.itemChanged.emit(item)

    def handleBrowse(self, *args):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f'{app.title} - Import Sequence File')
        if not filename:
            return
        self.addInputFile.emit(Path(filename))

    def setObject(self, object):
        # Workaround to repaint bugged card line
        QtCore.QTimer.singleShot(10, self.update)

        if object is None:
            row = 0
        else:
            file_item = object.file_item
            row = file_item.row + 1 if file_item else 0
        with self._guard:
            self.controls.combo.setCurrentIndex(row)

        self.binder.unbind_all()

    def setBusy(self, busy: bool):
        self.setEnabled(True)
        self.controls.combo.setVisible(not busy)
        self.controls.wait.setVisible(busy)
        self.controls.browse.setVisible(not busy)
        self.controls.loading.setVisible(busy)
        self.controls.label.setEnabled(not busy)
        self.controls.config.setEnabled(not busy)


class SequenceSelector(InputSelector):
    def set_model(self, combo, model):
        proxy_model = ItemProxyModel()
        proxy_model.setSourceModel(model, model.files)
        combo.setModel(proxy_model)

    def draw_config(self):
        self.controls.config = MinimumStackedWidget()
        self.addWidget(self.controls.config)
        self.draw_config_tabfile()
        self.draw_config_fasta()

    def draw_config_tabfile(self):
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

        index_filter = ColumnFilterCombobox()
        index_filter.setFixedWidth(40)
        sequence_filter = ColumnFilterCombobox()
        sequence_filter.setFixedWidth(40)

        layout.addWidget(index_filter, 0, column)
        layout.addWidget(sequence_filter, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 16)
        column += 1

        view = QtWidgets.QPushButton('View')
        view.setVisible(False)

        layout.addWidget(view, 0, column)
        layout.setColumnMinimumWidth(column, 80)
        column += 1

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.tabfile = AttrDict()
        self.controls.tabfile.widget = widget
        self.controls.tabfile.index_combo = index_combo
        self.controls.tabfile.sequence_combo = sequence_combo
        self.controls.tabfile.index_filter = index_filter
        self.controls.tabfile.sequence_filter = sequence_filter
        self.controls.tabfile.file_size = size_label_value
        self.controls.config.addWidget(widget)

    def draw_config_fasta(self):
        type_label = QtWidgets.QLabel('File format:')
        size_label = QtWidgets.QLabel('File size:')

        type_label_value = QtWidgets.QLabel('Fasta')
        size_label_value = QtWidgets.QLabel('42 MB')

        view = QtWidgets.QPushButton('View')
        view.setVisible(False)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(type_label)
        layout.addWidget(type_label_value)
        layout.addSpacing(48)
        layout.addWidget(size_label)
        layout.addWidget(size_label_value)
        layout.addStretch(1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.fasta = AttrDict()
        self.controls.fasta.widget = widget
        self.controls.fasta.file_size = size_label_value
        self.controls.config.addWidget(widget)

    def setObject(self, object):
        super().setObject(object)
        if object and isinstance(object, SequenceModel.Tabfile):
            self.populateCombos(object.file_item.object.info.headers)
            self.binder.bind(object.properties.index_column, self.controls.tabfile.index_combo.setCurrentIndex)
            self.binder.bind(self.controls.tabfile.index_combo.currentIndexChanged, object.properties.index_column)
            self.binder.bind(object.properties.sequence_column, self.controls.tabfile.sequence_combo.setCurrentIndex)
            self.binder.bind(self.controls.tabfile.sequence_combo.currentIndexChanged, object.properties.sequence_column)
            self.binder.bind(object.properties.index_filter, self.controls.tabfile.index_filter.setValue)
            self.binder.bind(self.controls.tabfile.index_filter.valueChanged, object.properties.index_filter)
            self.binder.bind(object.properties.sequence_filter, self.controls.tabfile.sequence_filter.setValue)
            self.binder.bind(self.controls.tabfile.sequence_filter.valueChanged, object.properties.sequence_filter)
            self.binder.bind(object.file_item.object.properties.size, self.controls.tabfile.file_size.setText, lambda x: human_readable_size(x))
            self.controls.config.setCurrentWidget(self.controls.tabfile.widget)
            self.controls.config.setVisible(True)
        elif object and isinstance(object, SequenceModel.Fasta):
            self.binder.bind(object.file_item.object.properties.size, self.controls.fasta.file_size.setText, lambda x: human_readable_size(x))
            self.controls.config.setCurrentWidget(self.controls.fasta.widget)
            self.controls.config.setVisible(True)
        else:
            self.controls.config.setVisible(False)

    def populateCombos(self, headers):
        self.controls.tabfile.index_combo.clear()
        self.controls.tabfile.sequence_combo.clear()
        for header in headers:
            self.controls.tabfile.index_combo.addItem(header)
            self.controls.tabfile.sequence_combo.addItem(header)


class AlignmentModeSelector(CardCustom):
    resetScores = QtCore.Signal()

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
        for mode in AlignmentMode:
            button = RichRadioButton(f'{mode.label}:', mode.description, self)
            if mode == AlignmentMode.NoAlignment:
                button.hide()
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


class DistanceMetricSelector(Card):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_main()
        self.draw_file_type()
        self.draw_format()

    def draw_main(self):
        label = QtWidgets.QLabel('Distance metric')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Select the type of distances that should be calculated for each pair of sequences:')
        description.setWordWrap(True)

        metrics = QtWidgets.QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(8)

        metric_p = NoWheelRadioButton('Uncorrected (p-distance)')
        metric_pg = NoWheelRadioButton('Uncorrected with gaps')
        metric_jc = NoWheelRadioButton('Jukes Cantor (jc)')
        metric_k2p = NoWheelRadioButton('Kimura 2-Parameter (k2p)')
        metrics.addWidget(metric_p, 0, 0)
        metrics.addWidget(metric_pg, 1, 0)
        metrics.setColumnStretch(0, 2)
        metrics.setColumnMinimumWidth(1, 16)
        metrics.setColumnStretch(1, 0)
        metrics.addWidget(metric_jc, 0, 2)
        metrics.addWidget(metric_k2p, 1, 2)
        metrics.setColumnStretch(2, 2)

        metric_ncd = NoWheelRadioButton('Normalized Compression Distance (NCD)')
        metric_bbc = NoWheelRadioButton('Base-Base Correlation (BBC)')

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
        write_linear = QtWidgets.QCheckBox('Write distances in linear format (all metrics in the same file)')
        write_matricial = QtWidgets.QCheckBox('Write distances in matricial format (one metric per matrix file)')

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

        unit_radio = QtWidgets.QRadioButton('Distances from 0.0 to 1.0')
        percent_radio = QtWidgets.QRadioButton('Distances as percentages (%)')

        percentile = RadioButtonGroup()
        percentile.add(unit_radio, False)
        percentile.add(percent_radio, True)

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

        precision = GLineEdit('4')
        missing = GLineEdit('NA')

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
        self.addLayout(layout)

        self.controls.similarityThreshold = threshold


class IdentityThresholdCard(Card):

    def __init__(self, parent=None):
        super().__init__(parent)

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
        self.addLayout(layout)

        self.controls.identityThreshold = threshold


class View(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.dummy_results = DummyResultsCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_sequences = SequenceSelector('Input sequence', self)
        self.cards.mode_selector = DecontaminateModeSelector(self)
        self.cards.outgroup_sequences = SequenceSelector('Outgroup reference', self)
        self.cards.ingroup_sequences = SequenceSelector('Ingroup reference', self)
        self.cards.weight_selector = ReferenceWeightSelector(self)
        self.cards.alignment_mode = AlignmentModeSelector(self)
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
        self.binder.bind(object.properties.ready, self.cards.title.setReady)
        self.binder.bind(object.properties.busy_main, self.cards.title.setBusy)
        self.binder.bind(object.properties.busy_main, self.cards.progress.setEnabled)
        self.binder.bind(object.properties.busy_main, self.cards.progress.setVisible)
        self.binder.bind(object.properties.busy_input, self.cards.input_sequences.setBusy)
        self.binder.bind(object.properties.busy_outgroup, self.cards.outgroup_sequences.setBusy)
        self.binder.bind(object.properties.busy_ingroup, self.cards.ingroup_sequences.setBusy)

        self.binder.bind(self.cards.mode_selector.toggled, self.object.properties.decontaminate_mode)
        self.binder.bind(self.object.properties.decontaminate_mode, self.cards.mode_selector.setDecontaminateMode)

        self.binder.bind(self.cards.input_sequences.itemChanged, object.set_input_file_from_file_item)
        self.binder.bind(object.properties.input_sequences, self.cards.input_sequences.setObject)
        self.binder.bind(self.cards.input_sequences.addInputFile, object.add_input_file)

        self.binder.bind(self.cards.outgroup_sequences.itemChanged, object.set_outgroup_file_from_file_item)
        self.binder.bind(object.properties.outgroup_sequences, self.cards.outgroup_sequences.setObject)
        self.binder.bind(self.cards.outgroup_sequences.addInputFile, object.add_outgroup_file)

        self.binder.bind(self.cards.ingroup_sequences.itemChanged, object.set_ingroup_file_from_file_item)
        self.binder.bind(object.properties.ingroup_sequences, self.cards.ingroup_sequences.setObject)
        self.binder.bind(self.cards.ingroup_sequences.addInputFile, object.add_ingroup_file)

        self.binder.bind(self.cards.alignment_mode.controls.mode.valueChanged, object.properties.alignment_mode)
        self.binder.bind(object.properties.alignment_mode, self.cards.alignment_mode.controls.mode.setValue)
        self.binder.bind(self.cards.alignment_mode.controls.write_pairs.toggled, object.properties.alignment_write_pairs)
        self.binder.bind(object.properties.alignment_write_pairs, self.cards.alignment_mode.controls.write_pairs.setChecked)
        self.binder.bind(self.cards.alignment_mode.resetScores, object.pairwise_scores.reset)
        for score in PairwiseScore:
            self.binder.bind(
                self.cards.alignment_mode.controls.score_fields[score.key].textEditedSafe,
                object.pairwise_scores.properties[score.key],
                lambda x: type_convert(x, int, None))
            self.binder.bind(
                object.pairwise_scores.properties[score.key],
                self.cards.alignment_mode.controls.score_fields[score.key].setText,
                lambda x: str(x) if x is not None else '')

        self.binder.bind(object.properties.distance_metric, self.cards.distance_metrics.controls.group.setValue)
        self.binder.bind(self.cards.distance_metrics.controls.group.valueChanged, object.properties.distance_metric)

        self.binder.bind(self.cards.distance_metrics.controls.bbc_k.textEditedSafe, object.properties.distance_metric_bbc_k, lambda x: type_convert(x, int, None))
        self.binder.bind(object.properties.distance_metric_bbc_k, self.cards.distance_metrics.controls.bbc_k.setText, lambda x: str(x) if x is not None else '')
        self.binder.bind(object.properties.distance_metric, self.cards.distance_metrics.controls.bbc_k.setEnabled, lambda x: x == DistanceMetric.BBC)
        self.binder.bind(object.properties.distance_metric, self.cards.distance_metrics.controls.bbc_k_label.setEnabled, lambda x: x == DistanceMetric.BBC)

        self.binder.bind(self.cards.distance_metrics.controls.write_linear.toggled, object.properties.distance_linear)
        self.binder.bind(object.properties.distance_linear, self.cards.distance_metrics.controls.write_linear.setChecked)
        self.binder.bind(self.cards.distance_metrics.controls.write_matricial.toggled, object.properties.distance_matricial)
        self.binder.bind(object.properties.distance_matricial, self.cards.distance_metrics.controls.write_matricial.setChecked)

        self.binder.bind(self.cards.distance_metrics.controls.percentile.valueChanged, object.properties.distance_percentile)
        self.binder.bind(object.properties.distance_percentile, self.cards.distance_metrics.controls.percentile.setValue)

        self.binder.bind(self.cards.distance_metrics.controls.precision.textEditedSafe, object.properties.distance_precision, lambda x: type_convert(x, int, None))
        self.binder.bind(object.properties.distance_precision, self.cards.distance_metrics.controls.precision.setText, lambda x: str(x) if x is not None else '')
        self.binder.bind(self.cards.distance_metrics.controls.missing.textEditedSafe, object.properties.distance_missing)
        self.binder.bind(object.properties.distance_missing, self.cards.distance_metrics.controls.missing.setText)

        self.binder.bind(object.properties.alignment_mode, self.cards.distance_metrics.setAlignmentMode)

        self.binder.bind(object.properties.similarity_threshold, self.cards.similarity.controls.similarityThreshold.setText, lambda x: f'{x:.2f}')
        self.binder.bind(self.cards.similarity.controls.similarityThreshold.textEditedSafe, object.properties.similarity_threshold, lambda x: type_convert(x, float, None))

        self.binder.bind(object.properties.similarity_threshold, self.cards.identity.controls.identityThreshold.setValue, lambda x: 100 - round(x * 100))
        self.binder.bind(self.cards.identity.controls.identityThreshold.valueChangedSafe, object.properties.similarity_threshold, lambda x: (100 - x) / 100)

        self.binder.bind(object.properties.outgroup_weight, self.cards.weight_selector.setOutgroupWeight)
        self.binder.bind(object.properties.ingroup_weight, self.cards.weight_selector.setIngroupWeight)
        self.binder.bind(self.cards.weight_selector.edited_outgroup, object.properties.outgroup_weight)
        self.binder.bind(self.cards.weight_selector.edited_ingroup, object.properties.ingroup_weight)

        self.binder.bind(object.properties.dummy_results, self.cards.dummy_results.setPath)
        self.binder.bind(object.properties.dummy_results, self.cards.dummy_results.roll_animation.setAnimatedVisible,  lambda x: x is not None)

        self.binder.bind(object.properties.distance_metric, self.update_visible_cards)
        self.binder.bind(object.properties.decontaminate_mode, self.update_visible_cards)

        self.binder.bind(object.properties.editable, self.setEditable)

    def update_visible_cards(self, *args, **kwargs):
        uncorrected = any((
            self.object.distance_metric == DistanceMetric.Uncorrected,
            self.object.distance_metric == DistanceMetric.UncorrectedWithGaps,
        ))
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
        path = self.getExistingDirectory('Save All')
        if path:
            self.object.save(path)

    def handleMode(self, mode):
        self.cards.similarity.setVisible(mode.type is ComparisonMode.AlignmentFree)
        self.cards.identity.setVisible(mode.type is not ComparisonMode.AlignmentFree)
