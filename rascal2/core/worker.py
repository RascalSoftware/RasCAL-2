from PyQt6 import QtCore


class Worker(QtCore.QThread):
    """Creates worker thread object.

    Parameters
    ----------
    func : Callable[..., Any]
        function to run on ``QThread``.
    args : Tuple[Any, ...]
        arguments of function ``func``.
    """

    job_succeeded = QtCore.pyqtSignal("PyQt_PyObject")
    job_failed = QtCore.pyqtSignal(Exception, "PyQt_PyObject")

    def __init__(self, func, args):
        super().__init__()
        self.func = func
        self._args = args
        self.stopped = False

    def run(self):
        """This function is executed on worker thread when the ``QThread.start``
        method is called."""
        if self.stopped:
            return

        try:
            result = self.func(*self._args)
            self.job_succeeded.emit(result)
        except Exception as e:
            self.job_failed.emit(e, self._args)

    def stop(self):
        self.stopped = True
        self.quit()
        self.wait()

    @classmethod
    def call(cls, func, args, on_success=None, on_failure=None, on_complete=None):
        """Calls the given function from a new worker thread object.

        Parameters
        ----------
        func : Callable[..., Any]
            function to run on ``QThread``.
        args : Tuple[Any, ...]
            arguments of function ``func``.
        on_success : Union[Callable[..., None], None]
            function to call on success.
        on_failure : Union[Callable[..., None], None]
            function to call on failure.
        on_complete : Union[Callable[..., None], None]
            function to call when complete.

        Returns
        -------
        Worker
            worker thread running ``func``.
        """
        worker = cls(func, args)
        if on_success is not None:
            worker.job_succeeded.connect(on_success)
        if on_failure is not None:
            worker.job_failed.connect(on_failure)
        if on_complete is not None:
            worker.finished.connect(on_complete)
        worker.start()

        return worker
