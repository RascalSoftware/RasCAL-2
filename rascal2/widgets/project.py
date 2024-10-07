from functools import partial

from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for


class UndoComboBoxUpdates(QtGui.QUndoCommand):
    def __init__(self, combo_box: QtWidgets.QComboBox, selected_value: str, previous_value: str):
        super().__init__()
        self.combo_box = combo_box
        self.selected_value = selected_value
        self.previous_value = previous_value

    def undo(self):
        self.combo_box.setCurrentText(self.previous_value)


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
        self.presenter = self.parent.presenter
        self.model = self.parent.presenter.model
        self.undo_stack = QtGui.QUndoStack(self)

        self.create_project_view()
        self.create_edit_view()
        self.handle_domains_tab()
        self.update_model_project_view()

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(self.project_widget)
        self.stacked_widget.addWidget(self.edit_project_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def update_model_project_view(self) -> None:
        """Updates the project view when a new project is created or values are updated in the model."""
        if self.model.project:
            self.project_calculation = self.model.project.calculation
            self.project_model = self.model.project.model
            self.project_geometry = self.model.project.geometry

            self.inter_calculation = self.model.project.calculation
            self.inter_model = self.model.project.model
            self.inter_geometry = self.model.project.geometry
        else:
            self.project_calculation = ""
            self.project_model = ""
            self.project_geometry = ""
            self.inter_calculation = ""
            self.inter_model = ""
            self.inter_geometry = ""

        self.calculation_type.setText(self.project_calculation)
        self.model_type.setText(self.project_model)
        self.geometry_type.setText(self.project_geometry)

        self.calculation_combobox.setCurrentText(self.project_calculation)
        self.model_combobox.setCurrentText(self.project_model)
        self.geometry_combobox.setCurrentText(self.project_geometry)

    def create_project_view(self) -> None:
        """Creates the project (non-edit) veiw"""
        self.project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(
            " Edit Project", self, objectName="bluebutton", icon=QtGui.QIcon(path_for("edit.png"))
        )
        self.edit_project_button.clicked.connect(self.show_edit_view)
        main_layout.addWidget(self.edit_project_button, 0, 5)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setReadOnly(True)

        main_layout.addWidget(self.calculation_label, 1, 0, 1, 1)
        main_layout.addWidget(self.calculation_type, 1, 1, 1, 1)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setReadOnly(True)

        main_layout.addWidget(self.model_type_label, 1, 2, 1, 1)
        main_layout.addWidget(self.model_type, 1, 3, 1, 1)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_type = QtWidgets.QLineEdit(self)
        self.geometry_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.geometry_type.setReadOnly(True)

        main_layout.addWidget(self.geometry_label, 1, 4, 1, 1)
        main_layout.addWidget(self.geometry_type, 1, 5, 1, 1)

        self.project_tab = QtWidgets.QTabWidget()

        # Replace QtWidgets.QWidget() with methods to create
        # the tabs in project view.
        self.project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.project_tab, 2, 0, 1, 6)
        self.project_widget.setLayout(main_layout)

    def create_edit_view(self) -> None:
        """Creates the project widget in edit mode"""

        self.edit_project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        self.save_project_button = QtWidgets.QPushButton(" Save Project", self, objectName="greybutton")
        self.save_project_button.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_button.clicked.connect(self.save_changes)

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self, objectName="redbutton")
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel-dark.png")))
        self.cancel_button.clicked.connect(self.cancel_changes)

        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.save_project_button)
        layout.addWidget(self.cancel_button)
        main_layout.addLayout(layout)

        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        self.calculation_combobox.addItems([calc for calc in Calculations])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.edit_calculation_label)
        layout.addWidget(self.calculation_combobox)

        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        self.model_combobox.addItems([model for model in LayerModels])

        layout.addWidget(self.edit_model_type_label)
        layout.addWidget(self.model_combobox)

        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_combobox = QtWidgets.QComboBox(self)
        self.geometry_combobox.addItems([geo for geo in Geometries])

        self.calculation_combobox.currentTextChanged.connect(
            partial(self.on_combobox_update, self.calculation_combobox, "inter_calculation")
        )
        self.model_combobox.currentTextChanged.connect(
            partial(self.on_combobox_update, self.model_combobox, "inter_model")
        )
        self.geometry_combobox.currentTextChanged.connect(
            partial(self.on_combobox_update, self.geometry_combobox, "inter_geometry")
        )

        layout.addWidget(self.edit_geometry_label)
        layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(layout)

        self.edit_project_tab = QtWidgets.QTabWidget()

        # Replace QtWidgets.QWidget() with methods to create
        # the tabs in edit view.
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.edit_project_tab)

        self.edit_project_widget.setLayout(main_layout)

    def on_combobox_update(self, combo_box: QtWidgets.QComboBox, attr_name: str, selected_value: str):
        """
        Tracks changes in combo boxes and pushes them to the undo stack.

        Parameters
        ----------
        combo_box: QtWidgets.QComboBox
                The combobox on which the value is updated.
        attr_name: str
                The attr that stores the previous value selected.
        selected_value: str
                The new selected value from the combobox.
        """
        previous_value = getattr(self, attr_name)
        if previous_value != selected_value:
            command = UndoComboBoxUpdates(combo_box, selected_value, previous_value)
            self.undo_stack.push(command)
            setattr(self, attr_name, selected_value)

    def handle_domains_tab(self) -> None:
        """Displays or hides the domains tab"""
        domain_tab_ix = 5
        if (
            self.calculation_type.text() == Calculations.Domains
            and self.project_tab.tabText(domain_tab_ix) != "Domains"
            and self.edit_project_tab.tabText(domain_tab_ix) != "Domains"
        ):
            # Replace QtWidgets.QWidget() with methods to create
            # the domains tab in project and edit view.
            self.project_tab.insertTab(domain_tab_ix, QtWidgets.QWidget(), "Domains")
            self.edit_project_tab.insertTab(domain_tab_ix, QtWidgets.QWidget(), "Domains")
        elif self.calculation_type.text() != Calculations.Domains:
            self.project_tab.removeTab(domain_tab_ix)
            self.edit_project_tab.removeTab(domain_tab_ix)

    def show_project_view(self) -> None:
        """Show project view"""
        self.setWindowTitle("Project")
        self.handle_domains_tab()
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")
        self.handle_domains_tab()
        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes and clear undo stack."""
        self.undo_stack.clear()
        self.presenter.edit_project(
            self.calculation_combobox.currentText(),
            self.model_combobox.currentText(),
            self.geometry_combobox.currentText(),
        )
        self.show_project_view()

    def cancel_changes(self) -> None:
        """Cancel changes to project."""
        while self.undo_stack.canUndo():
            self.undo_stack.undo()
        self.show_project_view()
