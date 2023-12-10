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

from time import time_ns

from itaxotools.common.utility import Guard, override


class DarkWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""DarkWidget {background: Palette(Dark);}""")


class ScrollArea(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setContentsMargins(40, 0, 0, 0)
        self.setStyleSheet("""ScrollArea {border: none;}""")

    def setLayout(self, layout):
        widget = DarkWidget()
        widget.setLayout(layout)
        self.setWidget(widget)


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

        action = QtGui.QAction("&Copy", self)
        action.triggered.connect(self.copy)
        self.addAction(action)

        action = QtGui.QAction(self)
        action.setSeparator(True)
        self.addAction(action)

        action = QtGui.QAction("Select &All", self)
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
        self.buttons = QtWidgets.QButtonGroup()
        self.value = None

    def add(self, widget, value):
        self.members[widget] = value
        widget.toggled.connect(self.handleToggle)
        self.buttons.addButton(widget)

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
        self.setStyleSheet(
            """
            RichRadioButton {
                letter-spacing: 1px;
                font-weight: bold;
            }"""
        )
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

        x = self.size().width() / 2
        y = self.size().height() / 2
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
        degrees = -360 * ns / period_ns
        painter.setPen(QtGui.QPen(bold, self.width, QtCore.Qt.SolidLine))
        painter.drawArc(rect, degrees * 16, self.span * 16)

        painter.end()


class CategoryButton(QtWidgets.QAbstractButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred
        )
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
        # bold = palette.color(QtGui.QPalette.Shadow)

        color = weak if self.grayed else mild
        if self.grayed:
            painter.setPen(QtGui.QPen(mild, 1, QtCore.Qt.SolidLine))

        up_triangle = QtGui.QPolygon(
            [QtCore.QPoint(-6, 3), QtCore.QPoint(6, 3), QtCore.QPoint(0, -3)]
        )

        down_triangle = QtGui.QPolygon(
            [QtCore.QPoint(-6, -3), QtCore.QPoint(6, -3), QtCore.QPoint(0, 3)]
        )

        if self.isChecked():
            triangle = up_triangle
        else:
            triangle = down_triangle

        rect = QtCore.QRect(QtCore.QPoint(0, 0), self._fontSize())

        painter.drawText(
            rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.text()
        )

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


class MinimumStackedWidget(QtWidgets.QStackedWidget):
    def sizeHint(self):
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self):
        return self.currentWidget().sizeHint()


class DisplayFrame(QtWidgets.QFrame):
    def __init__(
        self, stretch=9, center_vertical=True, center_horizontal=True, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("DisplayFrame {background: Palette(dark);}")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(1, stretch)
        layout.setRowStretch(1, stretch)
        if center_horizontal:
            layout.setColumnStretch(0, 1)
            layout.setColumnStretch(2, 1)
        if center_vertical:
            layout.setRowStretch(0, 1)
            layout.setRowStretch(2, 1)
        self.setLayout(layout)

        self.widget = None

    def setWidget(self, widget):
        if self.widget is not None:
            self.widget.deleteLater()
        self.layout().addWidget(widget, 1, 1)
        self.widget = widget


class UnscrollableSpinBox(QtWidgets.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class UnscrollableDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()
