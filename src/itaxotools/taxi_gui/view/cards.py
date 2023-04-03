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

from itaxotools.common.utility import AttrDict, override

from .. import app
from ..model.common import Item, ItemModel
from ..types import ComparisonMode, PairwiseComparisonConfig
from . animations import VerticalRollAnimation


class CardLayout(QtWidgets.QBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(QtWidgets.QBoxLayout.TopToBottom)
        # self.setContentsMargins(8, 8, 8, 8)

    def expandingDirections(self):
        return QtCore.Qt.Vertical

    def hasHeightForWidth(self):
        return False

    def setGeometry(self, rect):
        super().setGeometry(rect)

        margins = self.contentsMargins()
        rect.adjust(margins.left(), margins.top(), -margins.right(), -margins.bottom())

        width = rect.width()
        height = rect.height()
        yy_incr = height / self.count()
        xx = rect.x()
        yy = rect.y()
        for index in range(self.count()):
            item = self.itemAt(index)
            item_rect = QtCore.QRect(xx, yy, width, yy_incr)
            if isinstance(item, QtWidgets.QWidget) and not item.isVisible():
                continue
            if isinstance(item, QtWidgets.QWidgetItem) and not item.widget().isVisible():
                continue
            item_rect.setHeight(item.sizeHint().height())
            item.setGeometry(item_rect)
            yy += item.sizeHint().height()
            yy += self.spacing()

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        width = 0
        height = 0
        visible = 0
        for index in range(self.count()):
            item = self.itemAt(index)
            if isinstance(item, QtWidgets.QWidget) and not item.isVisible():
                continue
            if isinstance(item, QtWidgets.QWidgetItem) and not item.widget().isVisible():
                continue
            visible += 1
            width = max(width, item.sizeHint().width())
            height += item.sizeHint().height()
        if visible > 1:
            height += (visible - 1) * self.spacing()
        size = QtCore.QSize(width, height)

        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

        return size


class Card(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")
        self.roll_animation = VerticalRollAnimation(self)
        self.controls = AttrDict()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(16, 10, 16, 10)
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


class CardCustom(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""CardCustom{background: Palette(Midlight);}""")
        self.roll_animation = VerticalRollAnimation(self)
        self.controls = AttrDict()

        layout = CardLayout()
        layout.setContentsMargins(16, 10, 16, 10)
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

        combo = NoWheelComboBox()
        combo.setFixedWidth(180)
        combo.setModel(model)
        combo.setRootModelIndex(model.sequences_index)
        combo.currentIndexChanged.connect(self.handleIndexChanged)

        browse = QtWidgets.QPushButton('Import')
        browse.clicked.connect(self.handleImport)

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

    def handleImport(self, *args):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self.window(), f'{app.title} - Import Sequence(s)')
        if not filenames:
            return
        if len(filenames) == 1:
            path = Path(filenames[0])
            index = app.model.items.add_sequence(SequenceModel(path), focus=False)
        else:
            paths = [Path(filename) for filename in filenames]
            index = app.model.items.add_sequence(BulkSequencesModel(paths), focus=False)
        item = index.data(ItemModel.ItemRole)
        self.setSequenceItem(item)


class ComparisonModeSelector(Card):

    toggled = QtCore.Signal(ComparisonMode)
    edited = QtCore.Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addLayout(self.draw_main_selector())
        self.addWidget(self.draw_pairwise_config())
        self.mode = ComparisonMode()

    def draw_main_selector(self):
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
        return layout

    def draw_pairwise_config(self):
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
        return self.pairwise_config_panel

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
        self.toggled.emit(mode)

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
