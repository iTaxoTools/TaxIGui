from itaxotools.taxi_gui import app
from itaxotools.taxi_gui.main import Main
from itaxotools.taxi_gui.tasks import (
    decontaminate,
    dereplicate,
    versus_all,
    versus_reference,
)


def test_main(qapp):
    Main()


def test_decontaminate(qapp):
    task = app.Task.from_module(decontaminate)
    # task.model()
    task.view()


def test_dereplicate(qapp):
    task = app.Task.from_module(dereplicate)
    # task.model()
    task.view()


def test_versus_all(qapp):
    task = app.Task.from_module(versus_all)
    # task.model()
    task.view()


def test_versus_reference(qapp):
    task = app.Task.from_module(versus_reference)
    # task.model()
    task.view()
