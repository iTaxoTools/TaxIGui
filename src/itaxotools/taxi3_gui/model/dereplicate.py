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

from .. import app
from ..tasks import dereplicate
from ..types import ComparisonMode
from .bulk_sequences import BulkSequencesModel
from .common import Property, Task
from .sequence import SequenceModel


class DereplicateModel(Task):
    task_name = 'Dereplicate'

    comparison_mode = Property(ComparisonMode)
    similarity_threshold = Property(float)
    length_threshold = Property(int)
    input_item = Property(object)

    def __init__(self, name=None):
        super().__init__(name, init=dereplicate.initialize)
        self.comparison_mode = ComparisonMode.AlignmentFree()
        self.similarity_threshold = 0.07
        self.length_threshold = 0
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
        if not self.comparison_mode.is_valid():
            return False
        return True

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        input = self.input_item.object
        if isinstance(input, SequenceModel):
            input_paths = [input.path]
        elif isinstance(input, BulkSequencesModel):
            input_paths = [sequence.path for sequence in input.sequences]

        self.exec(
            None, dereplicate.dereplicate, work_dir,
            input_paths, input.reader,
            self.comparison_mode,
            self.similarity_threshold,
            self.length_threshold or None,
        )

    def onDone(self, report):
        results = report.result
        dereplicated_bulk = list()
        excluded_bulk = list()
        for input, result in results.items():
            dereplicated_bulk.append(result.dereplicated)
            excluded_bulk.append(result.excluded)

        if len(results) == 1:
            app.model.items.add_sequence(SequenceModel(result.dereplicated))
            app.model.items.add_sequence(SequenceModel(result.excluded))
        else:
            basename = self.input_item.object.name
            app.model.items.add_sequence(BulkSequencesModel(dereplicated_bulk, name=f'{basename} dereplicated'))
            app.model.items.add_sequence(BulkSequencesModel(excluded_bulk, name=f'{basename} excluded'))

        self.done()
