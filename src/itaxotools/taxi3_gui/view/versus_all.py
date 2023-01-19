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

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from .. import app
from ..utility import Guard, bind, unbind, type_convert, human_readable_size
from ..model import Item, ItemModel, Object, SequenceModel, SequenceModel2, PartitionModel
from ..types import ColumnFilter, Notification, AlignmentMode, PairwiseComparisonConfig, StatisticsGroup, AlignmentMode, PairwiseScore, DistanceMetric
from .common import Item, Card, NoWheelComboBox, GLineEdit, ObjectView, SequenceSelector as SequenceSelectorLegacy, ComparisonModeSelector as ComparisonModeSelectorLegacy


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


class RadioButtonGroup(QtCore.QObject):
    valueChanged = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.members = dict()
        self.value = None

    def add(self, widget, value):
        self.members[widget] = value
        widget.toggled.connect(self.handleToggle)

    def handleToggle(self, checked):
        if not checked:
            return
        self.value = self.members[self.sender()]
        self.valueChanged.emit(self.value)

    def setValue(self, newValue):
        self.value = newValue
        for widget, value in self.members.items():
            widget.setChecked(value == newValue)


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

        title = QtWidgets.QLabel('Versus All')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Derive statistics from the distance betweens all pairs of sequences.')
        description.setWordWrap(True)

        run = QtWidgets.QPushButton('Run')
        run.clicked.connect(self.handleRun)

        cancel = QtWidgets.QPushButton('Cancel')
        cancel.clicked.connect(self.handleCancel)

        remove = QtWidgets.QPushButton('Remove')
        remove.setEnabled(False)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)
        contents.setSpacing(12)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(run)
        buttons.addWidget(cancel)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
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
        self.controls.run.setEnabled(ready)

    def setBusy(self, busy: bool):
        self.setEnabled(True)
        self.controls.run.setVisible(not busy)
        self.controls.cancel.setVisible(busy)


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
        self.bindings = set()
        self._guard = Guard()
        self.draw_main(text, model)
        self.draw_config()

    def draw_main(self, text, model):
        label = QtWidgets.QLabel(text + ':')
        label.setStyleSheet("""font-size: 16px;""")

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
        layout.addSpacing(8)
        layout.addWidget(combo, 1)
        layout.addWidget(wait, 1)
        layout.addWidget(browse)
        layout.addWidget(loading)
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

        self.unbind_all()

    def bind(self, src, dst, proxy=None):
        key = bind(src, dst, proxy)
        self.bindings.add(key)

    def unbind(self, src, dst):
        key = unbind(src, dst)
        self.bindings.remove(key)

    def unbind_all(self):
        for key in self.bindings:
            unbind(key.signal, key.slot)
        self.bindings.clear()

    def setBusy(self, busy: bool):
        self.setEnabled(True)
        self.controls.combo.setVisible(not busy)
        self.controls.wait.setVisible(busy)
        self.controls.browse.setVisible(not busy)
        self.controls.loading.setVisible(busy)
        self.controls.label.setEnabled(not busy)
        self.controls.config.setEnabled(not busy)


