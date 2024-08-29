"""Tests for the terminal widget."""

from rascal2.widgets.terminal import TerminalWidget


def test_append_text():
    """Test that text can be successfully appended to the terminal."""
    wg = TerminalWidget()
    wg.append_text("test text")
    assert "test text" in wg.text_area.toPlainText()


def test_clear():
    """Test that the terminal clearing works."""
    wg = TerminalWidget()
    wg.append_text("test text")
    wg.clear()
    assert wg.text_area.toPlainText() == ""
