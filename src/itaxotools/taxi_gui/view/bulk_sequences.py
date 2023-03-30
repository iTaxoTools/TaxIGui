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

from itaxotools.common.utility import AttrDict

from .. import app
from ..model import SequenceListModel, SequenceModel
from .common import Card, ObjectView
from .sequence import SequenceReaderSelector


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
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(self.window(), app.title)
        paths = [Path(filename) for filename in filenames]
        sequences = [SequenceModel(path) for path in paths]
        self.object.model.add_sequences(sequences)

    def handleRemove(self):
        indexes = self.controls.view.selectedIndexes()
        self.object.model.remove_sequences(indexes)
        # if not self.object.sequences:
        #     self.parent().removeActiveItem()
