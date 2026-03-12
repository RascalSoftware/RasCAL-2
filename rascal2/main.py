import multiprocessing
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from rascal2.paths import path_for


def main():
    """Entry point function for starting RasCAL."""
    multiprocessing.freeze_support()

    app = QApplication([])
    app.setWindowIcon(QIcon(path_for("logo.png")))

    splash = QSplashScreen(QPixmap(path_for("splash.png")), Qt.WindowType.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    splash.show()
    splash.raise_()
    splash.activateWindow()
    app.processEvents()

    os.environ["DELAY_MATLAB_START"] = "1"
    from rascal2.app import start_app

    sys.exit(start_app(splash))


if __name__ == "__main__":
    main()
