"""Mocks for testing the Controls widget."""

from RATapi import Controls


class MockWindowModel:
    """A mock MainWindowModel object."""

    def __init__(self, procedure):
        self.controls = Controls(procedure=procedure)


class MockUndoStack:
    def __init__(self):
        self.stack = []

    def push(self, command):
        command.redo()


class MockPresenter:
    """A mock Presenter hooked into the model."""

    def __init__(self, procedure):
        self.undo_stack = MockUndoStack()
        self.model = MockWindowModel(procedure)
        self.errors_thrown = []

    def throwErrorDialog(self, error: Exception):
        raise error
