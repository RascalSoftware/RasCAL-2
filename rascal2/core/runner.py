"""QObject for running RAT."""

from dataclasses import dataclass
from multiprocessing import Process, Queue

import RATapi as RAT
from PyQt6 import QtCore
from RATapi.utils.enums import Procedures


class RATRunner(QtCore.QObject):
    """Class for running RAT."""

    event_received = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, rat_inputs, procedure: Procedures, display_on: bool):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.check_queue)

        # this queue handles both event data and results
        self.queue = Queue()

        self.process = Process(target=run, args=(self.queue, rat_inputs, procedure, display_on))

        self.results = None
        self.error = None
        self.events = []

    def start(self):
        """Start the calculation."""
        self.process.start()
        self.timer.start()

    def interrupt(self):
        """Interrupt the running process."""
        self.timer.stop()
        self.process.kill()
        self.stopped.emit()

    def check_queue(self):
        """Check for new data in the queue."""
        if not self.process.is_alive():
            self.timer.stop()
        self.queue.put(None)
        # the queue should never be empty at this line (because we just put a
        # None in it) but if it is, it'd hang forever - we add the timeout
        # to avoid this happening just in case
        for item in iter(lambda: self.queue.get(timeout=500), None):
            if isinstance(item, (RAT.outputs.Results, RAT.outputs.BayesResults)):
                self.results = item
                self.finished.emit()
            elif isinstance(item, Exception):
                self.error = item
                self.stopped.emit()
            else:  # else, assume item is an event
                self.events.append(item)
                self.event_received.emit()


def run(queue, rat_inputs: tuple, procedure: str, display: bool):
    """Run RAT and put the result into the queue.

    Parameters
    ----------
    queue : Queue
        The interprocess queue for the RATRunner.
    rat_inputs : tuple
        The C++ inputs for RAT.
    procedure : str
        The optimisation procedure.
    display : bool
        Whether to display events.

    """
    problem_definition, cells, limits, priors, cpp_controls = rat_inputs

    if display:
        RAT.events.register(RAT.events.EventTypes.Message, queue.put)
        RAT.events.register(RAT.events.EventTypes.Progress, queue.put)
        queue.put(LogData(20, "Starting RAT"))

    try:
        problem_definition, output_results, bayes_results = RAT.rat_core.RATMain(
            problem_definition, cells, limits, cpp_controls, priors
        )
        results = RAT.outputs.make_results(procedure, output_results, bayes_results)
    except Exception as err:
        queue.put(err)
        return

    if display:
        queue.put(LogData(20, "Finished RAT"))
        RAT.events.clear()

    queue.put(results)
    return


@dataclass
class LogData:
    """Dataclass for logging data."""

    level: int
    msg: str
