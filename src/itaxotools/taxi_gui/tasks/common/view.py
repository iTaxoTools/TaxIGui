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

from itaxotools.common.bindings import Binder
from itaxotools.common.utility import AttrDict, Guard

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.model.common import Item, ItemModel
from itaxotools.taxi_gui.model.partition import PartitionModel
from itaxotools.taxi_gui.model.sequence import SequenceModel
from itaxotools.taxi_gui.types import ColumnFilter
from itaxotools.taxi_gui.utility import human_readable_size
from itaxotools.taxi_gui.view.animations import VerticalRollAnimation
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.widgets import (
    GLineEdit, MinimumStackedWidget, NoWheelComboBox, RadioButtonGroup,
    RichRadioButton)

from .model import ItemProxyModel
from .types import AlignmentMode, PairwiseScore


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

        parse_organism = QtWidgets.QCheckBox('Parse identifiers as "individual|taxon"')

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
        layout.addSpacing(48)
        layout.addWidget(parse_organism)
        layout.addStretch(1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.fasta = AttrDict()
        self.controls.fasta.widget = widget
        self.controls.fasta.file_size = size_label_value
        self.controls.fasta.parse_organism = parse_organism
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
            self.binder.bind(object.properties.parse_organism, self.controls.fasta.parse_organism.setChecked)
            self.binder.bind(self.controls.fasta.parse_organism.toggled, object.properties.parse_organism)
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


class PartitionSelector(InputSelector):
    def __init__(self, text, subset_text=None, individual_text=None, parent=None, model=app.model.items):
        self._subset_text = subset_text or 'Subsets'
        self._individual_text = individual_text or 'Individuals'
        super().__init__(text, parent, model)

    def set_model(self, combo, model):
        proxy_model = ItemProxyModel()
        proxy_model.setSourceModel(model, model.files)
        combo.setModel(proxy_model)

    def draw_config(self):
        self.controls.config = MinimumStackedWidget()
        self.addWidget(self.controls.config)
        self.draw_config_tabfile()
        self.draw_config_fasta()
        self.draw_config_spart()

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

        subset_label = QtWidgets.QLabel(f'{self._subset_text}:')
        individual_label = QtWidgets.QLabel(f'{self._individual_text}:')

        layout.addWidget(subset_label, 0, column)
        layout.addWidget(individual_label, 1, column)
        column += 1

        layout.setColumnMinimumWidth(column, 8)
        column += 1

        subset_combo = NoWheelComboBox()
        individual_combo = NoWheelComboBox()

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
        view.setVisible(False)

        layout.addWidget(view, 0, column)
        layout.setColumnMinimumWidth(column, 80)
        column += 1

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.tabfile = AttrDict()
        self.controls.tabfile.widget = widget
        self.controls.tabfile.subset_combo = subset_combo
        self.controls.tabfile.individual_combo = individual_combo
        self.controls.tabfile.subset_filter = subset_filter
        self.controls.tabfile.individual_filter = individual_filter
        self.controls.tabfile.file_size = size_label_value
        self.controls.config.addWidget(widget)

    def draw_config_fasta(self):
        type_label = QtWidgets.QLabel('File format:')
        size_label = QtWidgets.QLabel('File size:')

        type_label_value = QtWidgets.QLabel('Fasta')
        size_label_value = QtWidgets.QLabel('42 MB')

        filter_first = QtWidgets.QCheckBox('Only keep first word')

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
        layout.addSpacing(48)
        layout.addWidget(filter_first)
        layout.addStretch(1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.fasta = AttrDict()
        self.controls.fasta.widget = widget
        self.controls.fasta.file_size = size_label_value
        self.controls.fasta.filter_first = filter_first
        self.controls.config.addWidget(widget)

    def draw_config_spart(self):
        type_label = QtWidgets.QLabel('File format:')
        size_label = QtWidgets.QLabel('File size:')

        type_label_value = QtWidgets.QLabel('Spart-???')
        size_label_value = QtWidgets.QLabel('42 MB')

        spartition_label = QtWidgets.QLabel('Spartition:')
        spartition = NoWheelComboBox()

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
        layout.addSpacing(48)
        layout.addWidget(spartition_label)
        layout.addWidget(spartition, 1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.controls.spart = AttrDict()
        self.controls.spart.widget = widget
        self.controls.spart.file_type = type_label_value
        self.controls.spart.file_size = size_label_value
        self.controls.spart.spartition = spartition
        self.controls.config.addWidget(widget)

    def setObject(self, object):
        super().setObject(object)
        self.object = object
        if object and isinstance(object, PartitionModel.Tabfile):
            self.populateCombos(object.file_item.object.info.headers)
            self.binder.bind(object.properties.subset_column, self.controls.tabfile.subset_combo.setCurrentIndex)
            self.binder.bind(self.controls.tabfile.subset_combo.currentIndexChanged, object.properties.subset_column)
            self.binder.bind(object.properties.individual_column, self.controls.tabfile.individual_combo.setCurrentIndex)
            self.binder.bind(self.controls.tabfile.individual_combo.currentIndexChanged, object.properties.individual_column)
            self.binder.bind(object.properties.subset_filter, self.controls.tabfile.subset_filter.setValue)
            self.binder.bind(self.controls.tabfile.subset_filter.valueChanged, object.properties.subset_filter)
            self.binder.bind(object.properties.individual_filter, self.controls.tabfile.individual_filter.setValue)
            self.binder.bind(self.controls.tabfile.individual_filter.valueChanged, object.properties.individual_filter)
            self.binder.bind(object.file_item.object.properties.size, self.controls.tabfile.file_size.setText, lambda x: human_readable_size(x))
            self.controls.config.setCurrentWidget(self.controls.tabfile.widget)
            self.controls.config.setVisible(True)
        elif object and isinstance(object, PartitionModel.Fasta):
            self.binder.bind(object.file_item.object.properties.size, self.controls.fasta.file_size.setText, lambda x: human_readable_size(x))
            self.binder.bind(object.properties.subset_filter, self.controls.fasta.filter_first.setChecked, lambda x: x == ColumnFilter.First)
            self.binder.bind(self.controls.fasta.filter_first.toggled, object.properties.subset_filter, lambda x: ColumnFilter.First if x else ColumnFilter.All)
            self.controls.config.setCurrentWidget(self.controls.fasta.widget)
            self.controls.config.setVisible(True)
        elif object and isinstance(object, PartitionModel.Spart):
            self.binder.bind(object.file_item.object.properties.size, self.controls.spart.file_size.setText, lambda x: human_readable_size(x))
            self.binder.bind(object.properties.is_xml, self.controls.spart.file_type.setText, lambda x: 'Spart-XML' if x else 'Spart')
            self.binder.bind(self.controls.spart.spartition.currentIndexChanged, object.properties.spartition, lambda x: self.controls.spart.spartition.itemData(x))
            self.binder.bind(object.properties.spartition, self.controls.spart.spartition.setCurrentIndex, lambda x: self.controls.spart.spartition.findText(x))
            self.populateSpartitions(object.file_item.object.info.spartitions)
            self.controls.config.setCurrentWidget(self.controls.spart.widget)
            self.controls.config.setVisible(True)
        else:
            self.controls.config.setVisible(False)

    def populateCombos(self, headers):
        self.controls.tabfile.subset_combo.clear()
        self.controls.tabfile.individual_combo.clear()
        for header in headers:
            self.controls.tabfile.subset_combo.addItem(header)
            self.controls.tabfile.individual_combo.addItem(header)

    def populateSpartitions(self, spartitions: list[str]):
        self.controls.spart.spartition.clear()
        for spartition in spartitions:
            self.controls.spart.spartition.addItem(spartition, spartition)


class AlignmentModeSelector(Card):
    resetScores = QtCore.Signal()
    modes = list(AlignmentMode)

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
        for mode in self.modes:
            button = RichRadioButton(f'{mode.label}:', mode.description, self)
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


class CrossAlignmentModeSelector(AlignmentModeSelector):
    modes = [AlignmentMode.PairwiseAlignment, AlignmentMode.AlignmentFree]