class SequenceSelector(InputSelector):
    indexColumnChanged = QtCore.Signal(str)
    sequenceColumnChanged = QtCore.Signal(str)

    def set_model(self, combo, model):
        proxy_model = ItemProxyModel()
        proxy_model.setSourceModel(model, model.files)
        combo.setModel(proxy_model)

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

        index_combo.currentIndexChanged.connect(self.handleIndexColumnChanged)
        sequence_combo.currentIndexChanged.connect(self.handleSequenceColumnChanged)

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

        layout.addWidget(view, 0, column)
        column += 1

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.config = widget
        self.controls.index_combo = index_combo
        self.controls.sequence_combo = sequence_combo
        self.controls.index_filter = index_filter
        self.controls.sequence_filter = sequence_filter
        self.controls.file_size = size_label_value

    def setObject(self, object):
        super().setObject(object)
        if object and isinstance(object, SequenceModel2.Tabfile):
            self.populateCombos(object.file_item.object.headers)
            self.bind(object.properties.index_column, self.setColumnIndex)
            self.bind(self.indexColumnChanged, object.properties.index_column)
            self.bind(object.properties.sequence_column, self.setColumnSequence)
            self.bind(self.sequenceColumnChanged, object.properties.sequence_column)
            self.bind(object.properties.index_filter, self.controls.index_filter.setValue)
            self.bind(self.controls.index_filter.valueChanged, object.properties.index_filter)
            self.bind(object.properties.sequence_filter, self.controls.sequence_filter.setValue)
            self.bind(self.controls.sequence_filter.valueChanged, object.properties.sequence_filter)
            self.bind(object.file_item.object.properties.size, self.controls.file_size.setText, lambda x: human_readable_size(x))
            self.controls.config.setVisible(True)
        else:
            self.controls.config.setVisible(False)

    def populateCombos(self, headers):
        self.controls.index_combo.clear()
        self.controls.sequence_combo.clear()
        for header in headers:
            self.controls.index_combo.addItem(header, header)
            self.controls.sequence_combo.addItem(header, header)

    def setColumnIndex(self, column):
        row = self.controls.index_combo.findData(column)
        self.controls.index_combo.setCurrentIndex(row)

    def setColumnSequence(self, column):
        row = self.controls.sequence_combo.findData(column)
        self.controls.sequence_combo.setCurrentIndex(row)

    def handleIndexColumnChanged(self, row):
        value = self.controls.index_combo.currentData() if row >= 0 else ''
        self.indexColumnChanged.emit(value)

    def handleSequenceColumnChanged(self, row):
        value = self.controls.sequence_combo.currentData() if row >= 0 else ''
        self.sequenceColumnChanged.emit(value)


