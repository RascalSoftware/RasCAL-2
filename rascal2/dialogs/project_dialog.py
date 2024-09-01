import os
from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class ProjectDialog(QtWidgets.QDialog):
    """
    The Project Dialog
    """

    _button_style = """background-color: {};
                       color: #F2F1E8;
                       padding-top: 0.3em;
                       padding-left: 1em;
                       padding-right: 1em;
                       padding-bottom: 0.3em;
                       font-weight: bold;
                       border-radius: 0.5em"""
    _label_style = "font-weight: bold"
    _error_style = "color: #E34234"
    _line_edit_error_style = "border: 1px solid #E34234"

    def __init__(self, parent=None):
        """
        Initializes the dialog
        """
        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumWidth(700)

        self.name_error = False
        self.folder_error = False

        self.create_project_dialog_labels()
        self.create_project_dialog_buttons()
        self.add_widgets_to_layout()

    def add_widgets_to_layout(self) -> None:
        """
        Adds the widgets to the layout
        """
        self.main_layout = QtWidgets.QVBoxLayout()

        self.main_layout.setSpacing(20)

        # Add project name widgets
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(2)
        layout.addWidget(self.project_name_label, 0, 0, 1, 1)
        layout.addWidget(self.project_name, 0, 1, 1, 5)
        layout.addWidget(self.project_name_error, 1, 1, 1, 5)
        self.main_layout.addLayout(layout)

        # Add project folder widgets
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(2)
        layout.addWidget(self.project_folder_label, 0, 0, 1, 1)
        layout.addWidget(self.project_folder, 0, 1, 1, 4)
        layout.addWidget(self.browse_button, 0, 5, 1, 1)
        layout.addWidget(self.project_folder_error, 1, 1, 1, 4)
        self.main_layout.addLayout(layout)

        # Add the create and cancel buttons
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(layout)

        self.setLayout(self.main_layout)

    def create_project_dialog_labels(self) -> None:
        """
        Creates the labels for the project dialog.
        """
        # Project name labels
        self.project_name_label = QtWidgets.QLabel("Project Name:", self)
        self.project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_name_label.setStyleSheet(self._label_style)

        self.project_name = QtWidgets.QLineEdit(self)
        self.project_name.setPlaceholderText("Enter project name")

        self.project_name_error = QtWidgets.QLabel("", self)
        self.project_name_error.setStyleSheet(self._error_style)
        self.project_name_error.hide()

        # Project folder labels
        self.project_folder_label = QtWidgets.QLabel("Project Folder:", self)
        self.project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_folder_label.setStyleSheet(self._label_style)

        self.project_folder = QtWidgets.QLineEdit(self)
        self.project_folder.setReadOnly(True)
        self.project_folder.setPlaceholderText("Select project folder")

        self.project_folder_error = QtWidgets.QLabel("", self)
        self.project_folder_error.setStyleSheet(self._error_style)
        self.project_folder_error.hide()

    def create_project_dialog_buttons(self) -> None:
        """
        Creates the buttons for the project dialog.
        """
        self.browse_button = QtWidgets.QPushButton(" Browse", self)
        self.browse_button.setIcon(QtGui.QIcon(path_for("open-project-light.png")))
        self.browse_button.clicked.connect(self.open_folder_selector)
        self.browse_button.setStyleSheet(self._button_style.format("#403F3F"))

        self.create_button = QtWidgets.QPushButton(" Create", self)
        self.create_button.setIcon(QtGui.QIcon(path_for("plus.png")))
        self.create_button.clicked.connect(self.create_project)
        self.create_button.setStyleSheet(self._button_style.format("#0D69BB"))

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self)
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel.png")))
        self.cancel_button.clicked.connect(self.cancel_project_creation)
        self.cancel_button.setStyleSheet(self._button_style.format("#E34234"))

    def cancel_project_creation(self) -> None:
        """
        Cancel project creation.
        """
        if self.parent().new_project_action_called:
            self.close()
        else:
            self.parent().toggleView()
        self.reset_variables()

    def reset_variables(self) -> None:
        """
        Resets the variables.
        """
        self.project_folder.setText("")
        self.project_name.setText("")
        self.name_error = False
        self.folder_error = False

    def open_folder_selector(self) -> None:
        """
        Opens the folder selector.
        """
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            files_in_folder = list(filter(lambda x: x[0] != ".", os.listdir(folder_path)))
            if files_in_folder:
                self.handle_error("folder", "Selected folder contains files. Select an empty folder.")
            else:
                self.handle_non_error("folder")
                self.project_folder.setText(folder_path)

    def handle_error(self, tag: Literal["name", "folder"], msg: str) -> None:
        """
        Displays the line edit error msgs.

        Parameters
        ----------
        tag: Literal["name", "folder"]
            Specifies whether the input verification
            is for the project name or folder.
        msg: str
            Specifies the msg to display.
        """
        input = getattr(self, "project_" + tag)
        input.setStyleSheet(self._line_edit_error_style)

        error_label = getattr(self, "project_" + tag + "_error")
        error_label.setText(msg)
        error_label.show()

        setattr(self, tag + "_error", True)

    def handle_non_error(self, tag: Literal["name", "folder"]) -> None:
        """
        Clears the style sheets of the error line edits.

        Parameters
        ----------
        tag: Literal["name", "folder"]
            Specifies whether to clear the error
            for the project name or folder.
        """
        input = getattr(self, "project_" + tag)
        input.setStyleSheet("")

        error_label = getattr(self, "project_" + tag + "_error")
        error_label.hide()

        setattr(self, tag + "_error", False)

    def verify_inputs(self, tag: Literal["name", "folder"], msg: str) -> None:
        """
        Verifies the name and folder inputs of the project dialog.

        Parameters
        ----------
        tag: Literal["name", "folder"]
            Specifies whether the input verification
            is for the project name or folder.
        msg: str
            Specifies the msg to display if there is an error
            in verification.
        """
        if getattr(self, "project_" + tag).text() == "":
            self.handle_error(tag, msg)
        else:
            self.handle_non_error(tag)

    def create_project(self) -> None:
        """
        Verifies the inputs specified.
        """
        self.verify_inputs("name", "Project name needs to be specified.")
        self.verify_inputs("folder", "An empty project folder needs to be selected.")
        if not self.name_error and not self.folder_error:
            self.parent().createNewProject()

    def resizeEvent(self, _) -> None:
        """
        Recenters the dialog when project folder is selected.
        """
        if self.parent():
            self.move(self.parent().geometry().center() - self.rect().center())
