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

from PySide6 import QtCore, QtWidgets, QtGui

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.utility import Guard, Binder, type_convert, human_readable_size
from itaxotools.taxi_gui.types import ColumnFilter, Notification, AlignmentMode, PairwiseComparisonConfig, StatisticsGroup, AlignmentMode, PairwiseScore, DistanceMetric
from itaxotools.taxi_gui.view.cards import Card, CardCustom
from itaxotools.taxi_gui.view.widgets import GLineEdit, GSpinBox, RadioButtonGroup, RichRadioButton, MinimumStackedWidget, NoWheelComboBox
from itaxotools.taxi_gui.view.animations import VerticalRollAnimation
from itaxotools.taxi_gui.view.cards import Card
from itaxotools.taxi_gui.view.tasks import TaskView
from itaxotools.taxi_gui.model.common import Item, ItemModel, Object
from itaxotools.taxi_gui.model.sequence import SequenceModel
from itaxotools.taxi_gui.model.input_file import InputFileModel
from itaxotools.taxi_gui.model.partition import PartitionModel


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

        title = QtWidgets.QLabel('Versus All')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Derive statistics from the distance betweens all pairs of sequences.')
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

        parse_organism = QtWidgets.QCheckBox('Parse identifiers as "sequence|taxon"')

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
        label = QtWidgets.QLabel('Distance metrics')
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


class PlotSelector(Card):

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QtWidgets.QCheckBox('Generate histogram plots')
        title.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Plot histograms of the distribution of sequence distances across species/genera. '
            'You may customize the width of the bins across the horizontal axis (from 0.0 to 1.0).'
        )
        description.setWordWrap(True)

        label = QtWidgets.QLabel('Bin width:')
        binwidth = GLineEdit('')
        binwidth.setValidator(QtGui.QDoubleValidator())
        binwidth.setPlaceholderText('0.05')

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


class View(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.dummy_results = DummyResultsCard(self)
        self.cards.progress = ProgressCard(self)
        self.cards.input_sequences = SequenceSelector('Input sequences', self)
        self.cards.perform_species = OptionalCategory(
            'Perform species analysis',
            'Calculate various metrics betweens all pairs of species (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_species = PartitionSelector('Species partition', 'Species', 'Individuals', self)
        self.cards.perform_genera = OptionalCategory(
            'Perform genus analysis',
            'Calculate various metrics betweens all pairs of genera (mean/min/max), '
            'based on the distances between their member specimens.',
            self)
        self.cards.input_genera = PartitionSelector('Genera partition', 'Genera', 'Individuals', self)
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

        self.binder.bind(self.cards.title.run, object.start)
        self.binder.bind(self.cards.title.cancel, object.stop)
        self.binder.bind(object.properties.name, self.cards.title.setTitle)
        self.binder.bind(object.properties.ready, self.cards.title.setReady)
        self.binder.bind(object.properties.busy_main, self.cards.title.setBusy)
        self.binder.bind(object.properties.busy_main, self.cards.progress.setEnabled)
        self.binder.bind(object.properties.busy_main, self.cards.progress.setVisible)
        self.binder.bind(object.properties.busy_sequence, self.cards.input_sequences.setBusy)
        self.binder.bind(object.properties.busy_species, self.cards.input_species.setBusy)
        self.binder.bind(object.properties.busy_genera, self.cards.input_genera.setBusy)

        self.binder.bind(self.cards.input_sequences.itemChanged, object.set_sequence_file_from_file_item)
        self.binder.bind(object.properties.input_sequences, self.cards.input_sequences.setObject)
        self.binder.bind(self.cards.input_sequences.addInputFile, object.add_sequence_file)

        self.binder.bind(self.cards.perform_species.toggled, object.properties.perform_species)
        self.binder.bind(object.properties.perform_species, self.cards.perform_species.setChecked)
        self.binder.bind(object.properties.perform_species, self.cards.input_species.roll_animation.setAnimatedVisible)

        self.binder.bind(self.cards.input_species.itemChanged, object.set_species_file_from_file_item)
        self.binder.bind(object.properties.input_species, self.cards.input_species.setObject)
        self.binder.bind(self.cards.input_species.addInputFile, object.add_species_file)

        self.binder.bind(self.cards.perform_genera.toggled, object.properties.perform_genera)
        self.binder.bind(object.properties.perform_genera, self.cards.perform_genera.setChecked)
        self.binder.bind(object.properties.perform_genera, self.cards.input_genera.roll_animation.setAnimatedVisible)

        self.binder.bind(self.cards.input_genera.itemChanged, object.set_genera_file_from_file_item)
        self.binder.bind(object.properties.input_genera, self.cards.input_genera.setObject)
        self.binder.bind(self.cards.input_genera.addInputFile, object.add_genera_file)

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

        for key in (metric.key for metric in DistanceMetric):
            self.binder.bind(self.cards.distance_metrics.controls.metrics[key].toggled, object.distance_metrics.properties[key])
            self.binder.bind(object.distance_metrics.properties[key], self.cards.distance_metrics.controls.metrics[key].setChecked)

        self.binder.bind(self.cards.distance_metrics.controls.bbc_k.textEditedSafe, object.distance_metrics.properties.bbc_k, lambda x: type_convert(x, int, None))
        self.binder.bind(object.distance_metrics.properties.bbc_k, self.cards.distance_metrics.controls.bbc_k.setText, lambda x: str(x) if x is not None else '')
        self.binder.bind(object.distance_metrics.properties.bbc, self.cards.distance_metrics.controls.bbc_k.setEnabled)
        self.binder.bind(object.distance_metrics.properties.bbc, self.cards.distance_metrics.controls.bbc_k_label.setEnabled)

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

        for group in StatisticsGroup:
            self.binder.bind(self.cards.stats_options.controls[group.key].toggled, object.statistics_groups.properties[group.key])
            self.binder.bind(object.statistics_groups.properties[group.key], self.cards.stats_options.controls[group.key].setChecked)

        self.binder.bind(object.properties.plot_histograms, self.cards.plot_options.controls.plot.setChecked)
        self.binder.bind(object.properties.plot_binwidth, self.cards.plot_options.controls.binwidth.setText, lambda x: str(x) if x is not None else '')
        self.binder.bind(self.cards.plot_options.controls.plot.toggled, object.properties.plot_histograms)
        self.binder.bind(self.cards.plot_options.controls.binwidth.textEditedSafe, object.properties.plot_binwidth, lambda x: type_convert(x, float, None))

        self.binder.bind(object.properties.dummy_results, self.cards.dummy_results.setPath)
        self.binder.bind(object.properties.dummy_results, self.cards.dummy_results.roll_animation.setAnimatedVisible,  lambda x: x is not None)

        self.binder.bind(object.properties.editable, self.setEditable)

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
