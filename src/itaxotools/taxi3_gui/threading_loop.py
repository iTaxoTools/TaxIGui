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

import sys
import traceback
from dataclasses import dataclass
from typing import Any, NamedTuple, Callable, List, Dict

from itaxotools.common.io import PipeIO

import itaxotools


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


class ReportError(NamedTuple):
    id: Any
    exit_code: int


class ReportProgress(NamedTuple):
    text: str
    value: int = 0
    minimum: int = 0
    maximum: int = 0


def loop(initializer, commands, results, progress, pipeIn, pipeOut, pipeErr):
    """Wait for commands, send back results"""

    inp = PipeIO(pipeIn, 'r')
    out = PipeIO(pipeOut, 'w')
    err = PipeIO(pipeErr, 'w')

    sys.stdin = inp
    sys.stdout = out
    sys.stderr = err

    def _progress_handler(*args, **kwargs):
        report = ReportProgress(*args, **kwargs)
        progress.send(report)

    itaxotools.progress_handler = _progress_handler

    if initializer:
        initializer()
    results.send(InitDone())

    while True:
        id, function, args, kwargs = commands.recv()
        try:
            result = function(*args, **kwargs)
            report = ReportDone(id, result)
        except Exception as exception:
            trace = traceback.format_exc()
            report = ReportFail(id, exception, trace)
        results.send(report)
