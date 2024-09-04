"""QObject for running RAT."""

from multiprocessing import Process, Queue
from time import time

import RATapi as RAT
from PyQt6 import QtCore
from RATapi.utils.enums import Procedures


class RATRunner(QtCore.QObject):
    """Class for running RAT."""

    message = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, rat_inputs, procedure: Procedures, display_on: bool):
        super().__init__()
        self.rat_inputs = rat_inputs
        self.procedure = procedure
        self.display_on = display_on

        self.timer = QtCore.QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.check_results)

        # this queue accepts both messages to emit and results objects
        self.queue = Queue()

        self.results = None

    def start(self):
        """Start the calculation."""
        self.process = Process(target=self.run, args=(self.queue, self.rat_inputs, self.procedure))
        self.process.daemon = True
        self.process.start()
        self.timer.start()

    def interrupt(self):
        """Interrupt the running process."""
        self.process.kill()
        self.teardown()
        self.stopped.emit()

    def check_results(self):
        """Check for new results in the queue."""
        if self.queue.empty():
            return
        else:
            item = self.queue.get()
            if isinstance(item, str):  # if item is message
                self.message.emit(item)
            else:  # else, assume item is results
                self.teardown()
                self.results = item
                self.finished.emit()

    def run(self, queue, rat_inputs: tuple, procedure: str) -> RAT.outputs.Results | RAT.outputs.BayesResults:
        """Run RAT and put the result into the queue.

        Parameters
        ----------
        queue : Queue
            The interprocess queue for the RATRunner.
        rat_inputs : tuple
            The C++ inputs for RAT.
        procedure : str
            The method procedure.

        Returns
        -------
        RAT.outputs.Results | RAT.outputs.BayesResults
            The results of the RAT calculation.

        """
        horizontal_line = "\u2500" * 107 + "\n"

        problem_definition, cells, limits, priors, cpp_controls = rat_inputs
        if self.display_on:
            RAT.events.register(RAT.events.EventTypes.Message, self.queue.put)
            start = time()
            self.queue.put("Starting RAT " + horizontal_line)
        problem_definition, output_results, bayes_results = RAT.rat_core.RATMain(
            problem_definition, cells, limits, cpp_controls, priors
        )
        results = RAT.outputs.make_results(procedure, output_results, bayes_results)
        if self.display_on:
            end = time()
            self.queue.put(f"Elapsed time is {end-start:.3f} seconds\n")
            self.queue.put("Finished RAT " + horizontal_line)
            RAT.events.clear(RAT.events.EventTypes.Message, self.queue.put)

        queue.put(results)
        return

    def teardown(self):
        """End and close all communication."""
        self.timer.stop()
        self.process.join()
        self.process.close()
        self.queue.close()
