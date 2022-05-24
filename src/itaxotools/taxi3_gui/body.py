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

from itaxotools.common.utility import AttrDict

from .model import Object, Task, Sequence, BulkSequences, Dereplicate, AlignmentType
from .sidebar import Item
from .dashboard import Dashboard


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.updateView()

    def updateView(self):
        pass


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""TaskView{background: Palette(Shadow);}""")


class SequenceView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")
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
        frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")
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
        self.sequenceListView.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)

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
        self.draw()

    def draw(self):
        self.controls = AttrDict()
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

        title = QtWidgets.QLabel('Dereplicate')
        title.setStyleSheet("""font-size: 18px; font-weight: bold; """)

        description = QtWidgets.QLabel('Truncate similar sequences within the provided dataset.')
        description.setWordWrap(True)

        run = QtWidgets.QPushButton('Run')
        results = QtWidgets.QPushButton('Results')
        remove = QtWidgets.QPushButton('Remove')

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(title)
        contents.addWidget(description)
        contents.addStretch(1)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(run)
        buttons.addWidget(results)
        buttons.addWidget(remove)
        buttons.addStretch(1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(contents, 1)
        layout.addLayout(buttons, 0)
        frame.setLayout(layout)

        self.controls.title = title
        self.controls.description = description
        self.controls.run = run
        self.controls.results = results
        self.controls.remove = remove
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

        free.toggled.connect(self.setAlignmentType)
        pairwise.toggled.connect(self.setAlignmentType)
        aligned.toggled.connect(self.setAlignmentType)
        self.controls.free = free
        self.controls.pairwise = pairwise
        self.controls.aligned = aligned
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

        threshold.valueChanged.connect(self.setSimilarityThreshold)
        self.controls.similarityThreshold = threshold
        return frame

    def draw_length_card(self):
        frame = QtWidgets.QFrame(self)
        frame.setStyleSheet("""QFrame{background: Palette(Midlight);}""")

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
        frame.setLayout(layout)

        threshold.textChanged.connect(self.setLengthThreshold)
        self.controls.lengthThreshold = threshold
        return frame

    def getName(self):
        if not self.object:
            return
        if getattr(self, '_flag_name', False):
            return
        print('getName')
        value = self.object.name
        self.controls.title.setText(value)

    def setSimilarityThreshold(self, value):
        if not self.object:
            return
        print('setSimilarityThreshold')
        value = value / 100
        if self.object.similarity_threshold == value:
            return
        setattr(self, '_flag_similarity_threshold', True)
        self.object.similarity_threshold = value
        setattr(self, '_flag_similarity_threshold', False)

    def getSimilarityThreshold(self):
        if not self.object:
            return
        if getattr(self, '_flag_similarity_threshold', False):
            return
        print('getSimilarityThreshold')
        value = self.object.similarity_threshold
        self.controls.similarityThreshold.setValue(round(value * 100))

    def setLengthThreshold(self, text):
        if not self.object:
            return
        print('setLengthThreshold')
        value = int(text)
        if self.object.length_threshold == value:
            return
        setattr(self, '_flag_length_threshold', True)
        self.object.length_threshold = value
        setattr(self, '_flag_length_threshold', False)

    def getLengthThreshold(self):
        if not self.object:
            return
        if getattr(self, '_flag_length_threshold', False):
            return
        print('getLengthThreshold')
        value = self.object.length_threshold
        self.controls.lengthThreshold.setText(str(value))

    def setAlignmentType(self, checked):
        if not self.object:
            return
        if not checked:
            return
        print('setAlignmentType')
        value = AlignmentType.AlignmentFree
        if self.controls.free.isChecked():
            value = AlignmentType.AlignmentFree
        elif self.controls.pairwise.isChecked():
            value = AlignmentType.PairwiseAlignment
        elif self.controls.aligned.isChecked():
            value = AlignmentType.AlreadyAligned
        if self.object.alignment_type == value:
            return
        setattr(self, '_flag_alignment_type', True)
        self.object.alignment_type = value
        setattr(self, '_flag_alignment_type', False)

    def getAlignmentType(self):
        if not self.object:
            return
        if getattr(self, '_flag_alignment_type', False):
            return
        print('getAlignmentType')
        value = self.object.alignment_type
        self.controls.free.setChecked(value == AlignmentType.AlignmentFree)
        self.controls.pairwise.setChecked(value == AlignmentType.PairwiseAlignment)
        self.controls.aligned.setChecked(value == AlignmentType.AlreadyAligned)

    def setObject(self, object):
        print('setObject', object, id(object))
        if self.object:
            self.object.changed.disconnect(self.getSimilarityThreshold)
            self.object.changed.disconnect(self.getLengthThreshold)
            self.object.changed.disconnect(self.getAlignmentType)
            self.object.changed.disconnect(self.getName)
        self.object = object
        self.object.changed.connect(self.getSimilarityThreshold)
        self.object.changed.connect(self.getLengthThreshold)
        self.object.changed.connect(self.getAlignmentType)
        self.object.changed.connect(self.getName)
        self.getSimilarityThreshold()
        self.getLengthThreshold()
        self.getAlignmentType()
        self.getName()
    #     self.object.changed.connect(self.updateView)
    #     self.updateView()
    #
    # def updateView(self):
    #     if not self.object:
    #         return
    #     self.title.setText(self.object.name)


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
        self.addView(Dereplicate, DereplicateView)

    def addView(self, object_type, view_type):
        view = view_type(self)
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
