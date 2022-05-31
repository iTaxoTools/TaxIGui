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

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from .dashboard import Dashboard
from .model import (
    Object, Task, Sequence, BulkSequences, Dereplicate, Decontaminate,
    AlignmentType, SequenceReader, Item, ItemModel, SequenceListModel,
    DecontaminateMode, NotificationType, bind, unbind)


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.bindings = set()
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.updateView()

    def updateView(self):
        pass

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


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""TaskView{background: Palette(Shadow);}""")


class Card(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(16)
        self.setLayout(layout)

    def addWidget(self, widget):
        self.layout().addWidget(widget)

    def addLayout(self, widget):
        self.layout().addLayout(widget)

    @override
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.layout().count():
            self.paintSeparators()

    def paintSeparators(self):
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        painter.setPen(option.palette.color(QtGui.QPalette.Mid))

        layout = self.layout()
        frame = layout.contentsRect()
        left = frame.left()
        right = frame.right()

        items = [
            item for item in (layout.itemAt(id) for id in range(0, layout.count()))
            if item.widget() and item.widget().isVisible()
            or item.layout()
        ]
        pairs = zip(items[:-1], items[1:])

        for first, second in pairs:
            bottom = first.geometry().bottom()
            top = second.geometry().top()
            middle = (bottom + top) / 2
            painter.drawLine(left, middle, right, middle)


class SequenceReaderSelector(Card):

    toggled = QtCore.Signal(SequenceReader)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('File Format')
        label.setStyleSheet("""font-size: 16px;""")

        combo = QtWidgets.QComboBox()
        combo.setFixedWidth(160)
        for reader in SequenceReader:
            combo.addItem(str(reader), reader)
        combo.currentIndexChanged.connect(self.handleIndexChanged)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(combo)
        self.addLayout(layout)

        self.combo = combo

    def handleIndexChanged(self, index):
        value = self.combo.currentData()
        self.toggled.emit(value)

    def setSequenceReader(self, reader):
        index = self.combo.findData(reader)
        self.combo.setCurrentIndex(index)


class SourceLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textalignment = QtCore.Qt.AlignLeft | QtCore.Qt.TextWrapAnywhere

    def setText(self, text):
        for char in r'\/':
            text = text.replace(char, f"{char}\u200b")
        super().setText(text)


class SequenceView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        main = self.draw_main_card()
        selector = self.draw_selector_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(main)
        layout.addWidget(selector)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_main_card(self):
        card = Card(self)

        name = QtWidgets.QLabel('Sequence')
        name.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        source = SourceLabel('...')
        source.setWordWrap(True)

        open = QtWidgets.QPushButton('Open')
        inspect = QtWidgets.QPushButton('Inspect')
        remove = QtWidgets.QPushButton('Remove')

        open.clicked.connect(self.handleOpen)
        inspect.clicked.connect(self.handleInspect)
        remove.clicked.connect(self.handleRemove)

        inspect.setEnabled(False)
        remove.setEnabled(False)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(name)
        contents.addSpacing(8)
        contents.addWidget(source)
        contents.addStretch(1)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(open)
        buttons.addWidget(inspect)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        card.addLayout(layout)

        self.controls.name = name
        self.controls.source = source
        self.controls.open = open
        self.controls.inspect = inspect
        self.controls.remove = remove
        return card

    def draw_selector_card(self):
        card = SequenceReaderSelector(self)
        self.controls.reader = card
        return card

    def setObject(self, object):
        self.object = object

        self.unbind_all()

        self.bind(object.properties.name, self.controls.name.setText)
        self.bind(object.properties.path, self.controls.source.setText, lambda x: str(x))
        self.bind(object.properties.reader, self.controls.reader.setSequenceReader)
        self.bind(self.controls.reader.toggled, object.properties.reader)

    def handleOpen(self):
        print('open', self.object.name, str(self.object.path))
        url = QtCore.QUrl.fromLocalFile(str(self.object.path))
        QtGui.QDesktopServices.openUrl(url)

    def handleInspect(self):
        print('inspect', self.object.name)

    def handleRemove(self):
        print('remove', self.object.name)
        self.parent().parent().parent().removeActiveItem()


class BulkSequencesView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        main = self.draw_main_card()
        selector = self.draw_selector_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(main)
        layout.addWidget(selector)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_main_card(self):
        card = Card(self)

        name = QtWidgets.QLabel('Bulk Sequences')
        name.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        view = QtWidgets.QListView(self)
        view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        view.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)

        open = QtWidgets.QPushButton('Open')
        add = QtWidgets.QPushButton('Add')
        remove = QtWidgets.QPushButton('Remove')

        open.clicked.connect(self.handleOpen)
        add.clicked.connect(self.handleAdd)
        remove.clicked.connect(self.handleRemove)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(name)
        contents.addSpacing(8)
        contents.addWidget(view)
        contents.addStretch(1)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(open)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        card.addLayout(layout)

        self.controls.name = name
        self.controls.view = view
        self.controls.open = open
        self.controls.add = add
        self.controls.remove = remove
        return card

    def draw_selector_card(self):
        frame = SequenceReaderSelector(self)
        self.controls.reader = frame
        return frame

    def setObject(self, object):
        self.object = object

        self.unbind_all()

        self.bind(object.properties.name, self.controls.name.setText)
        self.bind(object.properties.reader, self.controls.reader.setSequenceReader)
        self.bind(self.controls.reader.toggled, object.properties.reader)

        self.controls.view.setModel(object.model)

    def handleOpen(self):
        index = self.controls.view.currentIndex()
        path = index.data(SequenceListModel.PathRole)
        print('open', str(path))
        url = QtCore.QUrl.fromLocalFile(str(path))
        QtGui.QDesktopServices.openUrl(url)

    def handleAdd(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(self.window(), self.window().title)
        paths = [Path(filename) for filename in filenames]
        sequences = [Sequence(path) for path in paths]
        self.object.model.add_sequences(sequences)

    def handleRemove(self):
        indexes = self.controls.view.selectedIndexes()
        self.object.model.remove_sequences(indexes)
        # if not self.object.sequences:
        #     self.parent().removeActiveItem()


class AlignmentTypeSelector(Card):

    toggled = QtCore.Signal(AlignmentType)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('Sequence comparison mode')
        label.setStyleSheet("""font-size: 16px;""")

        description = QtWidgets.QLabel(
            'Choose which method to use to compare sequences, '
            'either by alignment-free distances, by calculating distances '
            'between sequences after performing pairwise alignment, or '
            'by calculating distances between already aligned sequences.')
        description.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(description)
        layout.setSpacing(8)

        self.radio_buttons = list()
        for type in AlignmentType:
            button = QtWidgets.QRadioButton(str(type))
            button.alignment_type = type
            button.toggled.connect(self.handleToggle)
            self.radio_buttons.append(button)
            layout.addWidget(button)

        self.addLayout(layout)

    def handleToggle(self, checked):
        if not checked:
            return
        for button in self.radio_buttons:
            if button.isChecked():
                self.toggled.emit(button.alignment_type)

    def setAlignmentType(self, type):
        for button in self.radio_buttons:
            button.setChecked(button.alignment_type == type)


class SequenceSelector(Card):

    sequenceChanged = QtCore.Signal(Item)

    def __init__(self, text, model, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel(text)
        label.setStyleSheet("""font-size: 16px;""")

        combo = QtWidgets.QComboBox()
        combo.setFixedWidth(180)
        combo.setModel(model)
        combo.setRootModelIndex(model.sequences_index)
        combo.currentIndexChanged.connect(self.handleIndexChanged)

        browse = QtWidgets.QPushButton('Import')
        browse.setEnabled(False)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label, 1)
        layout.addWidget(combo)
        layout.addWidget(browse)
        self.addLayout(layout)

        self.combo = combo

    def handleIndexChanged(self, row):
        if row < 0:
            item = None
        else:
            model = self.combo.model()
            parent = model.sequences_index
            index = model.index(row, 0, parent)
            item = index.data(ItemModel.ItemRole)
        self.sequenceChanged.emit(item)

    def setSequenceItem(self, item):
        row = item.row if item else -1
        self.combo.setCurrentIndex(row)


class NoWheelSpinBox(QtWidgets.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class DereplicateView(ObjectView):

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.controls = AttrDict()
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = self.draw_title_card()
        self.cards.input = self.draw_input_card()
        self.cards.distance = self.draw_distance_card()
        self.cards.similarity = self.draw_similarity_card()
        self.cards.length = self.draw_length_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.cards.title)
        layout.addWidget(self.cards.input)
        layout.addWidget(self.cards.distance)
        layout.addWidget(self.cards.similarity)
        layout.addWidget(self.cards.length)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_title_card(self):
        card = Card(self)

        title = QtWidgets.QLabel('Dereplicate')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel(
            'Remove sequences that are identical or similar to other '
            'sequences in the dataset.')
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
        card = SequenceSelector('Input Sequence:', self.model, self)
        self.controls.inputItem = card
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
            'Sequence pairs for which the uncorrected distance is below '
            'this threshold will be considered similar and will be truncated.')
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
        self.cards.distance.setEnabled(not busy)
        self.cards.similarity.setEnabled(not busy)
        self.cards.length.setEnabled(not busy)

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

        self.bind(object.properties.length_threshold, self.controls.lengthThreshold.setText, lambda x: str(x))
        self.bind(self.controls.lengthThreshold.textChanged, object.properties.length_threshold, lambda x: int(x))

        self.bind(object.properties.alignment_type, self.controls.alignmentTypeSelector.setAlignmentType)
        self.bind(self.controls.alignmentTypeSelector.toggled, object.properties.alignment_type)

        self.bind(object.properties.input_item, self.controls.inputItem.setSequenceItem)
        self.bind(self.controls.inputItem.sequenceChanged, object.properties.input_item)

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

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
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
        card = SequenceSelector('Input Sequence(s):', self.model, self)
        self.controls.inputItem = card
        return card

    def draw_mode_card(self):
        card = DecontaminateModeSelector(self)
        self.controls.mode = card
        return card

    def draw_ref1_card(self):
        card = SequenceSelector('Reference 1 (outgroup):', self.model, self)
        self.controls.referenceItem1 = card
        return card

    def draw_ref2_card(self):
        card = SequenceSelector('Reference 2 (ingroup):', self.model, self)
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


class ScrollArea(QtWidgets.QScrollArea):

    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setWidget(widget)


class Body(QtWidgets.QStackedWidget):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.activeItem = None
        self.activeIndex = None
        self.areas = dict()

        self.dashboard = Dashboard(self.model, self)
        self.addWidget(self.dashboard)

        self.addView(Task, TaskView)
        self.addView(Sequence, SequenceView)
        self.addView(BulkSequences, BulkSequencesView)
        self.addView(Dereplicate, DereplicateView, model=model)
        self.addView(Decontaminate, DecontaminateView, model=model)

    def addView(self, object_type, view_type, *args, **kwargs):
        view = view_type(parent=self, *args, **kwargs)
        area = ScrollArea(view, self)
        self.areas[object_type] = area
        self.addWidget(area)

    def showItem(self, item: Item, index: QtCore.QModelIndex):
        self.activeItem = item
        self.activeIndex = index
        if not item or not index.isValid():
            self.showDashboard()
            return False
        object = item.object
        area = self.areas.get(type(object))
        if not area:
            self.showDashboard()
            return False
        view = area.widget()
        view.setObject(object)
        self.setCurrentWidget(area)
        area.ensureVisible(0, 0)
        return True

    def removeActiveItem(self):
        self.model.remove_index(self.activeIndex)

    def showDashboard(self):
        self.setCurrentWidget(self.dashboard)
