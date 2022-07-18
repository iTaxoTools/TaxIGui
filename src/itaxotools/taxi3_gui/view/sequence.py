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

from itaxotools.common.utility import AttrDict

from ..types import SequenceReader
from .common import Card, NoWheelComboBox, ObjectView


class SequenceReaderSelector(Card):

    toggled = QtCore.Signal(SequenceReader)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel('File Format')
        label.setStyleSheet("""font-size: 16px;""")

        combo = NoWheelComboBox()
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

        name = QtWidgets.QLabel('SequenceModel')
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
