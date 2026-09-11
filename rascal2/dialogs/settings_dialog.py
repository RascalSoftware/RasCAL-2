import pathlib
import platform
import sys
from contextlib import suppress

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import LOGGER, SETTINGS, MatlabHelper
from rascal2.paths import MATLAB_ARCH_FILE
from rascal2.settings import SettingsGroups, change_ui_style, get_global_settings
from rascal2.theme import IconEngine
from rascal2.widgets.inputs import get_validated_input


class SettingsDialog(QtWidgets.QDialog):
    """Dialog to adjust RasCAL-2 settings.

    Parameters
    ----------
    parent : MainWindowView
        The view of the RasCAL-2 GUI
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.settings = SETTINGS.copy()
        self.matlab_tab = MatlabSetupTab()
        self.reset_dialog = None

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(SettingsTab(self, SettingsGroups.General), SettingsGroups.General)
        self.tab_widget.addTab(SettingsTab(self, SettingsGroups.Plotting), SettingsGroups.Plotting)
        self.tab_widget.addTab(self.matlab_tab, "Matlab")

        self.reset_button = QtWidgets.QPushButton("Reset to Defaults", self)
        self.reset_button.clicked.connect(self.reset_default_settings)
        self.accept_button = QtWidgets.QPushButton("OK", self)
        self.accept_button.clicked.connect(self.update_settings)
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.cancel_settings)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Settings")

    def update_settings(self) -> None:
        """Accept the changed settings."""
        vars(SETTINGS).update(vars(self.settings))
        SETTINGS.set_global_settings()
        self.matlab_tab.set_matlab_paths()
        self.accept()

    def reset_default_settings(self) -> None:
        """Reset the settings to the global defaults."""
        SETTINGS.reset_global_settings()
        change_ui_style(SETTINGS.model_fields["style"].default)
        self.accept()

    def cancel_settings(self):
        if SETTINGS.style != self.settings.style:
            change_ui_style(SETTINGS.style)
        self.reject()


class SettingsTab(QtWidgets.QWidget):
    """A tab in the Settings Dialog tab layout.

    Parameters
    ----------
    parent : SettingsDialog
        The dialog in which this tab lies
    group : SettingsGroups
        The set of settings with this value in "title" field of the
        Settings object's "field_info" will be included in this tab.
    """

    def __init__(self, parent: SettingsDialog, group: SettingsGroups):
        super().__init__(parent)

        self.settings = parent.settings
        self.widgets = {}
        tab_layout = QtWidgets.QGridLayout()

        field_info = self.settings.model_fields
        group_settings = [key for (key, value) in field_info.items() if value.title == group]

        for i, setting in enumerate(group_settings):
            label_text = setting.replace("_", " ").title()
            label = QtWidgets.QLabel(label_text)
            label.setToolTip(field_info[setting].description)
            tab_layout.addWidget(label, i, 0)
            self.widgets[setting] = get_validated_input(field_info[setting])
            try:
                self.widgets[setting].set_data(getattr(self.settings, setting))
            except TypeError:
                self.widgets[setting].set_data(str(getattr(self.settings, setting)))
            self.widgets[setting].edited_signal.connect(lambda ignore=None, s=setting: self.modify_setting(s))
            tab_layout.addWidget(self.widgets[setting], i, 1)

        tab_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(tab_layout)

    def modify_setting(self, setting: str):
        """Update the given setting in the dialog's copy of the Settings object.

        Connect this slot (via a lambda) to the "edited_signal" of the corresponding widget.

        Parameters
        ----------
        setting : str
            The name of the setting to be modified by this slot
        """
        setattr(self.settings, setting, self.widgets[setting].get_data())

        match setting:
            case "style":
                change_ui_style(self.widgets[setting].get_data())


class MatlabSetupTab(QtWidgets.QWidget):
    """Dialog to adjust Matlab location settings."""

    def __init__(self):
        super().__init__()

        form_layout = QtWidgets.QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(0)

        matlab_dir_label = QtWidgets.QLabel("Current Matlab Directory:")
        form_layout.addWidget(matlab_dir_label, 0, 0, 1, 6)
        self.matlab_path = QtWidgets.QLineEdit(self)
        self.matlab_path.setText(MatlabHelper().matlab_dir)
        self.matlab_path.setReadOnly(True)
        self.matlab_path.setPlaceholderText("Select MATLAB directory")
        self.matlab_path.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        browse_button = QtWidgets.QPushButton(QtGui.QIcon(IconEngine("browse-light.png")), "Browse")
        browse_button.clicked.connect(self.open_folder_selector)
        form_layout.addWidget(self.matlab_path, 1, 0, 1, 5)
        form_layout.addWidget(browse_button, 1, 5, 1, 1)

        if not getattr(sys, "frozen", False):
            browse_button.setEnabled(False)
            desc_text = (
                "<b>The current matlab path can only be changed when running in bundle.<br/>"
                "For non-bundle, You can change which Matlab to use by pip installing a "
                "different version <br/>of matlabengine.</b>"
            )
            matlab_dir_label.setText(f"{matlab_dir_label.text()}<br/>{desc_text}")

        desc_label = QtWidgets.QLabel(
            "MATLAB RAT Directory (Optional):<br/>"
            "<i>Running fully in MATLAB can provide more performance for custom files.</i>"
        )
        form_layout.addWidget(desc_label, 3, 0, 1, 6)
        self.rat_path = QtWidgets.QLineEdit(self)
        self.rat_path.setText(get_global_settings().value("matlab_rat_path", ""))
        self.rat_path.setReadOnly(True)
        self.rat_path.setPlaceholderText("Select MATLAB RAT directory")
        self.rat_path.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(lambda: self.set_matlab_rat_dir(clear=False))
        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.set_matlab_rat_dir(clear=True))
        form_layout.addWidget(self.rat_path, 4, 0, 1, 4)
        form_layout.addWidget(browse_button, 4, 4, 1, 1)
        form_layout.addWidget(clear_button, 4, 5, 1, 1)
        form_layout.setRowStretch(5, 1)

        self.setLayout(form_layout)
        self.changed = False

    def open_folder_selector(self) -> None:
        """Open folder selector."""
        if platform.system() == "Darwin":
            folder_name = QtWidgets.QFileDialog.getOpenFileName(self, "Select MATLAB Application", filter="(*.app)")[0]
        else:
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select MATLAB Directory", self.matlab_path.text()
            )
        if folder_name:
            self.matlab_path.setText(folder_name)
            self.changed = True

    def set_matlab_rat_dir(self, clear=False):
        if clear:
            self.rat_path.setText("")
            get_global_settings().remove("matlab_rat_path")
        else:
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select MATLAB Directory", self.rat_path.text()
            )
            if folder_name:
                self.rat_path.setText(folder_name)
                get_global_settings().setValue("matlab_rat_path", folder_name)

    def set_matlab_paths(self):
        """Update MATLAB paths in arch file."""
        if not self.changed:
            return

        with suppress(FileNotFoundError), open(MATLAB_ARCH_FILE, "r+") as path_file:
            try:
                install_dir = pathlib.Path(self.matlab_path.text())
                if not getattr(sys, "frozen", False):
                    return

                path_file.seek(0)
                if platform.system() == "Windows":
                    arch = "win64"
                elif platform.system() == "Darwin":
                    arch = "maca64" if platform.mac_ver()[-1] == "arm64" else "maci64"
                else:
                    arch = "glnxa64"
                path_file.writelines(
                    [
                        f"{arch}\n",
                        str(install_dir / f"bin/{arch}\n"),
                        str(install_dir / f"extern/engines/python/dist/matlab/engine/{arch}\n"),
                        str(install_dir / f"extern/bin/{arch}\n"),
                    ]
                )
                path_file.truncate()
            except Exception as ex:
                LOGGER.error("exception occurred", exc_info=ex)

        MatlabHelper().async_start()
