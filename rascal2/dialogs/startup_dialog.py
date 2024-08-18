import os

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class StartUpDialog(QtWidgets.QDialog):
    """
    The Start Up Dialog
    """

    _switch_to_project_dialog = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """
        Initializes the dialog
        """
        super().__init__(parent)
        self._parent = parent
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        self.setModal(True)

        self._startup_layout = QtWidgets.QGridLayout()

        self._create_widgets()
        self._add_widgets_to_layout()

    def _add_widgets_to_layout(self):
        """
        Adds the widgets to the layout.
        """
        self._startup_layout.setVerticalSpacing(50)

        # Add banner to layout
        self._startup_layout.addWidget(self._banner_label, 0, 2, 1, 5)

        # Add buttons to layout
        self._startup_layout.addWidget(self._new_project_button, 1, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self._startup_layout.addWidget(self._import_project_button, 1, 4, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self._startup_layout.addWidget(self._load_example_button, 1, 6, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

        # Add labels to layout
        self._startup_layout.addWidget(self._new_project_label, 2, 2, 1, 1)
        self._startup_layout.addWidget(self._import_project_label, 2, 4, 1, 1)
        self._startup_layout.addWidget(self._load_example_label, 2, 6, 1, 1)

        # Add footer to layout
        self._startup_layout.addWidget(self._footer_label, 3, 2, 1, 5)

        # Set layout
        self.setLayout(self._startup_layout)

    def _create_widgets(self):
        """
        Creates the widgets for the start up dialog.
        """

        # Create the banner and the footer
        self._banner_label = QtWidgets.QLabel()
        self._banner_label.setPixmap(QtGui.QPixmap(path_for("banner.png")))

        self._footer_label = QtWidgets.QLabel()
        self._footer_label.setPixmap(QtGui.QPixmap(path_for("footer.png")))

        # Create and style the buttons
        button_style = """background-color: #0D69BB;
                          icon-size: 4em;
                          border-radius : 0.5em;
                          padding: 0.5em;"""

        self._new_project_button = QtWidgets.QPushButton()
        self._new_project_button.setIcon(QtGui.QIcon(path_for("plus.png")))
        self._new_project_button.clicked.connect(self._switch_to_project_dialog.emit)
        self._new_project_button.setStyleSheet(button_style)

        self._import_project_button = QtWidgets.QPushButton()
        self._import_project_button.setIcon(QtGui.QIcon(path_for("open-project-light.png")))
        self._import_project_button.setStyleSheet(button_style)

        self._load_example_button = QtWidgets.QPushButton()
        self._load_example_button.setIcon(QtGui.QIcon(path_for("open-examples.png")))
        self._load_example_button.setStyleSheet(button_style)

        # Create and style the labels
        label_style = "font-weight: bold; font-size: 1em;"

        self._new_project_label = QtWidgets.QLabel("New\nProject")
        self._new_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._new_project_label.setStyleSheet(label_style)

        self._import_project_label = QtWidgets.QLabel("Import Existing\nProject")
        self._import_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._import_project_label.setStyleSheet(label_style)

        self._load_example_label = QtWidgets.QLabel("Open Example\nProject")
        self._load_example_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._load_example_label.setStyleSheet(label_style)


class ProjectDialog(QtWidgets.QDialog):
    """
    The Project Dialog
    """

    _switch_to_startup_dialog = QtCore.pyqtSignal()
    _create_project = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """
        Initializes the dialog
        """
        super().__init__(parent)

        self.layout = QtWidgets.QGridLayout()
        self.setModal(True)

        self._folder_selected = False

        self._create_widgets()
        self._add_widgets_to_layout()

        self.setLayout(self.layout)

    def _add_widgets_to_layout(self):
        """
        Adds the widgets to the layout
        """
        self.layout.setVerticalSpacing(20)

        # Add project name widgets
        self.layout.addWidget(self._project_name_label, 0, 0, 1, 1)
        self.layout.addWidget(self._project_name, 0, 1, 1, 5)

        # Add project folder widgets
        self.layout.addWidget(self._project_folder_label, 1, 0, 1, 1)
        self.layout.addWidget(self._project_folder, 1, 1, 1, 3)

        # Add the buttons
        self.layout.addWidget(self._browse_button, 1, 5, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self._create_button, 2, 4, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self._cancel_button, 2, 5, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _create_widgets(self):
        """
        Creates the widgets for the project dialog.
        """

        # Create labels
        self._project_name_label = QtWidgets.QLabel("Project Name:", self)
        self._project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self._project_folder_label = QtWidgets.QLabel("Project Folder:", self)
        self._project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self._project_folder = QtWidgets.QLabel("No folder selected", self)
        self._project_folder.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self._project_name = QtWidgets.QLineEdit(self)
        self._project_name.setPlaceholderText("Enter project name")

        # Create and style the buttons
        button_style = """background-color: {};
                          color: #F2F1E8;
                          padding-top: 0.3em;
                          padding-left: 1em;
                          padding-right: 1em;
                          padding-bottom: 0.3em;
                          font-weight: bold;
                          border-radius: 0.5em"""

        self._browse_button = QtWidgets.QPushButton(" Browse", self)
        self._browse_button.setIcon(QtGui.QIcon(path_for("open-project-light.png")))
        self._browse_button.clicked.connect(self._open_folder_selector)
        self._browse_button.setStyleSheet(button_style.format("#403F3F"))

        self._create_button = QtWidgets.QPushButton(" Create", self)
        self._create_button.setIcon(QtGui.QIcon(path_for("plus.png")))
        self._create_button.clicked.connect(self._verify_inputs)
        self._create_button.setStyleSheet(button_style.format("#0D69BB"))

        self._cancel_button = QtWidgets.QPushButton(" Cancel", self)
        self._cancel_button.setIcon(QtGui.QIcon(path_for("cancel.png")))
        self._cancel_button.clicked.connect(self._cancel_project_creation)
        self._cancel_button.setStyleSheet(button_style.format("#E34234"))

    def _cancel_project_creation(self):
        """
        Cancel project creation.
        """
        self._switch_to_startup_dialog.emit()
        self._reset_variables()

    def _reset_variables(self):
        """
        Resets the variables.
        """
        self._folder_selected = False
        self._project_folder.setText("")
        self._project_name.setText("")

    def _open_folder_selector(self):
        """
        Opens the folder selector.
        """
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            files_in_folder = list(filter(lambda x: x[0] != ".", os.listdir(folder_path)))
            if files_in_folder:
                self._show_error_message(
                    text="Select a different folder",
                    info="This folder contains files. Select an empty folder.",
                    title="Warning",
                    level="critical",
                )
            else:
                self._project_folder.setText(folder_path)
                self._folder_selected = True

    def _show_error_message(self, text=None, info=None, title=None, level="info"):
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

    def _verify_inputs(self):
        """
        Verfies the inputs specified.
        """
        if self._project_name.text() != "" and self._folder_selected:
            self._create_project.emit()
            self._reset_variables()
        elif not self._project_name.text():
            self._show_error_message(
                text="Specify project name",
                info="Project name needs to be specified for project creation.",
                title="Information",
            )
        elif not self._folder_selected:
            self._show_error_message(text="Specify project folder", info="Select an empty folder", title="Information")

    def resizeEvent(self, _):
        """
        Recenters the dialog when project folder
        is selected.
        """
        if self.parent():
            self.move(self.parent().geometry().center() - self.rect().center())
