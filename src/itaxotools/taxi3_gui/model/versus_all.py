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


def dummy_process(**kwargs):
    for k, v in kwargs.items():
        print(k, v)
    import time
    print('...')
    time.sleep(2)
    print('Done!~')
    return 42


class VersusAllModel(Task):
    task_name = 'Versus All'

    input_sequences_item = Property(object)
    perform_species = Property(bool)
    perform_genera = Property(bool)

    def __init__(self, name=None):
        super().__init__(name, init=versus_all.initialize)
        self.input_sequences_item = None
        self.perform_species = True
        self.perform_genera = False

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def readyTriggers(self):
        return [
            self.properties.input_sequences_item,
        ]

    def isReady(self):
        if self.input_sequences_item is None:
            return False
        if not isinstance(self.input_sequences_item.object, SequenceModel):
            return False
        return True

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            dummy_process,
            work_dir=work_dir,
            input_sequences=self.input_sequences_item.object.path,
            perform_species=self.perform_species,
            perform_genera=self.perform_genera,
        )

    def onDone(self, results):
        self.done()
