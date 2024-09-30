from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for


class ProjectWidget(QtWidgets.QWidget):
    """
    The Project MDI Widget
    """

    def __init__(self, parent):
        """
        Initialize widget.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__(parent)
        self.parent = parent

    def initialize_project_mdi(self):
        """Initialzes the Project MDI"""
        self.create_non_edit_view()
        self.create_edit_view()

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(self.project_widget)
        self.stacked_widget.addWidget(self.edit_project_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def toggle_view(self) -> None:
        """Toggles the project widget from edit to non-edit view"""
        if self.stacked_widget.currentIndex() == 0:
            self.setWindowTitle("Edit Project")
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.setWindowTitle("Project")
            self.stacked_widget.setCurrentIndex(0)

    def create_non_edit_view(self) -> None:
        """Creates the project widget"""
        self.project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(" Edit Project", self, objectName="bluebutton")
        self.edit_project_button.setIcon(QtGui.QIcon(path_for("edit.png")))
        self.edit_project_button.clicked.connect(self.toggle_view)
        main_layout.addWidget(self.edit_project_button, 0, 5, 1, 1)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setText(self.parent.presenter.model.project.calculation.value)
        self.calculation_type.setReadOnly(True)

        main_layout.addWidget(self.calculation_label, 1, 0, 1, 1)
        main_layout.addWidget(self.calculation_type, 1, 1, 1, 1)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setText(self.parent.presenter.model.project.model.value)
        self.model_type.setReadOnly(True)

        main_layout.addWidget(self.model_type_label, 1, 2, 1, 1)
        main_layout.addWidget(self.model_type, 1, 3, 1, 1)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_type = QtWidgets.QLineEdit(self)
        self.geometry_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.geometry_type.setText(self.parent.presenter.model.project.geometry.value)
        self.geometry_type.setReadOnly(True)

        main_layout.addWidget(self.geometry_label, 1, 4, 1, 1)
        main_layout.addWidget(self.geometry_type, 1, 5, 1, 1)

        self.project_tab = QtWidgets.QTabWidget()
        self.project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.project_tab, 2, 0, 1, 6)
        self.project_widget.setLayout(main_layout)

    def handle_domains_tab(self):
        """Displays or hides the domains tab"""
        if self.calculation_type.text() == Calculations.Domains.value:
            self.project_tab.insertTab(5, QtWidgets.QWidget(), "Domains")
        else:
            self.project_tab.removeTab(5)

    def create_edit_view(self) -> None:
        """Creates the project widget in edit mode"""

        # create widget and layout
        self.edit_project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        # save and cancel button
        self.save_project_button = QtWidgets.QPushButton(" Save Project", self, objectName="greybutton")
        self.save_project_button.setIcon(QtGui.QIcon(path_for("save-project.png")))

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self, objectName="redbutton")
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel-dark.png")))
        self.cancel_button.clicked.connect(self.toggle_view)

        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.save_project_button)
        layout.addWidget(self.cancel_button)
        main_layout.addLayout(layout)

        # calculation widgets
        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        for calc in Calculations:
            self.calculation_combobox.addItem(calc.value)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.edit_calculation_label)
        layout.addWidget(self.calculation_combobox)

        # model widgets
        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        for model in LayerModels:
            self.model_combobox.addItem(model.value)

        layout.addWidget(self.edit_model_type_label)
        layout.addWidget(self.model_combobox)

        # geometry widgets
        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_combobox = QtWidgets.QComboBox(self)
        for geo in Geometries:
            self.geometry_combobox.addItem(geo.value)

        layout.addWidget(self.edit_geometry_label)
        layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(layout)

        # edit project tabs
        self.edit_project_tab = QtWidgets.QTabWidget()

        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.edit_project_tab)

        self.edit_project_widget.setLayout(main_layout)
