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

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from ..tasks import versus_all
from ..types import ComparisonMode
from .common import Property, Task
from .sequence import SequenceModel


class VersusAllModel(Task):
    task_name = 'Versus All'

    comparison_mode = Property(ComparisonMode)
    input_item = Property(object)

    def __init__(self, name=None):
        super().__init__(name, init=versus_all.initialize)
        self.comparison_mode = ComparisonMode.AlignmentFree()
        self.input_item = None

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def readyTriggers(self):
        return [
            self.properties.input_item,
            self.properties.comparison_mode,
        ]

    def isReady(self):
        if self.input_item is None:
            return False
        if not isinstance(self.input_item.object, SequenceModel):
            return False
        if not self.comparison_mode.is_valid():
            return False
        return True

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        input = self.input_item.object.path

        self.exec(
            versus_all.versus_all, work_dir,
            input, self.comparison_mode,
        )

    def onDone(self, results):
        self.done()
