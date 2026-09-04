"""Tests for the RATRunner class."""

import contextlib
import os
from multiprocessing import Event
from queue import Queue  # we need a non-multiprocessing queue because mocks cannot be serialised
from unittest.mock import MagicMock, patch

import pytest
import ratapi as rat

from rascal2.core.runner import LogData, RATRunner, run


def make_rat_input():
    mock = MagicMock(spec=rat.rat_core.ProblemDefinition)
    mock.customFiles.files = []
    return (mock, 1)


def make_progress_event(percent):
    event = rat.events.ProgressEventData()
    event.percent = percent
    return event


def mock_rat_main(*args, **kwargs):
    """Mock of RAT main that produces some signals."""
    rat.events.notify(rat.events.EventTypes.Progress, make_progress_event(0.2))
    rat.events.notify(rat.events.EventTypes.Progress, make_progress_event(0.5))
    rat.events.notify(rat.events.EventTypes.Message, "test message")
    rat.events.notify(rat.events.EventTypes.Message, "test message 2")
    rat.events.notify(rat.events.EventTypes.Progress, make_progress_event(0.7))
    return 1, 2, 3


@patch("rascal2.core.runner.MatlabHelper", autospec=True)
@patch("rascal2.core.runner.Process")
def test_start(mock_process, mock_matlab):
    """Test that `start` creates and starts a process and timer."""
    mock_matlab.return_value = MagicMock()
    runner = RATRunner()
    runner.go_event = MagicMock()
    runner.set_runner_args(make_rat_input(), "", True, os.getcwd())
    runner.start()

    runner.go_event.set.assert_called_once()
    assert runner.timer.isActive()


@pytest.mark.parametrize(
    "queue_items",
    [
        [
            make_progress_event(0.5),
            (MagicMock(spec=rat.rat_core.ProblemDefinition), MagicMock(spec=rat.outputs.Results)),
        ],
        [(MagicMock(spec=rat.rat_core.ProblemDefinition), MagicMock(spec=rat.outputs.Results))],
        [make_progress_event(0.6)],
        [make_progress_event(0.5), ValueError("Runner error!")],
    ],
)
@patch("rascal2.core.runner.MatlabHelper", autospec=True)
@patch("rascal2.core.runner.Process")
def test_check_queue(mock_process, mock_matlab, queue_items):
    """Test that queue data is appropriately assigned."""
    mock_matlab.return_value = MagicMock()
    runner = RATRunner()
    runner.queue = Queue()
    runner.arg_queue = Queue()
    runner.set_runner_args([], "", True, os.getcwd())
    runner.queue = Queue()

    for item in queue_items:
        runner.queue.put(item)

    runner.check_queue()

    assert len(runner.events) == len([x for x in queue_items if not isinstance(x, (tuple, Exception))])
    for i, item in enumerate(runner.events):
        if isinstance(item, rat.events.ProgressEventData):
            assert item.percent == queue_items[i].percent
        else:
            assert item == queue_items[i]

    if isinstance(queue_items[-1], tuple):
        assert isinstance(runner.updated_problem, rat.rat_core.ProblemDefinition)
        assert isinstance(runner.results, rat.outputs.Results)
    if isinstance(queue_items[-1], Exception):
        assert isinstance(runner.error, ValueError)
        assert str(runner.error) == "Runner error!"


@patch("rascal2.core.runner.MatlabHelper", autospec=True)
@patch("rascal2.core.runner.Process")
def test_empty_queue(mock_process, mock_matlab):
    """Test that nothing happens if the queue is empty."""
    mock_matlab.return_value = MagicMock()
    runner = RATRunner()
    runner.queue = Queue()
    runner.arg_queue = Queue()
    runner.set_runner_args(make_rat_input(), "", True, os.getcwd())

    runner.check_queue()

    assert len(runner.events) == 0
    assert runner.results is None


