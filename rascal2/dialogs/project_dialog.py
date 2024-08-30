import os

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class ProjectDialog(QtWidgets.QDialog):
    """
    The Project Dialog
    """

    def __init__(self, parent=None):
        """
        Initializes the dialog
        """
        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)

        self.layout = QtWidgets.QGridLayout()
        self.setModal(True)

        self.folder_selected = False

        self.create_widgets()
        self.add_widgets_to_layout()

        self.setLayout(self.layout)

    def add_widgets_to_layout(self):
        """
        Adds the widgets to the layout
        """
        self.layout.setVerticalSpacing(20)

        # Add project name widgets
        self.layout.addWidget(self.project_name_label, 0, 0, 1, 1)
        self.layout.addWidget(self.project_name, 0, 1, 1, 5)

        # Add project folder widgets
        self.layout.addWidget(self.project_folder_label, 1, 0, 1, 1)
        self.layout.addWidget(self.project_folder, 1, 1, 1, 3)

        # Add the buttons
        self.layout.addWidget(self.browse_button, 1, 5, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.create_button, 2, 4, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.cancel_button, 2, 5, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

    def create_widgets(self):
        """
        Creates the widgets for the project dialog.
        """

        # Create labels
        self.project_name_label = QtWidgets.QLabel("Project Name:", self)
        self.project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.project_folder_label = QtWidgets.QLabel("Project Folder:", self)
        self.project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.project_folder = QtWidgets.QLabel("No folder selected", self)
        self.project_folder.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.project_name = QtWidgets.QLineEdit(self)
        self.project_name.setPlaceholderText("Enter project name")

        # Create and style the buttons
        button_style = """background-color: {};
                          color: #F2F1E8;
                          padding-top: 0.3em;
                          padding-left: 1em;
                          padding-right: 1em;
                          padding-bottom: 0.3em;
                          font-weight: bold;
                          border-radius: 0.5em"""

        self.browse_button = QtWidgets.QPushButton(" Browse", self)
        self.browse_button.setIcon(QtGui.QIcon(path_for("open-project-light.png")))
        self.browse_button.clicked.connect(self.open_folder_selector)
        self.browse_button.setStyleSheet(button_style.format("#403F3F"))

        self.create_button = QtWidgets.QPushButton(" Create", self)
        self.create_button.setIcon(QtGui.QIcon(path_for("plus.png")))
        self.create_button.clicked.connect(self.verify_inputs)
        self.create_button.setStyleSheet(button_style.format("#0D69BB"))

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self)
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel.png")))
        self.cancel_button.clicked.connect(self.cancel_project_creation)
        self.cancel_button.setStyleSheet(button_style.format("#E34234"))

    def cancel_project_creation(self):
        """
        Cancel project creation.
        """
        if self.parent().new_project_action_called:
            self.close()
        else:
            self.parent().toggleView()
        self.reset_variables()

    def reset_variables(self):
        """
        Resets the variables.
        """
        self.folder_selected = False
        self.project_folder.setText("")
        self.project_name.setText("")

    def open_folder_selector(self):
        """
        Opens the folder selector.
        """
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            files_in_folder = list(filter(lambda x: x[0] != ".", os.listdir(folder_path)))
            if files_in_folder:
                self.show_error_message(
                    text="Select a different folder",
                    info="This folder contains files. Select an empty folder.",
                    title="Warning",
                    level="critical",
                )
            else:
                self.project_folder.setText(folder_path)
                self.folder_selected = True

    def show_error_message(self, text=None, info=None, title=None, level="info"):
        """
        Displays the error message.
        """
        error_msg = QtWidgets.QMessageBox(self)
        if level == "critical":
            error_msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        elif level == "info":
            error_msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        error_msg.setText(text)
        error_msg.setInformativeText(info)
        error_msg.setWindowTitle(title)
        error_msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        error_msg.exec()

    def verify_inputs(self):
        """
        Verifies the inputs specified.
        """
        if self.project_name.text() != "" and self.folder_selected:
            self.parent().createNewProject()
            self.reset_variables()
        elif not self.project_name.text():
            self.show_error_message(
                text="Specify project name",
                info="Project name needs to be specified for project creation.",
                title="Information",
            )
        elif not self.folder_selected:
            self.show_error_message(text="Specify project folder", info="Select an empty folder", title="Information")

    def resizeEvent(self, _):
        """
        Recenters the dialog when project folder is selected.
        """
        if self.parent():
            self.move(self.parent().geometry().center() - self.rect().center())
