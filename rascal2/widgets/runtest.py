from PyQt6.QtWidgets import QApplication, QMainWindow
from rascal2.ui.model import MainWindowModel
from rascal2.widgets.controls_widget import ControlsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        model = MainWindowModel()
        widget = ControlsWidget(model)
        self.setCentralWidget(widget)


app = QApplication([])

window = MainWindow()
window.show()

app.exec()