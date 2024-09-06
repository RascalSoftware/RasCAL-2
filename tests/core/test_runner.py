"""Tests for the RATRunner class."""

from unittest.mock import patch

import pytest
import RATapi as RAT
from PyQt6 import QtTest

from rascal2.core import RATRunner


def make_progress_event(percent):
    event = RAT.events.ProgressEventData()
    event.percent = percent
    return event


def mock_rat_main(*args, **kwargs):
    """Mock of RAT main that produces some signals."""

    RAT.events.notify(RAT.events.EventTypes.Progress, make_progress_event(0.2))
    RAT.events.notify(RAT.events.EventTypes.Progress, make_progress_event(0.5))
    RAT.events.notify(RAT.events.EventTypes.Message, "test message")
    RAT.events.notify(RAT.events.EventTypes.Message, "test message 2")
    RAT.events.notify(RAT.events.EventTypes.Progress, make_progress_event(0.7))
    return 1, 2, 3


def mock_make_results(*args, **kwargs):
    """Produce an empty Results object."""
    return RAT.outputs.Results(
        reflectivity=[],
        simulation=[],
        shiftedData=[],
        layerSlds=[],
        sldProfiles=[],
        resampledLayers=[],
        calculationResults=RAT.outputs.CalculationResults(chiValues=[], sumChi=0.0),
        contrastParams=RAT.outputs.ContrastParams(
            backgroundParams=[], scalefactors=[], bulkIn=[], bulkOut=[], resolutionParams=[], subRoughs=[], resample=[]
        ),
        fitParams=[],
        fitNames=[],
    )


@patch("rascal2.core.runner.Process")
def test_start(mock_process):
    """Test that `start` creates and starts a process and timer."""
    runner = RATRunner([], "", True)
    runner.start()

    runner.process.start.assert_called_once()
    assert runner.timer.isActive()


@patch("rascal2.core.runner.Process")
def test_interrupt(mock_process):
    """Test that `start` creates and starts a process and timer."""
    runner = RATRunner([], "", True)
    runner.interrupt()

    runner.process.join.assert_called_once()
    runner.process.close.assert_called_once()
    runner.process.kill.assert_called_once()
    assert not runner.timer.isActive()


@pytest.mark.parametrize(
    "queue_items",
    [
        ["message!"],
        ["message!", mock_make_results()],
        [make_progress_event(0.6)],
        ["message 1!", make_progress_event(0.4), "message 2!"],
    ],
)
@patch("rascal2.core.runner.Process")
def test_check_queue(mock_process, queue_items):
    """Test that signals are sent when the queue receives messages."""
    runner = RATRunner([], "", True)

    messages = []
    progress_events = []
    runner.message.connect(lambda x: messages.append(x))
    runner.progress.connect(lambda x: progress_events.append(x.percent))
    message_spy = QtTest.QSignalSpy(runner.message)
    progress_spy = QtTest.QSignalSpy(runner.progress)
    result_spy = QtTest.QSignalSpy(runner.finished)

    def assert_results_last():
        assert runner.queue.empty()

    runner.finished.connect(assert_results_last)

    for item in queue_items:
        runner.queue.put(item)

    for item in queue_items:
        if isinstance(item, str):
            message_spy.wait(50)
            runner.check_queue()
        elif isinstance(item, RAT.events.ProgressEventData):
            progress_spy.wait(50)
            runner.check_queue()
        elif isinstance(item, RAT.outputs.Results):
            result_spy.wait(50)
            runner.check_queue()

    assert messages == [x for x in queue_items if isinstance(x, str)]
    assert progress_events == [x.percent for x in queue_items if isinstance(x, RAT.events.ProgressEventData)]


@pytest.mark.parametrize("display", [True, False])
@patch("RATapi.rat_core.RATMain", new=mock_rat_main)
@patch("RATapi.outputs.make_results", new=mock_make_results)
def test_run(display):
    """Test that a run puts the correct items in the queue."""
    runner = RATRunner([], "", True)
    runner.run(runner.queue, [0, 1, 2, 3, 4], "", display)
    horizontal_line = "\u2500" * 107 + "\n"
    expected_display = [
        "Starting RAT " + horizontal_line,
        0.2,
        0.5,
        "test message",
        "test message 2",
        0.7,
        "Finished RAT " + horizontal_line,
    ]

    while not runner.queue.empty():
        item = runner.queue.get()
        if isinstance(item, RAT.outputs.Results):
            # ensure results were the last item to be added
            assert runner.queue.empty()
        else:
            expected_item = expected_display.pop(0)
            if isinstance(item, RAT.events.ProgressEventData):
                assert item.percent == expected_item
            else:
                assert item == expected_item
