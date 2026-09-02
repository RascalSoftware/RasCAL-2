"""QObject for running rat."""

import os
import sys
from dataclasses import dataclass
from logging import INFO
from multiprocessing import Event, Process, Queue

import ratapi as rat
from PyQt6 import QtCore

from rascal2.config import MatlabHelper, get_matlab_engine


def clear_queue(queue):
    queue.put(None)
    for _ in iter(queue.get, None):
        pass


class RATRunner(QtCore.QObject):
    """Class for running rat."""

    event_received = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.check_queue)

        # this queue handles both event data and results
        self.queue = Queue()
        self.msg_queue = Queue()
        self.plot_queue = Queue()
        self.arg_queue = Queue()
        self.go_event = Event()
        self.exit_event = Event()
        matlab_helper = MatlabHelper()
        self.process = Process(
            target=run,
            args=(
                self.queue,
                self.arg_queue,
                self.msg_queue,
                self.plot_queue,
                self.go_event,
                self.exit_event,
                matlab_helper.ready_event,
                matlab_helper.engine_output,
            ),
        )
        self.updated_problem = None
        self.results = None
        self.error = None
        self.events = []

    def set_runner_args(self, rat_inputs, procedure, display_on: bool, working_dir: str):
        self.clear_queues()
        self.arg_queue.put((rat_inputs, procedure, display_on, working_dir))

    def start(self):
        """Start the calculation."""
        if not self.process.is_alive():
            self.process.start()
        self.go_event.set()
        self.timer.start()

    # def write_msg(self):
    #     self.msg_queue.put(None)
    #     text = ''
    #     for item in iter(self.msg_queue.get, None):
    #         if isinstance(item, str):
    #             text += item[:-1] if item.endswith("\n\n") else item
    #         if isinstance(item, LogData):
    #             if text:
    #                 self.events.append(text)
    #                 self.event_received.emit()
    #                 text = ''
    #             self.events.append(item)
    #             self.event_received.emit()
    #     if text:
    #         self.events.append(text)
    #         self.event_received.emit()


    def handle_plot(self):
        item = None
        while not self.plot_queue.empty():
            item = self.plot_queue.get()
        else:
            if item is not None:
                self.events.append(item)
                self.event_received.emit()

    def write_msg(self):
        text = ''
        while not self.msg_queue.empty():
            item = self.msg_queue.get()
            if isinstance(item, str):
                text += item[:-1] if item.endswith("\n\n") else item
            if isinstance(item, LogData):
                if text:
                    self.events.append(text)
                    self.event_received.emit()
                    text = ''
                self.events.append(item)
                self.event_received.emit()
        if text:
            self.events.append(text)
            self.event_received.emit()



    def check_queue(self):
        """Check for new data in the queue."""
        if self.process is None or not self.process.is_alive():
            self.timer.stop()

        self.handle_plot()
        self.write_msg()
        self.queue.put(None)
        for item in iter(self.queue.get, None):
            if isinstance(item, tuple):
                self.updated_problem, self.results = item
                self.go_event.clear()
                self.handle_plot()
                self.write_msg()
                if is_empty_bayes_result(self.results):
                    self.stopped.emit()
                else:
                    self.finished.emit()
                self.timer.stop()
            elif isinstance(item, Exception):
                self.error = item
                self.go_event.clear()
                self.handle_plot()
                self.write_msg()
                self.stopped.emit()
                self.timer.stop()
            else:  # else, assume item is an event
                self.events.append(item)
                self.event_received.emit()

    def clear_queues(self):
        clear_queue(self.queue)
        clear_queue(self.arg_queue)
        clear_queue(self.msg_queue)
        clear_queue(self.plot_queue)
        self.events.clear()
        self.go_event.clear()
        self.exit_event.clear()

    def stop(self):
        self.event_received.disconnect()
        if self.process.is_alive():
            self.process.kill()
        self.process = None
        self.clear_queues()


def init_matlab_engine(problem_definition, engine_ready, engine_output, queue):
    """Initialise the Matlab engine if using a Matlab custom file and returns the engine future if available."""
    engine_future = rat.wrappers.MatlabWrapper.loader
    if engine_future is None and any([file["language"] == "matlab" for file in problem_definition.customFiles.files]):
        if engine_output.empty():
            print(11)
            queue.put(LogData(INFO, "Attempting to start Matlab..."))

        print(12)
        result = get_matlab_engine(engine_ready, engine_output)

        if isinstance(result, Exception):
            print(13)
            raise result
        else:
            print(14)
            engine_future = result
            engine_future.result().cd(os.getcwd())
    return engine_future


def stop_matlab_engine(engine_future):
    """Exit the Matlab engine future if present."""
    if engine_future is not None:
        engine_future.result().exit()


def is_empty_bayes_result(result):
    return isinstance(result, rat.BayesResults) and result.chain.shape == (1, 2)


def run(queue: Queue, arg_queue: Queue, msg_queue: Queue, plot_queue, go_event, exit_event, engine_ready, engine_output):
    """Run RAT and put the result into the queue.

    Parameters
    ----------
    queue : Queue
        The interprocess queue for the RATRunner.
    arg_queue :
        A queue of arguments used to initialize the RAT process, passed from the Main Presenter

    """
    engine_future = None
    while True:
        go_event.wait()
        if exit_event.is_set():
            stop_matlab_engine(engine_future)
            return
        rat_inputs, procedure, display, working_dir = arg_queue.get()
        os.chdir(working_dir)
        problem_definition, cpp_controls = rat_inputs

        if display:
            rat.events.register(rat.events.EventTypes.Message, msg_queue.put)
            rat.events.register(rat.events.EventTypes.Progress, queue.put)
            rat.events.register(rat.events.EventTypes.Plot, plot_queue.put)
            msg_queue.put(LogData(INFO, "Starting RAT"))

        try:
            sys.path.append(working_dir)
            engine_future = init_matlab_engine(problem_definition, engine_ready, engine_output, queue)
            problem_definition, output_results, bayes_results = rat.rat_core.RATMain(problem_definition, cpp_controls)
            results = rat.outputs.make_results(procedure, output_results, bayes_results)
        except Exception as err:
            queue.put(err)
            go_event.clear()
            continue
        finally:
            sys.path.remove(working_dir)

        if display:
            msg = "RAT run interrupted!" if is_empty_bayes_result(results) else "Finished RAT"
            msg_queue.put(LogData(INFO, msg))
            rat.events.clear()

        queue.put((problem_definition, results))
        go_event.clear()


@dataclass
class LogData:
    """Dataclass for logging data."""

    level: int
    msg: str
