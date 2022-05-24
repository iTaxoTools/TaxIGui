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

from pathlib import Path

from itaxotools.common.utility import AttrDict

from .model import Object, Task, Sequence, BulkSequences, Dereplicate
from .sidebar import Item
from .dashboard import Dashboard


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.updateView()

    def updateView(self):
        pass


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: Palette(Shadow);""")


class SequenceView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: Palette(Dark);""")
        self.draw()

    def draw(self):
        self.draw_main_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.frame)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_main_card(self):
        frame = QtWidgets.QFrame(self)
        frame.setStyleSheet("""background: Palette(Midlight);""")
        label = QtWidgets.QLabel('')
        self.draw_buttons()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label, 1)
        layout.addLayout(self.buttons, 0)
        frame.setLayout(layout)
        self.frame = frame
        self.label = label

    def draw_buttons(self):
        open = QtWidgets.QPushButton('Open')
        inspect = QtWidgets.QPushButton('Inspect')
        remove = QtWidgets.QPushButton('Remove')

        open.clicked.connect(self.handleOpen)
        inspect.clicked.connect(self.handleInspect)
        remove.clicked.connect(self.handleRemove)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(open)
        layout.addWidget(inspect)
        layout.addWidget(remove)
        self.buttons = layout

    def setObject(self, object):
        if self.object:
            self.object.changed.disconnect(self.updateView)
        self.object = object
        self.object.changed.connect(self.updateView)
        self.updateView()

    def updateView(self):
        if not self.object:
            return
        self.label.setText(self.object.name)

    def handleOpen(self):
        print('open', self.object.name)

    def handleInspect(self):
        print('inspect', self.object.name)

    def handleRemove(self):
        print('remove', self.object.name)
        self.parent().removeActiveItem()


