"""QObject for running RAT."""

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

        self.process = Process(target=self.run, args=(self.queue, rat_inputs, procedure, display_on))
        self.process.daemon = True

        self.results = None
        self.events = []

    def start(self):
        """Start the calculation."""
        self.process.start()
        self.timer.start()

    def interrupt(self):
        """Interrupt the running process."""
        self.process.kill()
        self.teardown()
        self.stopped.emit()

    def check_queue(self):
        """Check for new data in the queue."""
        self.queue.put(None)
        for item in iter(self.queue.get, None):
            if isinstance(item, RAT.outputs.Results):
                self.teardown()
                self.results = item
                self.finished.emit()
                break
            else:  # else, assume item is an event
                self.events.append(item)
                self.event_received.emit()

    def run(self, queue, rat_inputs: tuple, procedure: str, display: bool):
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
        horizontal_line = "\u2500" * 107 + "\n"
        problem_definition, cells, limits, priors, cpp_controls = rat_inputs

        if display:
            RAT.events.register(RAT.events.EventTypes.Message, self.queue.put)
            RAT.events.register(RAT.events.EventTypes.Progress, self.queue.put)
            self.queue.put("Starting RAT " + horizontal_line)

        problem_definition, output_results, bayes_results = RAT.rat_core.RATMain(
            problem_definition, cells, limits, cpp_controls, priors
        )
        results = RAT.outputs.make_results(procedure, output_results, bayes_results)

        if display:
            self.queue.put("Finished RAT " + horizontal_line)
            RAT.events.clear()

        queue.put(results)
        return

    def teardown(self):
        """End and close all communication."""
        self.timer.stop()
        self.process.join()
        self.process.close()
        self.queue.close()