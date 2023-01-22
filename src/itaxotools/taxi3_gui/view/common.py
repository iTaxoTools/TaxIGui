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

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from .. import app
from ..model import BulkSequencesModel, Item, ItemModel, Object, SequenceModel
from ..types import ComparisonMode, Notification, PairwiseComparisonConfig
from ..utility import Guard, Binder


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.binder = Binder()
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.binder.unbind_all()
        self.binder.bind(object.notification, self.showNotification)

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
        self.window().msgShow(msgBox)

    def getOpenPath(self, caption='Open File', dir='', filter=''):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f'{app.title} - {caption}', dir, filter=filter)
        if not filename:
            return None
        return Path(filename)

    def getSavePath(self, caption='Open File', dir=''):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)

    def getExistingDirectory(self, caption='Open File', dir=''):
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)

    def getConfirmation(self, title='Confirmation', text='Are you sure?'):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(f'{app.title} - {title}')
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText(text)
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = self.window().msgShow(msgBox)
        return confirm == QtWidgets.QMessageBox.Yes


class TaskView(ObjectView):

    def start(self):
        self.object.start()

    def stop(self):
        if self.getConfirmation(
            'Stop diagnosis',
            'Are you sure you want to stop the ongoing diagnosis?'
        ):
            self.object.stop()

    def save(self):
        path = self.getExistingDirectory(
            'Save All', str(self.object.suggested_directory))
        if path:
            self.object.save_all(path)

    def clear(self):
        if self.getConfirmation(
            'Clear results',
            'Are you sure you want to clear all results and try again?'
        ):
            self.object.clear()


class Card(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")
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


class NoWheelComboBox(QtWidgets.QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class GLineEdit(QtWidgets.QLineEdit):
    textEditedSafe = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textEdited.connect(self._handleEdit)
        self._guard = Guard()

    def _handleEdit(self, text):
        with self._guard:
            self.textEditedSafe.emit(text)

    @override
    def setText(self, text):
        if self._guard:
            return
        super().setText(text)


class GSpinBox(QtWidgets.QSpinBox):

    valueChangedSafe = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valueChanged.connect(self._handleEdit)
        self._guard = Guard()

    def _handleEdit(self, value):
        with self._guard:
            self.valueChangedSafe.emit(value)

    @override
    def setValue(self, value):
        if self._guard:
            return
        super().setValue(value)

    @override
    def wheelEvent(self, event):
        event.ignore()


class LongLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setWordWrap(True)

        action = QtGui.QAction('&Copy', self)
        action.triggered.connect(self.copy)
        self.addAction(action)

        action = QtGui.QAction(self)
        action.setSeparator(True)
        self.addAction(action)

        action = QtGui.QAction('Select &All', self)
        action.triggered.connect(self.select)
        self.addAction(action)

    def copy(self):
        text = self.selectedText()
        QtWidgets.QApplication.clipboard().setText(text)

    def select(self):
        self.setSelection(0, len(self.text()))


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


class NoWheelRadioButton(QtWidgets.QRadioButton):
    # Fix scrolling when hovering disabled button
    def event(self, event):
        if isinstance(event, QtGui.QWheelEvent):
            event.ignore()
            return False
        return super().event(event)


class RichRadioButton(NoWheelRadioButton):
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


class SpinningCircle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.handleTimer)
        self.timerStep = 10
        self.radius = 8
        self.period = 2
        self.span = 120
        self.width = 2

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.start()
        else:
            self.stop()

    def start(self):
        self.timer.start(self.timerStep)

    def stop(self):
        self.timer.stop()

    def handleTimer(self):
        self.repaint()

    def sizeHint(self):
        diameter = (self.radius + self.width) * 2
        return QtCore.QSize(diameter, diameter)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtCore.Qt.NoBrush)

        x = self.size().width()/2
        y = self.size().height()/2
        painter.translate(QtCore.QPoint(x, y))

        palette = QtGui.QGuiApplication.palette()
        weak = palette.color(QtGui.QPalette.Mid)
        bold = palette.color(QtGui.QPalette.Shadow)

        rad = self.radius
        rect = QtCore.QRect(-rad, -rad, 2 * rad, 2 * rad)

        painter.setPen(QtGui.QPen(weak, self.width, QtCore.Qt.SolidLine))
        painter.drawEllipse(rect)

        period_ns = int(self.period * 10**9)
        ns = time_ns() % period_ns
        degrees = - 360 * ns / period_ns
        painter.setPen(QtGui.QPen(bold, self.width, QtCore.Qt.SolidLine))
        painter.drawArc(rect, degrees * 16, self.span * 16)

        painter.end()


class CategoryButton(QtWidgets.QAbstractButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)
        self.setCheckable(True)
        self.setText(text)
        self.hovered = False
        self.triangle_pixels = 38
        self.grayed = False

        self.toggled.connect(self.handleChecked)

    def setGray(self, gray):
        self.grayed = gray

    def enterEvent(self, event):
        self.hovered = True

    def leaveEvent(self, event):
        self.hovered = False

    def handleChecked(self, checked):
        self.checked = checked

    def _fontSize(self):
        return self.fontMetrics().size(QtCore.Qt.TextSingleLine, self.text())

    def sizeHint(self):
        return self._fontSize() + QtCore.QSize(self.triangle_pixels, 0)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)

        palette = QtGui.QGuiApplication.palette()
        weak = palette.color(QtGui.QPalette.Mid)
        mild = palette.color(QtGui.QPalette.Dark)
        bold = palette.color(QtGui.QPalette.Shadow)

        color = weak if self.grayed else bold
        if self.grayed:
            painter.setPen(QtGui.QPen(mild, 1, QtCore.Qt.SolidLine))

        up_triangle = QtGui.QPolygon([
            QtCore.QPoint(-6, 3),
            QtCore.QPoint(6, 3),
            QtCore.QPoint(0, -3)])

        down_triangle = QtGui.QPolygon([
            QtCore.QPoint(-6, -3),
            QtCore.QPoint(6, -3),
            QtCore.QPoint(0, 3)])

        if self.isChecked():
            triangle = up_triangle
        else:
            triangle = down_triangle

        rect = QtCore.QRect(QtCore.QPoint(0, 0), self._fontSize())

        painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.text())

        if self.hovered:
            painter.save()
            painter.translate(0, -1)
            painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.SolidLine))
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.restore()

        painter.save()
        painter.translate(self._fontSize().width(), self._fontSize().height() / 2)
        painter.translate(self.triangle_pixels / 2, 1)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(color))
        painter.drawPolygon(triangle)
        painter.restore()

        painter.end()
