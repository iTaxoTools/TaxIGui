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

from PySide6 import QtCore

import multiprocessing as mp
import sys
from contextlib import contextmanager

from itaxotools.common.utility import override

from .io import PipeWrite, StreamGroup
from .loop import (
    Command,
    DataQuery,
    ReportDone,
    ReportExit,
    ReportFail,
    ReportProgress,
    ReportQuit,
    ReportStop,
    loop,
)


class Worker(QtCore.QThread):
    """Execute functions on a child process, get notified with results"""

    done = QtCore.Signal(ReportDone)
    fail = QtCore.Signal(ReportFail)
    error = QtCore.Signal(ReportExit)
    stop = QtCore.Signal(ReportStop)
    progress = QtCore.Signal(ReportProgress)
    query = QtCore.Signal(DataQuery)

    def __init__(self, name="Worker", eager=True, log_path=None):
        """Immediately starts thread execution"""
        super().__init__()
        self.name = name
        self.eager = eager
        self.log_path = log_path

        self.queue = mp.Queue()
        self.pipe_out = None
        self.commands = None
        self.results = None
        self.reports = None
        self.queries = None
        self.process = None
        self.resetting = False
        self.quitting = False

        self.streamOut = StreamGroup(sys.stdout)
        self.streamErr = StreamGroup(sys.stderr)

        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.quit)

        self.start()

    @override
    def run(self):
        """
        Internal. This is executed on the new thread after start() is called.
        Once a child process is ready, enter an event loop.
        """
        with self.open_log("all.log"):
            if self.eager:
                self.process_start()
            while not self.quitting:
                task = self.queue.get()
                if task is None:
                    break
                if self.process is None:
                    self.process_start()
                with self.open_log(f"{str(task.id)}.log"):
                    self.commands.send(task)
                    report = self.loop(task)
                    self.handle_report(report)

    def loop(self, task: Command):
        """
        Internal. Thread event loop that handles events
        for the currently running process.
        """
        sentinel = self.process.sentinel
        waitList = {
            sentinel: None,
            self.results: None,
            self.reports: self.progress.emit,
            self.queries: self.query.emit,
            self.pipe_out: self.handle_output,
        }
        report = None
        while not report:
            readyList = mp.connection.wait(waitList.keys())
            if sentinel in readyList:
                waitList.pop(sentinel, None)
                waitList.pop(self.results, None)
                report = self.handle_exit(task, waitList)
            elif self.results in readyList:
                try:
                    report = self.results.recv()
                except EOFError:
                    waitList.pop(self.results, None)
                else:
                    waitList.pop(sentinel, None)
                    waitList.pop(self.results, None)
                    self.consume_connections(waitList)
            else:
                self.handle_connections(waitList, readyList)
        return report

    def handle_output(self, out: PipeWrite):
        if out.tag == 1:
            self.streamOut.write(out.text)
        elif out.tag == 2:
            self.streamErr.write(out.text)

    def handle_exit(self, task, waitList):
        self.consume_connections(waitList)
        exitcode = self.process.exitcode
        resetting = self.resetting

        self.pipe_out.close()
        self.commands.close()
        self.results.close()
        self.reports.close()
        self.process = None

        if self.quitting:
            return ReportQuit()
        elif self.eager:
            self.process_start()

        if resetting:
            return ReportStop(task.id)

        return ReportExit(task.id, exitcode)

    def handle_connections(self, waitList, readyList):
        for connection in readyList:
            try:
                data = connection.recv()
            except EOFError:
                waitList.pop(connection)
            else:
                waitList[connection](data)

    def consume_connections(self, waitList):
        while readyList := mp.connection.wait(waitList.keys(), 0):
            self.handle_connections(waitList, readyList)

    def handle_report(self, report):
        self.streamOut.flush()
        self.streamErr.flush()
        if isinstance(report, ReportDone):
            self.done.emit(report)
        elif isinstance(report, ReportFail):
            self.streamErr.write(report.traceback)
            self.streamErr.flush()
            self.fail.emit(report)
        if isinstance(report, ReportStop):
            self.streamErr.write("\nCancelled process by user request.\n")
            self.streamErr.flush()
            self.stop.emit(report)
        elif isinstance(report, ReportExit):
            self.streamErr.write(f"Process failed with exit code: {report.exit_code}")
            self.streamErr.flush()
            if report.id != 0:
                self.error.emit(report)

    @contextmanager
    def open_log(self, filename):
        path = self.log_path
        if not path:
            yield
            return
        with open(path / filename, "a") as file:
            self.streamOut.add(file)
            self.streamErr.add(file)
            yield
            self.streamOut.remove(file)
            self.streamErr.remove(file)

    def process_start(self):
        """Internal. Initialize process and pipes"""
        self.resetting = False
        self.pipe_out, pipe_out = mp.Pipe(duplex=False)
        commands, self.commands = mp.Pipe(duplex=False)
        self.results, results = mp.Pipe(duplex=False)
        self.reports, reports = mp.Pipe(duplex=False)
        self.queries, queries = mp.Pipe(duplex=True)
        self.process = mp.Process(
            target=loop,
            daemon=True,
            name=self.name,
            args=(commands, results, reports, queries, pipe_out),
        )
        self.process.start()

    def exec(self, id, function, *args, **kwargs):
        """Execute given function on a child process"""
        self.queue.put(Command(id, function, args, kwargs))

    def reset(self):
        """Interrupt the current task"""
        if self.process is not None and self.process.is_alive():
            self.resetting = True
            self.streamOut.flush()
            self.streamErr.flush()
            self.process.terminate()

    def answer(self, data):
        """Respond to a query signal"""
        self.queries.send(data)

    @override
    def quit(self):
        """Also kills the child process"""
        self.reset()
        self.quitting = True
        self.queue.put(None)

        super().quit()
        self.wait()
        self.streamOut.close()
        self.streamErr.close()