class BulkSequencesView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""background: Palette(Dark);""")
        self.draw()

    def draw(self):
        self.draw_main_card()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.frame)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def draw_main_card(self):
        frame = QtWidgets.QFrame(self)
        frame.setStyleSheet("""background: Palette(Midlight);""")
        self.draw_contents()
        self.draw_buttons()
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.contents, 1)
        layout.addLayout(self.buttons, 0)
        frame.setLayout(layout)
        self.frame = frame

    def draw_contents(self):
        self.label = QtWidgets.QLabel('')
        self.sequenceListView = QtWidgets.QListView(self)
        self.sequenceListView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.sequenceListView)

        self.contents = layout

    def draw_buttons(self):
        open = QtWidgets.QPushButton('Open')
        add = QtWidgets.QPushButton('Add')
        remove = QtWidgets.QPushButton('Remove')

        open.clicked.connect(self.handleOpen)
        add.clicked.connect(self.handleAdd)
        remove.clicked.connect(self.handleRemove)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(open)
        layout.addWidget(add)
        layout.addWidget(remove)
        layout.addStretch(1)
        self.buttons = layout

    def setObject(self, object):
        if self.object:
            self.object.changed.disconnect(self.updateView)
        self.object = object
        self.object.changed.connect(self.updateView)
        self.sequenceListView.setModel(self.object.sequenceModel)
        self.updateView()

    def updateView(self):
        if not self.object:
            return
        self.label.setText(self.object.name)

    def handleOpen(self):
        print('open', self.object, self.object.sequences)

    def handleAdd(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(self.window(), self.window().title)
        paths = [Path(filename) for filename in filenames]
        sequences = [Sequence(path) for path in paths]
        self.object.sequenceModel.add_sequences(sequences)

    def handleRemove(self):
        indexes = self.sequenceListView.selectedIndexes()
        self.object.sequenceModel.remove_sequences(indexes)
        if not self.object.sequences:
            self.parent().removeActiveItem()


class DereplicateView(ObjectView):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setStyleSheet("""DereplicateView{background: Palette(Dark);}""")
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
            frame = QtWidgets.QFrame(self)
            frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

            self.title = QtWidgets.QLabel('Dereplicate')
            self.title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

            self.description = QtWidgets.QLabel('Truncate similar sequences within the provided dataset.')
            self.description.setWordWrap(True)

            self.run = QtWidgets.QPushButton('Run')
            self.results = QtWidgets.QPushButton('Results')
            self.remove = QtWidgets.QPushButton('Remove')

            contents = QtWidgets.QVBoxLayout()
            contents.addWidget(self.title)
            contents.addWidget(self.description)
            contents.addStretch(1)

            buttons = QtWidgets.QVBoxLayout()
            buttons.addWidget(self.run)
            buttons.addWidget(self.results)
            buttons.addWidget(self.remove)
            buttons.addStretch(1)

            layout = QtWidgets.QHBoxLayout()
            layout.addLayout(contents, 1)
            layout.addLayout(buttons, 0)
            frame.setLayout(layout)
            return frame

        def draw_input_card(self):
            frame = QtWidgets.QFrame(self)
            frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

            label = QtWidgets.QLabel('Input Sequence')
            label.setStyleSheet("""font-size: 16px;""")

            sequence = QtWidgets.QComboBox()
            browse = QtWidgets.QPushButton('Import')

            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(label, 1)
            layout.addWidget(sequence)
            layout.addWidget(browse)
            frame.setLayout(layout)
            return frame

        def draw_distance_card(self):
            frame = QtWidgets.QFrame(self)
            frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

            label = QtWidgets.QLabel('Distance Calculation')
            label.setStyleSheet("""font-size: 16px;""")

            description = QtWidgets.QLabel('The method for calculating distances between sequences.')
            description.setWordWrap(True)

            free = QtWidgets.QRadioButton('Alignment-Free')
            pairwise = QtWidgets.QRadioButton('Pairwise Alignment')
            aligned = QtWidgets.QRadioButton('Already Aligned')

            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(description)
            layout.addWidget(free)
            layout.addWidget(pairwise)
            layout.addWidget(aligned)
            frame.setLayout(layout)
            return frame

        def draw_similarity_card(self):
            frame = QtWidgets.QFrame(self)
            frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

            label = QtWidgets.QLabel('Similarity Threshold (%)')
            label.setStyleSheet("""font-size: 16px;""")

            threshold = QtWidgets.QSpinBox()
            threshold.setMinimum(0)
            threshold.setMaximum(100)
            threshold.setSingleStep(1)
            threshold.setValue(7)
            threshold.setFixedWidth(80)

            description = QtWidgets.QLabel('Sequence pairs for which the uncorrected distance is below this threshold will be considered similar and will be truncated.')
            description.setWordWrap(True)

            layout = QtWidgets.QGridLayout()
            layout.addWidget(label, 0, 0)
            layout.addWidget(threshold, 0, 1)
            layout.addWidget(description, 1, 0)
            layout.setColumnStretch(0, 1)
            layout.setHorizontalSpacing(20)
            frame.setLayout(layout)
            return frame

        def draw_length_card(self):
            frame = QtWidgets.QFrame(self)
            frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

            label = QtWidgets.QCheckBox('Length Threshold')
            label.setStyleSheet("""font-size: 16px;""")

            threshold = QtWidgets.QLineEdit('0')
            threshold.setFixedWidth(80)

            description = QtWidgets.QLabel('Sequences with length below this threshold will be ignored (optional).')
            description.setWordWrap(True)

            layout = QtWidgets.QGridLayout()
            layout.addWidget(label, 0, 0)
            layout.addWidget(threshold, 0, 1)
            layout.addWidget(description, 1, 0)
            layout.setColumnStretch(0, 1)
            layout.setHorizontalSpacing(20)
            frame.setLayout(layout)
            return frame


class Body(QtWidgets.QStackedWidget):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.activeItem = None
        self.activeIndex = None
        self.views = dict()

        self.dashboard = Dashboard(self.model, self)
        self.addWidget(self.dashboard)

        self.addView(Task, TaskView)
        self.addView(Sequence, SequenceView)
        self.addView(BulkSequences, BulkSequencesView)
        self.addView(Dereplicate, DereplicateView)

    def addView(self, object_type, view_type):
        view = view_type(self)
        self.views[object_type] = view
        self.addWidget(view)

    def showItem(self, item: Item, index: QtCore.QModelIndex):
        self.activeItem = item
        self.activeIndex = index
        if not item or not index.isValid():
            self.showDashboard()
            return False
        object = item.object
        view = self.views.get(type(object))
        if not view:
            self.showDashboard()
            return False
        view.setObject(object)
        self.setCurrentWidget(view)
        return True

    def removeActiveItem(self):
        self.model.remove_index(self.activeIndex)

    def showDashboard(self):
        self.setCurrentWidget(self.dashboard)
