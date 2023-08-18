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

"""Worker process loop"""

import sys
import traceback
from typing import Any, Callable, Dict, List, NamedTuple

import itaxotools

from .io import PipeWriterIO


class InitDone:
    pass


class Command(NamedTuple):
    id: Any
    function: Callable
    args: List[Any]
    kwargs: Dict[str, Any]


class ReportDone(NamedTuple):
    id: Any
    result: Any


class ReportFail(NamedTuple):
    id: Any
    exception: Exception
    traceback: str


class ReportExit(NamedTuple):
    id: Any
    exit_code: int


class ReportStop(NamedTuple):
    id: Any


class ReportQuit:
    pass


class ReportProgress(NamedTuple):
    text: str
    value: int = 0
    minimum: int = 0
    maximum: int = 0


class DataQuery(NamedTuple):
    id: Any
    data: object


class AbortCommand(Exception):
    pass


def loop(commands, results, progress, queries, pipe_out):
    """Wait for commands, send back results"""

    out = PipeWriterIO(pipe_out, 1)
    err = PipeWriterIO(pipe_out, 2)

    sys.stdout = out
    sys.stderr = err

    def progress_handler(*args, **kwargs):
        report = ReportProgress(*args, **kwargs)
        progress.send(report)

    def get_feedback(data: object):
        id = itaxotools.current_command_id
        query = DataQuery(id, data)
        queries.send(query)
        return queries.recv()

    def abort():
        raise AbortCommand()

    itaxotools.current_command_id = None
    itaxotools.progress_handler = progress_handler
    itaxotools.get_feedback = get_feedback
    itaxotools.abort = abort

    while True:
        id, function, args, kwargs = commands.recv()
        itaxotools.current_command_id = id
        try:
            result = function(*args, **kwargs)
            report = ReportDone(id, result)
        except AbortCommand:
            report = ReportStop(id)
        except Exception as exception:
            trace = traceback.format_exc()
            report = ReportFail(id, exception, trace)
        results.send(report)
