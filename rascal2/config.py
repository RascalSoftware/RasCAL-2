import logging
import multiprocessing as mp
import pathlib
import platform
import sys

from rascal2.paths import MATLAB_ARCH_FILE
from rascal2.settings import Settings, get_global_settings

EXAMPLES_TEMP_PATH = pathlib.Path(get_global_settings().fileName()).parent / "examples"
LOGGER = logging.getLogger("rascal2")
SETTINGS = Settings()


def handle_scaling():
    """Change settings to handle UI scaling."""
    if platform.system() == "Windows":
        from ctypes import windll

        windll.user32.SetProcessDPIAware()


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Qt slots swallows exceptions but this ensures exceptions are logged."""
    logging.critical("An unhandled exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))
    logging.shutdown()
    sys.exit(1)


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging for the project.

    Parameters
    ----------
    level : int, default logging.INFO
        The debug level for the logger.

    """
    path = pathlib.Path(get_global_settings().fileName()).parent
    path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    log_file_handler = logging.FileHandler(path / "rascal.log")
    file_formatting = logging.Formatter("%(asctime)s - %(threadName)s -  %(name)s - %(levelname)s - %(message)s")
    log_file_handler.setFormatter(file_formatting)
    logger.addHandler(log_file_handler)

    # handler that logs to terminal widget
    log_term_handler = logging.StreamHandler()
    term_formatting = logging.Formatter("%(levelname)s - %(message)s")
    log_term_handler.setFormatter(term_formatting)
    logger.addHandler(log_term_handler)

    sys.excepthook = log_uncaught_exceptions


def run_matlab(ready_event, close_event, engine_output):
    """Start a new matlab engine instance and waits until closed.

    Parameters
    ----------
    ready_event : multiprocessing.Event
        An event to inform listeners that MATLAB is ready.
    close_event : multiprocessing.Event
        An event to inform this function that MATLAB should be closed.
    engine_output : multiprocessing.Manager.list
        A list to output the name of MATLAB engine instance or an exception.

    """
    try:
        import matlab.engine

        eng = matlab.engine.start_matlab()
        eng.matlab.engine.shareEngine(nargout=0)
        if not close_event.is_set():
            engine_output.append(eng.matlab.engine.engineName(nargout=1).encode("utf-8"))
    except Exception as ex:
        engine_output.append(ex)
        raise ex

    ready_event.set()
    close_event.wait()

    eng.fclose("all", nargout=0)
    eng.close("all", nargout=0)
    eng.quit()


def get_matlab_engine(engine_ready, engine_output):
    """Get a MATLAB engine from the MatlabHelper or exception if no engine is available.

    Parameters
    ----------
    engine_ready : multiprocessing.Event
        An event to inform listeners that MATLAB is ready.
    engine_output :  multiprocessing.Manager.list
        A list with the name of MATLAB engine instance or an exception from the MatlabHelper.

    Returns
    -------
    output : Union[matlab.engine.futureresult.FutureResult, Exception]
        MATLAB engine future or Exception from MatlabHelper
    """
    if not engine_output:
        engine_ready.wait(timeout=40)

    if engine_output:
        if isinstance(engine_output[0], bytes):
            engine_name = engine_output[0].decode("utf-8")

            import ratapi

            engine_future = ratapi.wrappers.use_shared_matlab(
                engine_name,
                "Error occurred when connecting to MATLAB, please ensure MATLAB is installed and set up properly.",
            )

            return engine_future
        elif isinstance(engine_output[0], Exception):
            return engine_output[0]
    else:
        return Exception("Matlab could not be started!")


class MatlabHelper:
    """Helper to start MATLAB on another process."""

    class ConfigError(Exception):
        """Error when setting up MATLAB for RasCAL usage."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.ready_event = mp.Event()
            cls._instance.close_event = mp.Event()
            cls._instance.engine_output = None
            cls._instance.matlab_dir = ""
            cls._instance.__engine = None
            cls._instance.async_start()

        return cls._instance

    def async_start(self):
        """Start MATLAB on a new process."""
        self.manager = mp.Manager()
        self.engine_output = self.manager.list()

        if not self.get_matlab_path():
            return

        self.process = mp.Process(
            target=run_matlab,
            args=(
                self.ready_event,
                self.close_event,
                self.engine_output,
            ),
        )
        self.process.daemon = False
        self.process.start()

    def get_local_engine(self):
        """Get an instance of MATLAB engine for use on the main process.

        Returns
        -------
        matlab.engine.MatlabEngine
            MATLAB engine instance
        """
        if self.__engine is not None:
            return self.__engine

        result = get_matlab_engine(self.ready_event, self.engine_output)
        if isinstance(result, Exception):
            raise result

        self.__engine = result.result()
        return self.__engine

    def get_matlab_path(self):
        """Get MATLAB install directory.

        Returns
        -------
        str
            Return MATLAB install directory.
        """
        install_dir = ""

        try:
            with open(MATLAB_ARCH_FILE) as path_file:
                lines = path_file.readlines()
                if len(lines) == 4:
                    arch = {"x86_64": "maci64", "arm64": "maca64"}
                    if platform.system() == "Darwin" and arch.get(platform.mac_ver()[-1]) != lines[0].strip():
                        # installed intel Matlab on ARM or vice versa
                        raise MatlabHelper.ConfigError(
                            "The installed MATLAB is incompatible, "
                            f"ensure the {platform.mac_ver()[-1]} version of "
                            "MATLAB is installed instead."
                        )

                    install_dir = pathlib.Path(lines[1]).parent.parent
                else:
                    raise MatlabHelper.ConfigError(
                        "Matlab not found, specify MATLAB location in settings i.e. 'File > Settings' menu."
                    )
        except (FileNotFoundError, MatlabHelper.ConfigError) as ex:
            if isinstance(ex, FileNotFoundError):
                ex = MatlabHelper.ConfigError(
                    "Matlab engine could not be found, ensure it is installed properly."
                ).with_traceback(ex.__traceback__)
            self.engine_output[:] = []
            self.engine_output.append(ex)
            LOGGER.error(f"Attempt to read MATLAB _arch file failed {MATLAB_ARCH_FILE}.\n {ex}.")

        self.matlab_dir = str(install_dir)
        return self.matlab_dir
