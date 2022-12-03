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

from collections import deque
import multiprocessing as mp
import sys

from itaxotools.common.utility import override

from .threading_loop import (
    Command, InitDone, ReportProgress, ReportDone, ReportFail, ReportError, loop)


class Worker(QtCore.QThread):
    """Execute functions on a child process, get notified with results"""
    done = QtCore.Signal(ReportDone)
    fail = QtCore.Signal(ReportFail)
    error = QtCore.Signal(ReportError)
    progress = QtCore.Signal(ReportProgress)

    def __init__(self, name='Worker', eager=True, init=None, stream=None):
        """Immediately starts thread execution"""
        super().__init__()
        self.eager = eager
        self.initializer = init
        self.name = name

        self.queue = deque()
        self.ready = mp.Semaphore(0)
        self.pipeIn = None
        self.pipeOut = None
        self.pipeErr = None
        self.commands = None
        self.results = None
        self.reports = None
        self.process = None
        self.stream = None
        self.initialized = False
        self.resetting = False
        self.quitting = False

        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.quit)

        self.setStream(stream or sys.stdout)
        self.start()

        if eager:
            self.init()

    @override
    def run(self):
        """
        Internal. This is executed on the new thread after start() is called.
        Once a child process is ready, enter an event loop.
        """
        while not self.quitting:
            self.ready.acquire()
            # check again in case of quit()
            if self.quitting:
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
            self.reports: self.handleProgress,
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

        if self.process and self.process.exitcode != 0:
            if not self.resetting and not self.quitting:
                if not self.initialized:
                    # If process failed during init, don't run it again
                    self.eager = False
                id = self.queue[0]  # just get the current id
                report = ReportError(id, self.process.exitcode)
                self.handleResults(report)

        self.pipeIn.close()
        self.pipeOut.close()
        self.pipeErr.close()
        self.commands.close()
        self.results.close()
        self.reports.close()
        self.process = None

        if self.eager and not self.quitting:
            self.init()

    def handleResults(self, report):
        """Internal. Emit results."""
        if isinstance(report, InitDone):
            self.initialized = True
            return
        current_id = self.queue.popleft()
        assert report.id == current_id
        if isinstance(report, ReportDone):
            self.done.emit(report)
        elif isinstance(report, ReportFail):
            self.fail.emit(report)
        elif isinstance(report, ReportError):
            self.error.emit(report)

    def handleProgress(self, report):
        """Internal. Emit progress report."""
        self.progress.emit(report)

    def init(self):
        """Internal. Initialize process and pipes"""
        self.initialized = False
        self.resetting = False
        pipeIn, self.pipeIn = mp.Pipe(duplex=False)
        self.pipeOut, pipeOut = mp.Pipe(duplex=False)
        self.pipeErr, pipeErr = mp.Pipe(duplex=False)
        commands, self.commands = mp.Pipe(duplex=False)
        self.results, results = mp.Pipe(duplex=False)
        self.reports, reports = mp.Pipe(duplex=False)
        self.process = mp.Process(
            target=loop, daemon=True, name=self.name,
            args=(self.initializer, commands, results, reports, pipeIn, pipeOut, pipeErr))
        self.process.start()
        self.ready.release()

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

    def exec(self, id, function, *args, **kwargs):
        """Execute given function on a child process"""
        if self.process is None:
            self.init()
        print(f'>>> {repr(id)}',)
        self.queue.append(id)
        self.commands.send(Command(id, function, args, kwargs))

    def reset(self):
        """Interrupt the current task"""
        if self.process is not None and self.process.is_alive():
            self.resetting = True
            self.process.terminate()

    @override
    def quit(self):
        """Also kills the child process"""
        self.reset()
        self.quitting = True
        self.ready.release()

        super().quit()
        self.wait()
