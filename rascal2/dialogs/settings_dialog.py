import pathlib
import platform
import sys
from contextlib import suppress

from PyQt6 import QtCore, QtWidgets

from rascal2.config import MATLAB_ARCH_FILE, MatlabHelper
from rascal2.settings import Settings, SettingsGroups, delete_local_settings
from rascal2.widgets.inputs import get_validated_input


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        """
        Dialog to adjust RasCAL-2 settings.

        Parameters
        ----------
        parent : MainWindowView
            The view of the RasCAL-2 GUI
        """
        super().__init__(parent)

        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.settings = parent.settings.copy()
        self.matlab_tab = MatlabSetupTab()
        self.reset_dialog = None

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(SettingsTab(self, SettingsGroups.General), SettingsGroups.General)
        self.tab_widget.addTab(SettingsTab(self, SettingsGroups.Plotting), SettingsGroups.Plotting)
        self.tab_widget.addTab(self.matlab_tab, "Matlab")
        self.tab_widget.setTabVisible(0, parent.presenter.model.save_path != "")
        self.tab_widget.setTabVisible(1, parent.presenter.model.save_path != "")

        self.reset_button = QtWidgets.QPushButton("Reset to Defaults", self)
        self.reset_button.clicked.connect(self.reset_default_settings)
        self.accept_button = QtWidgets.QPushButton("OK", self)
        self.accept_button.clicked.connect(self.update_settings)
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

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
        """Accept the changed settings"""
        self.parent().settings = self.settings
        if self.parent().presenter.model.save_path:
            self.parent().settings.save(self.parent().presenter.model.save_path)
        self.matlab_tab.set_matlab_paths()
        self.accept()

    def reset_default_settings(self) -> None:
        """Reset the settings to the global defaults"""
        delete_local_settings(self.parent().presenter.model.save_path)
        self.parent().settings = Settings()
        self.accept()


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: SettingsDialog, group: SettingsGroups):
        """A tab in the Settings Dialog tab layout.

        Parameters
        ----------
        parent : SettingsDialog
            The dialog in which this tab lies
        group : SettingsGroups
            The set of settings with this value in "title" field of the
            Settings object's "field_info" will be included in this tab.
        """
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
        """A slot that updates the given setting in the dialog's copy of the Settings object.

        Connect this (via a lambda) to the "edited_signal" of the corresponding widget.

        Parameters
        ----------
        setting : str
            The name of the setting to be modified by this slot
        """
        setattr(self.settings, setting, self.widgets[setting].get_data())


class MatlabSetupTab(QtWidgets.QWidget):
    def __init__(self):
        """Dialog to adjust Matlab location settings."""
        super().__init__()

        form_layout = QtWidgets.QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(0)

        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(QtWidgets.QLabel("Current Matlab Directory:"))
        label_layout.addStretch(1)
        self.matlab_path = QtWidgets.QLineEdit(self)
        self.matlab_path.setText(MatlabHelper().get_matlab_path())
        self.matlab_path.setReadOnly(True)
        self.matlab_path.setPlaceholderText("Select MATLAB directory")
        self.matlab_path.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        browse_button = QtWidgets.QPushButton("Browse", objectName="BrowseButton")
        browse_button.clicked.connect(self.open_folder_selector)
        form_layout.addWidget(self.matlab_path, 0, 0, 1, 4)
        form_layout.addWidget(browse_button, 0, 4, 1, 1)

        main_layout = QtWidgets.QVBoxLayout()
        if not getattr(sys, "frozen", False):
            self.setEnabled(False)
            main_layout.addWidget(
                QtWidgets.QLabel(
                    "<b>The current matlab path can only be changed when running in bundle.<br/>"
                    "For non-bundle, You can change which Matlab to use by pip installing a <br/>"
                    "different version of matlabengine."
                )
            )
        main_layout.addLayout(label_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)

        self.setLayout(main_layout)
        self.changed = False

    def open_folder_selector(self) -> None:
        """Open folder selector."""
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(self, "Select MATLAB Directory", ".")
        if folder_name:
            self.matlab_path.setText(folder_name)
            self.changed = True

    def set_matlab_paths(self):
        """Update MATLAB paths in arch file"""
        if not self.changed:
            return

        should_init = False
        with suppress(FileNotFoundError), open(MATLAB_ARCH_FILE, "r+") as path_file:
            install_dir = pathlib.Path(self.matlab_path.text())
            if not getattr(sys, "frozen", False):
                return

            if len(path_file.readlines()) == 0:
                should_init = True

            path_file.truncate(0)

            arch = "win64" if platform.system() == "Windows" else "glnxa64"
            path_file.writelines(
                [
                    f"{arch}\n",
                    str(install_dir / f"bin/{arch}\n"),
                    str(install_dir / f"extern/engines/python/dist/matlab/engine/{arch}\n"),
                    str(install_dir / f"extern/bin/{arch}\n"),
                ]
            )
        if should_init:
            MatlabHelper().async_start()