class PartitionSelector(InputSelector):
    subsetColumnChanged = QtCore.Signal(str)
    individualColumnChanged = QtCore.Signal(str)

    def __init__(self, text, subset_text=None, individual_text=None, parent=None, model=app.model.items):
        self._subset_text = subset_text or 'Subsets'
        self._individual_text = individual_text or 'Individuals'
        super().__init__(text, parent, model)

    def set_model(self, combo, model):
        proxy_model = ItemProxyModel()
        proxy_model.setSourceModel(model, model.files)
        combo.setModel(proxy_model)

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

        subset_label = QtWidgets.QLabel(f'{self._subset_text}:')
        individual_label = QtWidgets.QLabel(f'{self._individual_text}:')

        layout.addWidget(subset_label, 0, column)
        layout.addWidget(individual_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        subset_combo = NoWheelComboBox()
        individual_combo = NoWheelComboBox()

        subset_combo.currentIndexChanged.connect(self.handleSubsetColumnChanged)
        individual_combo.currentIndexChanged.connect(self.handleIndividualColumnChanged)

        layout.addWidget(subset_combo, 0, column)
        layout.addWidget(individual_combo, 1, column)
        layout.setColumnStretch(column, 1)
        column += 1

        subset_filter = ColumnFilterCombobox()
        subset_filter.setFixedWidth(40)
        individual_filter = ColumnFilterCombobox()
        individual_filter.setFixedWidth(40)

        layout.addWidget(subset_filter, 0, column)
        layout.addWidget(individual_filter, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 16)
        column += 1

        view = QtWidgets.QPushButton('View')

        layout.addWidget(view, 0, column)
        column += 1

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.config = widget
        self.controls.subset_combo = subset_combo
        self.controls.individual_combo = individual_combo
        self.controls.subset_filter = subset_filter
        self.controls.individual_filter = individual_filter
        self.controls.file_size = size_label_value

    def setObject(self, object):
        super().setObject(object)
        if object and isinstance(object, PartitionModel.Tabfile):
            self.populateCombos(object.file_item.object.headers)
            self.bind(object.properties.subset_column, self.setColumnSubset)
            self.bind(self.subsetColumnChanged, object.properties.subset_column)
            self.bind(object.properties.individual_column, self.setColumnIndividual)
            self.bind(self.individualColumnChanged, object.properties.individual_column)
            self.bind(object.properties.subset_filter, self.controls.subset_filter.setValue)
            self.bind(self.controls.subset_filter.valueChanged, object.properties.subset_filter)
            self.bind(object.properties.individual_filter, self.controls.individual_filter.setValue)
            self.bind(self.controls.individual_filter.valueChanged, object.properties.individual_filter)
            self.bind(object.file_item.object.properties.size, self.controls.file_size.setText, lambda x: human_readable_size(x))
            self.controls.config.setVisible(True)
        else:
            self.controls.config.setVisible(False)

    def populateCombos(self, headers):
        self.controls.subset_combo.clear()
        self.controls.individual_combo.clear()
        for header in headers:
            self.controls.subset_combo.addItem(header, header)
            self.controls.individual_combo.addItem(header, header)

    def setColumnSubset(self, column):
        row = self.controls.subset_combo.findData(column)
        self.controls.subset_combo.setCurrentIndex(row)

    def setColumnIndividual(self, column):
        row = self.controls.individual_combo.findData(column)
        self.controls.individual_combo.setCurrentIndex(row)

    def handleSubsetColumnChanged(self, row):
        value = self.controls.subset_combo.currentData() if row >= 0 else ''
        self.subsetColumnChanged.emit(value)

    def handleIndividualColumnChanged(self, row):
        value = self.controls.individual_combo.currentData() if row >= 0 else ''
        self.individualColumnChanged.emit(value)


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


class AlignmentModeSelector(Card):
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
        layout.setSpacing(16)

        group = RadioButtonGroup()
        group.valueChanged.connect(self.handleModeChanged)
        self.controls.mode = group

        radios = QtWidgets.QVBoxLayout()
        radios.setSpacing(8)
        for mode in AlignmentMode:
            button = RichRadioButton(f'{mode.label}:', mode.description, self)
            button.setEnabled(mode != AlignmentMode.MSA)
            radios.addWidget(button)
            group.add(button, mode)

        layout.addLayout(radios)
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

        self.controls.pairwise_config = widget

    def handleToggle(self, checked):
        if not checked:
            return
        for button in self.controls.radio_buttons:
            if button.isChecked():
                self.toggled.emit(button.alignmentMode)

    def handleModeChanged(self, mode):
        self.controls.pairwise_config.setVisible(mode == AlignmentMode.PairwiseAlignment)


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


class VersusAllView(ObjectView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_sequences = SequenceSelector('Input Sequences', self)
        self.cards.perform_species = OptionalCategory(
            'Perform Species Analysis',
            'Calculate various metrics betweens all pairs of species (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_species = PartitionSelector('Species Partition', 'Species', 'Individuals', self)
        self.cards.perform_genera = OptionalCategory(
            'Perform Genus Analysis',
            'Calculate various metrics betweens all pairs of genera (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_genera = PartitionSelector('Genera Partition', 'Genera', 'Individuals', self)
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

        self.bind(object.notification, self.showNotification)
        self.bind(object.progression, self.cards.progress.showProgress)

        self.bind(self.cards.title.run, object.start)
        self.bind(self.cards.title.cancel, object.stop)
        self.bind(object.properties.name, self.cards.title.setTitle)
        self.bind(object.properties.ready, self.cards.title.setReady)
        self.bind(object.properties.busy_main, self.setBusyMain)
        self.bind(object.properties.busy_sequence, self.setBusySequence)
        self.bind(object.properties.busy_species, self.setBusySpecies)
        self.bind(object.properties.busy_genera, self.setBusyGenera)

        self.bind(self.cards.input_sequences.itemChanged, object.set_sequence_file_from_file_item)
        self.bind(object.properties.input_sequences, self.cards.input_sequences.setObject)
        self.bind(self.cards.input_sequences.addInputFile, object.add_sequence_file)

        self.bind(self.cards.perform_species.toggled, object.properties.perform_species)
        self.bind(object.properties.perform_species, self.cards.perform_species.setChecked)
        self.bind(object.properties.perform_species, self.cards.input_species.setVisible)

        self.bind(self.cards.input_species.itemChanged, object.set_species_file_from_file_item)
        self.bind(object.properties.input_species, self.cards.input_species.setObject)
        self.bind(self.cards.input_species.addInputFile, object.add_species_file)

        self.bind(self.cards.perform_genera.toggled, object.properties.perform_genera)
        self.bind(object.properties.perform_genera, self.cards.perform_genera.setChecked)
        self.bind(object.properties.perform_genera, self.cards.input_genera.setVisible)

        self.bind(self.cards.input_genera.itemChanged, object.set_genera_file_from_file_item)
        self.bind(object.properties.input_genera, self.cards.input_genera.setObject)
        self.bind(self.cards.input_genera.addInputFile, object.add_genera_file)

        self.bind(self.cards.alignment_mode.controls.mode.valueChanged, object.properties.alignment_mode)
        self.bind(object.properties.alignment_mode, self.cards.alignment_mode.controls.mode.setValue)
        self.bind(self.cards.alignment_mode.controls.write_pairs.toggled, object.properties.alignment_write_pairs)
        self.bind(object.properties.alignment_write_pairs, self.cards.alignment_mode.controls.write_pairs.setChecked)
        self.bind(self.cards.alignment_mode.resetScores, object.pairwise_scores.reset)
        for score in PairwiseScore:
            self.bind(
                self.cards.alignment_mode.controls.score_fields[score.key].textEditedSafe,
                object.pairwise_scores.properties[score.key],
                lambda x: type_convert(x, int, None))
            self.bind(
                object.pairwise_scores.properties[score.key],
                self.cards.alignment_mode.controls.score_fields[score.key].setText,
                lambda x: str(x) if x is not None else '')

        for key in (metric.key for metric in DistanceMetric):
            self.bind(self.cards.distance_metrics.controls.metrics[key].toggled, object.distance_metrics.properties[key])
            self.bind(object.distance_metrics.properties[key], self.cards.distance_metrics.controls.metrics[key].setChecked)

        self.bind(self.cards.distance_metrics.controls.bbc_k.textEditedSafe, object.distance_metrics.properties.bbc_k, lambda x: type_convert(x, int, None))
        self.bind(object.distance_metrics.properties.bbc_k, self.cards.distance_metrics.controls.bbc_k.setText, lambda x: str(x) if x is not None else '')
        self.bind(object.distance_metrics.properties.bbc, self.cards.distance_metrics.controls.bbc_k.setEnabled)
        self.bind(object.distance_metrics.properties.bbc, self.cards.distance_metrics.controls.bbc_k_label.setEnabled)

        self.bind(self.cards.distance_metrics.controls.write_linear.toggled, object.properties.distance_linear)
        self.bind(object.properties.distance_linear, self.cards.distance_metrics.controls.write_linear.setChecked)
        self.bind(self.cards.distance_metrics.controls.write_matricial.toggled, object.properties.distance_matricial)
        self.bind(object.properties.distance_matricial, self.cards.distance_metrics.controls.write_matricial.setChecked)

        self.bind(self.cards.distance_metrics.controls.percentile.valueChanged, object.properties.distance_percentile)
        self.bind(object.properties.distance_percentile, self.cards.distance_metrics.controls.percentile.setValue)

        self.bind(self.cards.distance_metrics.controls.precision.textEditedSafe, object.properties.distance_precision, lambda x: type_convert(x, int, None))
        self.bind(object.properties.distance_precision, self.cards.distance_metrics.controls.precision.setText, lambda x: str(x) if x is not None else '')
        self.bind(self.cards.distance_metrics.controls.missing.textEditedSafe, object.properties.distance_missing)
        self.bind(object.properties.distance_missing, self.cards.distance_metrics.controls.missing.setText)

        for group in StatisticsGroup:
            self.bind(self.cards.stats_options.controls[group.key].toggled, object.statistics_groups.properties[group.key])
            self.bind(object.statistics_groups.properties[group.key], self.cards.stats_options.controls[group.key].setChecked)

    def setBusyMain(self, busy: bool):
        for card in self.cards:
            card.setEnabled(not busy)
        self.cards.title.setBusy(busy)
        self.cards.progress.setEnabled(busy)
        self.cards.progress.setVisible(busy)

    def setBusySequence(self, busy: bool):
        for card in self.cards:
            card.setEnabled(not busy)
        self.cards.input_sequences.setBusy(busy)

    def setBusySpecies(self, busy: bool):
        for card in self.cards:
            card.setEnabled(not busy)
        self.cards.input_species.setBusy(busy)

    def setBusyGenera(self, busy: bool):
        for card in self.cards:
            card.setEnabled(not busy)
        self.cards.input_genera.setBusy(busy)

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
