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


class Task:
    def __init__(self, name):
        self.name = name


class TaskModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()

        self.tasks = [
            Task('DEREP #1'),
            Task('DEREP #2'),
            Task('DEREP #3'),
            Task('DECONT #1'),
            Task('DECONT #2'),
        ]

    def rowCount(self, parent):
        return len(self.tasks)

    def data(self, index, role):
        if (
            role == QtCore.Qt.DisplayRole and
            index.row() >= 0 and
            index.row() < len(self.tasks) and
            index.column() == 0
        ):
            return self.tasks[index.row()].name
        else:
            return None


class TaskDelegate(QtWidgets.QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QtCore.QSize(256, 50)

    def paint(self, painter, option, index):
        # super().paint(painter, option, index)
        # print('flags', f'{int(option.state):b}', 'over', f'{int(QtWidgets.QStyle.State_MouseOver):b}')
        # return
        self.initStyleOption(option, index)

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillRect(option.rect, option.palette.light())
        else:
            painter.fillRect(option.rect, option.palette.mid())

        textRect = QtCore.QRect(option.rect)
        text = index.data(QtCore.Qt.DisplayRole)
        painter.drawText(textRect, text)

    ### CLICKABLE REGIONS:
    ### https://forum.qt.io/topic/28142/detect-clicked-icon-of-item-solved/5
    # def editorEvent(self, event, model, option, index):
    #     print(event)
    #     return super().event(event)

class TaskView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            TaskView {
                background: palette(Midlight);
                border: 0px solid transparent;
                border-right: 1px solid palette(Mid);
            }
        """)
        self.setSpacing(2)
        self.delegate = TaskDelegate()
        self.setItemDelegate(self.delegate)

    def sizeHint(self):
        w = self.sizeHintForColumn(0) + 1
        h = self.sizeHintForRow(0)
        return QtCore.QSize(w, h)


class SideBar(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.taskModel = TaskModel()
        self.taskView = TaskView()
        self.taskView.setModel(self.taskModel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.taskView)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