@pytest.mark.parametrize("display", [True, False])
@patch("ratapi.rat_core.RATMain", new=mock_rat_main)
@patch("ratapi.outputs.make_results", new=MagicMock(spec=rat.outputs.Results))
def test_run(display):
    """Test that a run puts the correct items in the queue."""
    queue = Queue()
    engine_ready = Queue()
    engine_output = Queue()
    args_queue = Queue()
    msg_queue = Queue()
    plot_queue = Queue()
    args_queue.put((make_rat_input(), "", display, os.getcwd()))
    go_event, exit_event = (Event(), Event())
    go_event.set()
    go_event.clear = lambda: exit_event.set()
    with patch("rascal2.core.runner.init_matlab_engine"), patch("rascal2.core.runner.stop_matlab_engine"):
        run(queue, args_queue, msg_queue, plot_queue, go_event, exit_event, engine_ready, engine_output)

    main_display = [
        0.2,
        0.5,
        0.7,
    ]

    msg_display = [
        LogData(20, "Starting RAT"),
        "test message",
        "test message 2",
        LogData(20, "Finished RAT"),
    ]
    while not msg_queue.empty():
        item = msg_queue.get()
        expected_item = msg_display.pop(0)
        assert item == expected_item

    while not queue.empty():
        item = queue.get()
        if isinstance(item, tuple):
            # ensure results were the last item to be added
            assert queue.empty()
        else:
            expected_item = main_display.pop(0)
            assert item.percent == expected_item


def test_run_error():
    """If RATMain produces an error, it should be added to the queue."""

    def erroring_ratmain(*args):
        """RATMain mock that raises an error."""
        raise ValueError("RAT Main Error!")

    with (
        patch("ratapi.rat_core.RATMain", new=erroring_ratmain),
        patch("rascal2.core.runner.init_matlab_engine"),
        patch("rascal2.core.runner.stop_matlab_engine"),
    ):
        queue = Queue()
        engine_ready = Queue()
        engine_output = Queue()
        args_queue = Queue()
        msg_queue = Queue()
        plot_queue = Queue()
        args_queue.put((make_rat_input(), "", True, os.getcwd()))
        go_event, exit_event = (Event(), Event())
        go_event.set()
        go_event.clear = lambda: exit_event.set()
        run(queue, args_queue, msg_queue, plot_queue, go_event, exit_event, engine_ready, engine_output)

    queue.put(None)
    queue_contents = list(iter(queue.get, None))
    msg_queue.put(None)
    msg_queue_content = list(iter(msg_queue.get, None))
    assert len(queue_contents) == 1
    assert len(msg_queue_content) == 1
    assert isinstance(msg_queue_content[0], LogData)
    error = queue_contents[0]
    assert isinstance(error, ValueError)
    assert str(error) == "RAT Main Error!"


@pytest.mark.parametrize("example", rat.examples.__all__)
def test_run_examples(example):
    """Test that the run function runs without an error on the ratapi example projects."""
    # skip convert rascal example
    if example == "convert_rascal":
        return

    # suppress RAT printing
    with open(os.devnull, "w", encoding="utf-8") as stdout, contextlib.redirect_stdout(stdout):
        project, _ = getattr(rat.examples, example)()

    rat_inputs = rat.inputs.make_input(project, rat.Controls())

    queue = Queue()
    args_queue = Queue()
    args_queue.put((rat_inputs, "calculate", False, os.getcwd()))
    plot_queue = Queue()
    msg_queue = Queue()
    engine_ready = Queue()
    engine_output = Queue()
    go_event, exit_event = (Event(), Event())
    go_event.set()
    go_event.clear = lambda: exit_event.set()
    with patch("rascal2.core.runner.init_matlab_engine"), patch("rascal2.core.runner.stop_matlab_engine"):
        run(queue, args_queue, msg_queue, plot_queue, go_event, exit_event, engine_ready, engine_output)

    output = queue.get()

    assert isinstance(output[0], rat.rat_core.ProblemDefinition)
    assert isinstance(output[1], rat.outputs.Results)
