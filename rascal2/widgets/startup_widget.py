from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class StartUpWidget(QtWidgets.QWidget):
    """
    The Start Up Widget
    """

    def __init__(self, parent=None):
        """
        Initializes the Widget
        """
        super().__init__(parent)

        self.create_banner_and_footer()

        self.create_widgets_for_startup_page()
        self.add_widgets_to_startup_page_layout()

        self.create_widgets_for_load_page()
        self.add_widgets_to_load_page_layout()

        self.create_main_layout()

    def create_main_layout(self):
        """
        Creates the main layout.
        """
        # Create the stacked layout
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(self.startup_page)
        self.stacked_widget.addWidget(self.load_page)

        # Create the main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(50)
        main_layout.addStretch(1)
        main_layout.addWidget(self.banner_label)
        main_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.footer_label)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def create_banner_and_footer(self):
        """
        Creates the banner and the footer.
        """
        self.banner_label = QtWidgets.QLabel()
        self.banner_label.setPixmap(QtGui.QPixmap(path_for("banner.png")))
        self.banner_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.footer_label = QtWidgets.QLabel()
        self.footer_label.setPixmap(QtGui.QPixmap(path_for("footer.png")))
        self.footer_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def add_widgets_to_startup_page_layout(self):
        """
        Adds the buttons and labels to the startup layout.
        """
        self.startup_page = QtWidgets.QWidget()
        startup_layout = QtWidgets.QVBoxLayout()

        startup_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        startup_layout.setSpacing(30)

        # Add buttons to startup layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.new_project_button)
        button_layout.addWidget(self.import_project_button)
        button_layout.addWidget(self.load_example_button)
        startup_layout.addLayout(button_layout)

        # Add labels to startup layout
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(self.new_project_label)
        label_layout.addWidget(self.import_project_label)
        label_layout.addWidget(self.load_example_label)
        startup_layout.addLayout(label_layout)

        self.startup_page.setLayout(startup_layout)

    def add_widgets_to_load_page_layout(self):
        """
        Adds the buttons and labels to the load layout.
        """
        self.load_page = QtWidgets.QWidget()
        load_layout = QtWidgets.QVBoxLayout()

        load_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        load_layout.setSpacing(30)

        # Add buttons to load layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.import_r1_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.import_rascal_button)
        load_layout.addLayout(button_layout)

        # Add labels to load layout
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(self.import_r1_label)
        label_layout.addWidget(self.cancel_label)
        label_layout.addWidget(self.import_rascal_label)
        load_layout.addLayout(label_layout)

        self.load_page.setLayout(load_layout)

    def create_widgets_for_startup_page(self):
        """
        Creates the buttons and labels for the startup page.
        """

        # Create and style the startup buttons
        button_style = """background-color: #0D69BB;
                          icon-size: 4em;
                          border-radius : 0.5em;
                          padding: 0.5em;
                          margin-left: 5em;
                          margin-right: 5em;"""

        self.new_project_button = QtWidgets.QPushButton()
        self.new_project_button.setIcon(QtGui.QIcon(path_for("plus.png")))
        self.new_project_button.clicked.connect(self.parent().toggleView)
        self.new_project_button.setStyleSheet(button_style)

        self.import_project_button = QtWidgets.QPushButton()
        self.import_project_button.setIcon(QtGui.QIcon(path_for("open-project-light.png")))
        self.import_project_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.import_project_button.setStyleSheet(button_style)

        self.load_example_button = QtWidgets.QPushButton()
        self.load_example_button.setIcon(QtGui.QIcon(path_for("open-examples.png")))
        self.load_example_button.setStyleSheet(button_style)

        # Create and style the startup labels
        label_style = "font-weight: bold; font-size: 1em;"

        self.new_project_label = QtWidgets.QLabel("New\nProject")
        self.new_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.new_project_label.setStyleSheet(label_style)

        self.import_project_label = QtWidgets.QLabel("Import Existing\nProject")
        self.import_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.import_project_label.setStyleSheet(label_style)

        self.load_example_label = QtWidgets.QLabel("Open Example\nProject")
        self.load_example_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.load_example_label.setStyleSheet(label_style)

    def create_widgets_for_load_page(self):
        """
        Creates the buttons and labels for the load page.
        """

        # Create and style the load buttons
        button_style = """background-color: {};
                          icon-size: 4em;
                          border-radius : 0.5em;
                          padding: 0.5em;
                          margin-left: 5em;
                          margin-right: 5em;"""

        self.import_r1_button = QtWidgets.QPushButton()
        self.import_r1_button.setIcon(QtGui.QIcon(path_for("import-r1.png")))
        self.import_r1_button.setStyleSheet(button_style.format("#0D69BB"))

        self.cancel_button = QtWidgets.QPushButton()
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cross.png")))
        self.cancel_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.cancel_button.setStyleSheet(button_style.format("#E34234"))

        self.import_rascal_button = QtWidgets.QPushButton()
        self.import_rascal_button.setIcon(QtGui.QIcon(path_for("import-rascal.png")))
        self.import_rascal_button.setStyleSheet(button_style.format("#0D69BB"))

        # Create and style the load labels
        label_style = "font-weight: bold; font-size: 1em;"

        self.import_r1_label = QtWidgets.QLabel("Import R1\nProject")
        self.import_r1_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.import_r1_label.setStyleSheet(label_style)

        self.cancel_label = QtWidgets.QLabel("Cancel")
        self.cancel_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cancel_label.setStyleSheet(label_style)

        self.import_rascal_label = QtWidgets.QLabel("Import RasCAL\nProject")
        self.import_rascal_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.import_rascal_label.setStyleSheet(label_style)
