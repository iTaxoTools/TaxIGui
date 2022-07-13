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

import multiprocessing as mp
import traceback
import sys

from itaxotools.common.utility import override
from itaxotools.common.io import PipeIO


class ResultDone:
    def __init__(self, result):
        self.result = result


class ResultFail:
    def __init__(self, exception):
        trace = traceback.format_exc()
        self.exception = exception
        self.trace = trace


def _work(commands, results, pipeIn, pipeOut, pipeErr):
    """Wait for commands, send back results"""

    inp = PipeIO(pipeIn, 'r')
    out = PipeIO(pipeOut, 'w')
    err = PipeIO(pipeErr, 'w')

    import sys
    sys.stdin = inp
    sys.stdout = out
    sys.stderr = err

    try:
        while True:
            function, args, kwargs = commands.recv()
            try:
                result = function(*args, **kwargs)
                result = ResultDone(result)
            except Exception as exception:
                result = ResultFail(exception)
            results.send(result)
    finally:
        pipeIn.close()
        pipeOut.close()
        pipeErr.close()
        commands.close()
        results.close()


class Worker(QtCore.QThread):
    """Execute functions on a child process, get notified with results"""
    done = QtCore.Signal(object)
    fail = QtCore.Signal(object, str)
    error = QtCore.Signal(int)

    def __init__(self, stream=None):
        """Immediately starts thread execution"""
        super().__init__()

        self.ready = mp.Condition()
        self.pipeIn = None
        self.pipeOut = None
        self.pipeErr = None
        self.commands = None
        self.results = None
        self.process = None
        self.stream = None
        self.die = False

        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.quit)

        self.setStream(stream or sys.stdout)
        self.start()

    @override
    def run(self):
        """
        Internal. This is executed on the new thread after start() is called.
        Once a child process is ready, enter an event loop.
        """
        while not self.die:
            with self.ready:
                self.ready.wait()
            # check again in case of quit()
            if self.die:
                break
            self.loop()

    def loop(self):
        """
        Internal. Thread event loop that handles events
        for the currently running process.
        """
        sentinel = self.process.sentinel
        waitList = {
            sentinel: None,
            self.results: self.handleResults,
            self.pipeOut: self.handleOut,
            self.pipeErr: self.handleErr,
        }
        while waitList and sentinel is not None:
            readyList = mp.connection.wait(waitList.keys())
            for connection in readyList:
                if connection == sentinel:
                    # Process exited, but must make sure
                    # all other pipes are empty before quitting
                    if len(readyList) == 1:
                        sentinel = None
                else:
                    try:
                        data = connection.recv()
                    except EOFError:
                        waitList.pop(connection)
                    else:
                        waitList[connection](data)

        if self.process and self.process.exitcode != 0 and not self.die:
            self.error.emit(self.process.exitcode)

        self.pipeIn.close()
        self.pipeOut.close()
        self.pipeErr.close()
        self.commands.close()
        self.results.close()
        self.process = None

    def handleResults(self, result):
        """Internal. Emit results."""
        if isinstance(result, ResultDone):
            self.done.emit(result.result)
        elif isinstance(result, ResultFail):
            self.fail.emit(result.exception, result.trace)

    def init(self):
        """Internal. Initialize process and pipes"""
        with self.ready:
            pipeIn, self.pipeIn = mp.Pipe(duplex=False)
            self.pipeOut, pipeOut = mp.Pipe(duplex=False)
            self.pipeErr, pipeErr = mp.Pipe(duplex=False)
            commands, self.commands = mp.Pipe(duplex=False)
            self.results, results = mp.Pipe(duplex=False)
            self.process = mp.Process(
                target=_work, daemon=True,
                args=(commands, results, pipeIn, pipeOut, pipeErr))
            self.process.start()
            self.ready.notify()

    def setStream(self, stream):
        """Internal. Send process output to given file-like stream"""
        self.stream = stream

        if stream is not None:
            self.handleOut = self._streamOut
            self.handleErr = self._streamOut
        else:
            self.handleOut = self._streamNone
            self.handleErr = self._streamNone

    def handleOut(self, data):
        pass

    def handleErr(self, data):
        pass

    def _streamNone(self, data):
        pass

    def _streamOut(self, data):
        self.stream.write(data)

    def exec(self, function, *args, **kwargs):
        """Execute given function on a child process"""
        if self.process is None:
            self.init()
        self.commands.send((function, args, kwargs))

    def reset(self):
        """Interrupt the current task"""
        if self.process is not None and self.process.is_alive():
            self.process.terminate()
            self.process = None

    @override
    def quit(self):
        """Also kills the child process"""
        with self.ready:
            self.reset()
            self.die = True
            self.ready.notify()

        super().quit()
        self.wait()
