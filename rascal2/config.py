import logging
import pathlib
import platform
import sys
from os import PathLike

<<<<<<< HEAD
from rascal2.core import Settings, get_global_settings
=======
from rascal2.core import Settings
from rascal2.widgets import TerminalWidget
>>>>>>> a071eb5 (added terminal output for logging)

SOURCE_PATH = pathlib.Path(__file__).parent
STATIC_PATH = SOURCE_PATH / "static"
IMAGES_PATH = STATIC_PATH / "images"


def handle_scaling():
    """Changes settings to handle UI scaling"""
    if platform.system() == "Windows":
        from ctypes import windll

        windll.user32.SetProcessDPIAware()


def path_for(filename: str):
    """Gets full path for the given image file.

    Parameters
    ----------
    filename : str
        basename and extension of image.

    Returns
    -------
    full path : str
        full path of the image.
    """
    return (IMAGES_PATH / filename).as_posix()


def setup_settings(project_path: str | PathLike) -> Settings:
    """Set up the Settings object for the project.

    Parameters
    ----------
    project_path : str or PathLike
        The path to the current RasCAL-2 project.

    Returns
    -------
    Settings
        If a settings.json file already exists in the
        RasCAL-2 project, returns a Settings object with
        the settings defined there. Otherwise, returns a
        (global) default Settings object.

    """
    filepath: pathlib.Path = pathlib.Path(project_path, "settings.json")
    if filepath.is_file():
        json = filepath.read_text()
        return Settings.model_validate_json(json)
    return Settings()


def setup_logging(log_path: str | PathLike, terminal: TerminalWidget, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for the project.

    The default logging path and level are defined in the settings.

    Parameters
    ----------
    log_path : str | PathLike
        The path to where the log file will be written.
    terminal : TerminalWidget
        The StdoutReceiver instance which sends text to the terminal widget.
    level : int, default logging.INFO
        The debug level for the logger.

    """
    path = pathlib.Path(log_path)
    logger = logging.getLogger("rascal_log")
    logger.setLevel(level)
    logger.handlers.clear()

    log_filehandler = logging.FileHandler(path)
    logger.addHandler(log_filehandler)

    # handler that logs to terminal widget
    log_termhandler = logging.StreamHandler(stream=terminal)
    logger.addHandler(log_termhandler)

    return logger


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Qt slots swallows exceptions but this ensures exceptions are logged"""
    logger = logging.getLogger("rascal_log")
    if not logger.handlers:
        # Backup in case the crash happens before the local logger setup
        path = pathlib.Path(get_global_settings().fileName()).parent
        path.mkdir(parents=True, exist_ok=True)
        logger.addHandler(logging.FileHandler(path / "crash.log"))
    logger.critical("An unhandled exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))
    logging.shutdown()
    sys.exit(1)
