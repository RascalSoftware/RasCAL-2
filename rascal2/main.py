import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QApplication, QSplashScreen


def main():
    app = QApplication([])

    SOURCE_PATH = Path(sys.executable).parent.parent
    if Path(SOURCE_PATH / "MacOS").is_dir():
        SOURCE_PATH = SOURCE_PATH / "Resources"
    IMAGE_PATH = SOURCE_PATH / "static" / "images"

    app.setWindowIcon(QIcon(str(IMAGE_PATH / "logo.png")))

    splash = QSplashScreen(QPixmap(str(IMAGE_PATH / "splash.png")),
                           Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    splash.raise_()
    splash.activateWindow()
    app.processEvents()

    from app import start_app
    start_app(splash)


if __name__ == "__main__":
    main()
