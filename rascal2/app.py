import logging
import multiprocessing

from PyQt6 import QtWidgets

from rascal2.config import SETTINGS, MatlabHelper, handle_scaling, setup_logging
from rascal2.settings import change_ui_style
from rascal2.theme import THEMES, set_stylesheet
from rascal2.ui.view import MainWindowView


def ui_execute(splash):
    """Create main window and executes GUI event loop.

    Returns
    -------
    exit code : int
        QApplication exit code
    """
    handle_scaling()
    app = QtWidgets.QApplication.instance()
    app.setStyle("Fusion")
    app.installEventFilter(THEMES)
    change_ui_style(SETTINGS.style)
    set_stylesheet(app)

    window = MainWindowView()
    window.check_update_dialog.check(startup=True)
    window.show()
    splash.finish(window)

    exit_code = app.exec()
    app.removeEventFilter(THEMES)
    return exit_code


def start_app(splash):
    """Start RasCAL app."""
    multiprocessing.set_start_method("spawn", force=True)
    setup_logging()
    matlab_helper = MatlabHelper()
    exit_code = ui_execute(splash)
    matlab_helper.close_event.set()
    logging.shutdown()
    return exit_code
