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

from itaxotools.common.utility import override

from .. import app
from ..model import Item, ItemModel, Object
from ..types import ComparisonMode, PairwiseComparisonConfig
from ..utility import bind, unbind


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
        layout.setSpacing(24)
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


class SequenceSelector(Card):

    sequenceChanged = QtCore.Signal(Item)

    def __init__(self, text, parent=None, model=app.model.items):
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


class ComparisonModeSelector(Card):

    toggled = QtCore.Signal(ComparisonMode)
    edited = QtCore.Signal(str, int)

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
        for Mode in ComparisonMode:
            button = QtWidgets.QRadioButton(Mode.label)
            button.comparisonMode = Mode
            button.toggled.connect(self.handleToggle)
            self.radio_buttons.append(button)
            layout.addWidget(button)
        self.addLayout(layout)

        self.pairwise_config_panel = QtWidgets.QWidget()

        self.score_fields = dict()
        scores = QtWidgets.QGridLayout()
        validator = QtGui.QIntValidator()
        for i, (key, score) in enumerate(PairwiseComparisonConfig.scores.items()):
            label = QtWidgets.QLabel(f'{score.label}:')
            field = QtWidgets.QLineEdit()
            field.textEdited.connect(self.handleEdit)
            field.setFixedWidth(80)
            field.setValidator(validator)
            scores.addWidget(label, i // 2, (i % 2) * 4)
            scores.addWidget(field, i // 2, (i % 2) * 4 + 2)
            self.score_fields[key] = field
            field.scoreKey = key
        scores.setColumnMinimumWidth(1, 16)
        scores.setColumnMinimumWidth(5, 16)
        scores.setColumnStretch(3, 1)
        scores.setContentsMargins(0, 0, 0, 0)
        scores.setSpacing(8)

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('You may configure the pairwise comparison scores below.')
        reset = QtWidgets.QPushButton('Reset to default scores')
        reset.clicked.connect(self.handlePairwiseReset)
        layout.addWidget(label)
        layout.addLayout(scores)
        layout.addWidget(reset)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        self.pairwise_config_panel.setLayout(layout)
        self.addWidget(self.pairwise_config_panel)

        self.mode = ComparisonMode()

    def handleToggle(self, checked):
        if not checked:
            return
        for button in self.radio_buttons:
            if button.isChecked():
                self.mode = button.comparisonMode()
                self.toggled.emit(self.mode)

    def handleEdit(self, text):
        if self.mode.type is not ComparisonMode.PairwiseAlignment:
            return
        key = self.sender().scoreKey
        try:
            value = int(text)
        except ValueError:
            value = None
        self.mode.config[key] = value
        self.edited.emit(key, value)

    def handlePairwiseReset(self):
        mode = ComparisonMode.PairwiseAlignment()
        self.setComparisonMode(mode)

    def setComparisonMode(self, mode):
        self.mode = mode
        for button in self.radio_buttons:
            button.setChecked(mode.type is button.comparisonMode)
        if mode.type is ComparisonMode.PairwiseAlignment:
            for key, field in self.score_fields.items():
                value = mode.config[key]
                text = str(value) if value is not None else ''
                field.setText(text)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        is_pairwise = mode.type is ComparisonMode.PairwiseAlignment
        self.pairwise_config_panel.setVisible(is_pairwise)


class NoWheelSpinBox(QtWidgets.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()
