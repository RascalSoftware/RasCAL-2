import logging
import multiprocessing
import re
from contextlib import suppress

from PyQt6 import QtWidgets

from rascal2.config import MatlabHelper, handle_scaling, setup_logging
from rascal2.paths import IMAGES_PATH, STATIC_PATH
from rascal2.ui.view import MainWindowView


def ui_execute(splash):
    """Create main window and executes GUI event loop.

    Returns
    -------
    exit code : int
        QApplication exit code
    """
    handle_scaling()
    QtWidgets.QApplication.setStyle("Fusion")
    app = QtWidgets.QApplication.instance()
    with suppress(FileNotFoundError), open(STATIC_PATH / "style.css") as stylesheet:
        palette = app.palette()
        replacements = {
            "@Path": IMAGES_PATH.as_posix(),
            "@Window": palette.window().color().name(),
            "@Highlight": palette.highlight().color().name(),
            "@Midlight": palette.midlight().color().name(),
            "@Text": palette.text().color().name(),
        }
        style = re.sub("|".join(replacements), lambda x: replacements[x.group(0)], stylesheet.read())
        app.setStyleSheet(style)

    window = MainWindowView()
    window.show()
    splash.finish(window)

    return app.exec()


def start_app(splash):
    """Start RasCAL app."""
    multiprocessing.set_start_method("spawn", force=True)
    setup_logging()
    matlab_helper = MatlabHelper()
    exit_code = ui_execute(splash)
    matlab_helper.close_event.set()
    logging.shutdown()
    return exit_code
