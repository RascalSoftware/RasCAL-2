import multiprocessing
import os
import sys

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from rascal2.paths import path_for


class SplashScreen(QSplashScreen):
    """Create splash screen widget."""

    def __init__(self, *args):
        super().__init__(*args)
        self.painted = False

    def paintEvent(self, event):
        super().paintEvent(event)
        self.painted = True


def main():
    """Entry point function for starting RasCAL."""
    multiprocessing.freeze_support()

    app = QApplication([])
    app.setWindowIcon(QIcon(path_for("logo.png")))

    splash = SplashScreen(QPixmap(path_for("splash.png")), Qt.WindowType.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    splash.show()
    splash.raise_()
    splash.activateWindow()
    app.processEvents()
    for _ in range(100):
        if splash.painted:
            break
        # wait for splash to paint on linux
        QThread.usleep(100)
        app.processEvents()
    app.processEvents()

    os.environ["DELAY_MATLAB_START"] = "1"
    from rascal2.app import start_app

    sys.exit(start_app(splash))


if __name__ == "__main__":
    main()
