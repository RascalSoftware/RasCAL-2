import platform
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from rascal2.dialogs.settings_dialog import SettingsDialog
from rascal2.settings import Settings
from tests.utils import edit_line_edit_text


class FakeSetting:
    def __init__(self):
        self.settings = Settings()
        self.reset_global_settings = MagicMock()
        self.set_global_settings = MagicMock()

    def __getattribute__(self, name):
        if name in ["settings", "reset_global_settings", "set_global_settings"]:
            return object.__getattribute__(self, name)
        else:
            return getattr(self.settings, name)

    def __setattr__(self, name, value):
        if name in ["settings", "reset_global_settings", "set_global_settings"]:
            object.__setattr__(self, name, value)
        else:
            setattr(self.settings, name, value)


@patch("rascal2.dialogs.settings_dialog.SETTINGS", new_callable=FakeSetting)
@patch("rascal2.dialogs.settings_dialog.MatlabHelper")
def test_setting_dialog(mock_matlab_helper, fake_setting, mock_window_view):
    mock_matlab_helper.return_value = MagicMock()
    mock_matlab_helper.return_value.matlab_dir = "matlab_2023a"

    dialog = SettingsDialog(mock_window_view)

    general_tab = dialog.tab_widget.widget(0)
    old_fontsize = general_tab.widgets["editor_fontsize"].editor.value()
    new_fontsize = old_fontsize + 5
    edit_line_edit_text(general_tab.widgets["editor_fontsize"].editor, str(new_fontsize))

    old_live_recalculate = general_tab.widgets["live_recalculate"].editor.isChecked()
    general_tab.widgets["live_recalculate"].editor.setChecked(not old_live_recalculate)

    dialog.accept_button.click()
    assert fake_setting.editor_fontsize == new_fontsize
    assert fake_setting.live_recalculate != old_live_recalculate
    fake_setting.set_global_settings.assert_called_once()

    dialog.reset_button.click()
    fake_setting.reset_global_settings.assert_called_once()


@patch("rascal2.dialogs.settings_dialog.sys", autospec=True)
@patch("rascal2.dialogs.settings_dialog.QtWidgets.QFileDialog.getOpenFileName")
@patch("rascal2.dialogs.settings_dialog.QtWidgets.QFileDialog.getExistingDirectory")
@patch("rascal2.dialogs.settings_dialog.SETTINGS", new_callable=FakeSetting)
@patch("rascal2.dialogs.settings_dialog.MatlabHelper")
def test_matlab_setup(mock_matlab_helper, _fake_setting, mock_get_dir, mock_get_file, mock_sys, mock_window_view):
    mock_matlab_helper.return_value = MagicMock()
    matlab_dir = "matlab_2023a"
    mock_matlab_helper.return_value.matlab_dir = matlab_dir

    dialog = SettingsDialog(mock_window_view)
    assert dialog.matlab_tab.matlab_path.text() == matlab_dir

    matlab_dir = "matlab_2024b.app" if platform.system() == "Darwin" else "matlab_2024b"
    mock_get_file.return_value = (matlab_dir,)
    mock_get_dir.return_value = matlab_dir
    assert not dialog.matlab_tab.changed
    dialog.matlab_tab.open_folder_selector()
    assert dialog.matlab_tab.changed
    assert dialog.matlab_tab.matlab_path.text() == matlab_dir

    with patch("rascal2.dialogs.settings_dialog.MATLAB_ARCH_FILE", new=""):
        dialog.matlab_tab.set_matlab_paths()
        mock_matlab_helper.return_value.async_start.assert_called_once()

    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, "_arch.txt")
        file.write_text("arch file")
        with patch("rascal2.dialogs.settings_dialog.MATLAB_ARCH_FILE", new=file.as_posix()):
            dialog.matlab_tab.set_matlab_paths()
            assert mock_matlab_helper.return_value.async_start.call_count == 1

            mock_sys.frozen = True
            dialog.matlab_tab.set_matlab_paths()
            arch_content = file.read_text().split("\n")
            assert len(arch_content) == 5
            assert arch_content[-1] == ""
            assert mock_matlab_helper.return_value.async_start.call_count == 2
