"""Mocks for testing the Controls widget."""

from PyQt6 import QtWidgets
from RATapi import Controls


class MockWindowModel:
    """A mock MainWindowModel object."""

    def __init__(self):
        self.controls = Controls()


class MockUndoStack:
    """A mock Undo stack."""

    def __init__(self):
        self.stack = []

    def push(self, command):
        command.redo()


class MockPresenter:
    """A mock Presenter."""

    def __init__(self):
        self.undo_stack = MockUndoStack()
        self.model = MockWindowModel()
        self.errors_thrown = []
        self.terminal_interrupted = False

    def interrupt_terminal(self):
        self.terminal_interrupted = True


class MockWindowView(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()

        self.setCentralWidget(QtWidgets.QWidget())
