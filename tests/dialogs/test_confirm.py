"""Test the confirm dialog."""

from rascal2.dialogs.confirm import ConfirmDialog


def test_confirm_init():
    """Test that we can create a confirmation dialog."""
    dlg = ConfirmDialog("Confirm Title", "Confirm?")
    assert dlg.windowTitle() == "Confirm Title"
    assert dlg.layout().itemAt(0).widget().text() == "Confirm?"
