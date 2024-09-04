"""Widget for setting up the Controls class."""

from typing import Callable

from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.controls import common_fields, fields
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.widgets.inputs import ValidatedInputWidget


class ControlsWidget(QtWidgets.QWidget):
    """Widget for editing the Controls window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.presenter = parent.presenter

        # create fit settings view and setup connection to model
        self.fit_settings_layout = QtWidgets.QStackedLayout()
        for procedure in Procedures:
            fit_set = FitSettingsWidget(self, procedure, self.presenter)
            self.fit_settings_layout.addWidget(fit_set)

        self.fit_settings = QtWidgets.QWidget()
        self.fit_settings.setLayout(self.fit_settings_layout)
        self.fit_settings.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        # set initial procedure to whatever is in the Controls object
        init_procedure = [p.value for p in Procedures].index(self.presenter.model.controls.procedure)
        self.set_procedure(init_procedure)

        # create run and stop buttons
        self.run_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("play.png")), text="Run")
        self.run_button.toggled.connect(self.toggle_run_button)
        self.run_button.setStyleSheet("background-color: green;")
        self.run_button.setCheckable(True)

        self.stop_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("stop.png")), text="Stop")
        self.stop_button.pressed.connect(self.presenter.interrupt_terminal)
        self.stop_button.pressed.connect(self.run_button.toggle)
        self.stop_button.setStyleSheet("background-color: red;")
        self.stop_button.setEnabled(False)

        # validation label for if user tries to run with invalid controls
        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setStyleSheet("color : red")
        self.validation_label.font().setPointSize(10)
        self.validation_label.setWordWrap(True)
        self.validation_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        self.validation_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        # create box containing chi-squared value
        chi_layout = QtWidgets.QHBoxLayout()
        self.chi_squared = QtWidgets.QLineEdit("1.060")  # TODO hook this up when we can actually run... issue #9
        self.chi_squared.setReadOnly(True)
        chi_layout.addWidget(QtWidgets.QLabel("Current chi-squared:"))
        chi_layout.addWidget(self.chi_squared)
        chi_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # create dropdown to choose procedure
        procedure_layout = QtWidgets.QHBoxLayout()
        procedure_layout.addWidget(QtWidgets.QLabel("Procedure:"))
        self.procedure_dropdown = QtWidgets.QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.setCurrentIndex(init_procedure)
        self.procedure_dropdown.currentIndexChanged.connect(self.set_procedure)
        procedure_layout.addWidget(self.procedure_dropdown)

        # create button to hide/show fit settings
        self.fit_settings_button = QtWidgets.QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.setChecked(True)

        # compose buttons & widget
        buttons_layout = QtWidgets.QVBoxLayout()
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        procedure_box = QtWidgets.QVBoxLayout()
        procedure_box.addLayout(chi_layout)
        procedure_box.addLayout(buttons_layout)
        procedure_box.addLayout(procedure_layout)
        procedure_box.addWidget(self.fit_settings_button, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)
        procedure_box.addWidget(self.validation_label, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.addLayout(procedure_box)
        widget_layout.addWidget(self.fit_settings)

        self.setLayout(widget_layout)

    def toggle_fit_settings(self, toggled: bool):
        """Toggle whether the fit settings table is visible.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            self.fit_settings.show()
            self.fit_settings_button.setText("Hide fit settings")
        else:
            self.fit_settings.hide()
            self.fit_settings_button.setText("Show fit settings")

    def toggle_run_button(self, toggled: bool):
        """Toggle whether the optimisation is currently running.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            invalid_inputs = self.fit_settings_layout.currentWidget().get_invalid_inputs()
            if invalid_inputs:
                # can use an f-string in Python 3.12 and up for the fit settings,
                # but below that you cannot put '\n' in an f-string
                # so we use this method for compatibility
                self.validation_label.setText(
                    "Could not run due to invalid fit settings:\n    "
                    + "\n    ".join(invalid_inputs)
                    + "\nFix these inputs and try again.\n"
                    "See fit settings for more details.\n"
                )
                self.run_button.setChecked(False)
                return
            self.validation_label.setText("")
            self.fit_settings.setEnabled(False)
            self.procedure_dropdown.setEnabled(False)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            # TODO some functional stuff... issue #9
            # self.presenter.run() etc.
            # presenter should send a signal when run is completed,
            # which then toggles the button back
        else:
            self.fit_settings.setEnabled(True)
            self.procedure_dropdown.setEnabled(True)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def set_procedure(self, index: int):
        """Change the Controls procedure and update the table.

        Parameters
        ----------
        index : int
            The index of the procedure to change to in the procedure list.

        """
        self.fit_settings_layout.setCurrentIndex(index)
        procedure = [p.value for p in Procedures][index]
        self.presenter.editControls("procedure", procedure)
        # synchronise common fields between procedures
        for field in common_fields:
            if field not in ["procedure", "resampleParams"]:  # FIXME remove resampleparams when merged
                self.fit_settings_layout.currentWidget().update_data(field)


class FitSettingsWidget(QtWidgets.QWidget):
    """Widget containing the fit settings form.

    Parameters
    ----------
    parent : QWidget
        The parent widget of this widget.
    procedure : Procedures
        The procedure that this widget should get its settings from.
    presenter : MainWindowPresenter
        The RasCAL presenter.

    """

    def __init__(self, parent, procedure: Procedures, presenter):
        super().__init__(parent)
        self.presenter = presenter
        self.rows = {}
        self.datasetter = {}
        self.val_labels = {}
        self.visible_settings = [f for f in fields.get(procedure, []) if f != "procedure"]
        self.visible_settings.remove("resampleParams")  # FIXME remove when merged - just for testing

        settings_grid = QtWidgets.QGridLayout()
        settings_grid.setContentsMargins(10, 10, 10, 10)
        controls_fields = self.presenter.getControlsAttribute("model_fields")
        for i, setting in enumerate(self.visible_settings):
            field_info = controls_fields[setting]
            self.rows[setting] = ValidatedInputWidget(field_info)
            self.datasetter[setting] = self.create_model_data_setter(setting)
            self.rows[setting].edited_signal.connect(self.datasetter[setting])
            label = QtWidgets.QLabel(setting)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.val_labels[setting] = QtWidgets.QLabel()
            self.val_labels[setting].setStyleSheet("QLabel { color : red; }")
            self.val_labels[setting].font().setPointSize(10)
            self.val_labels[setting].setWordWrap(True)
            self.val_labels[setting].setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            self.update_data(setting)
            settings_grid.addWidget(label, 2 * i, 0)
            settings_grid.addWidget(self.rows[setting], 2 * i, 1)
            settings_grid.addWidget(self.val_labels[setting], 2 * i + 1, 1)

        settings_grid.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        fit_settings = QtWidgets.QWidget(self)
        fit_settings.setLayout(settings_grid)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(fit_settings)
        scroll_area.setWidgetResizable(True)
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(scroll_area)

        self.setLayout(widget_layout)

    def update_data(self, setting):
        """Update the view to match the data in the model.
        
        Parameters
        ----------
        setting : str
            The setting to update.

        """
        try:
            self.rows[setting].set_data(self.presenter.getControlsAttribute(setting))
        except TypeError:
            self.rows[setting].set_data(str(self.presenter.getControlsAttribute(setting)))

    def create_model_data_setter(self, setting: str) -> Callable:
        """Create a model data setter for a fit setting.

        Parameters
        ----------
        setting : str
            The setting to which the setter connects.

        Returns
        -------
        Callable
            A function which sets the model data to the current value of the view input.

        """

        def set_model_data():
            value = self.rows[setting].get_data()
            result = self.presenter.editControls(setting, value)
            if result is False:
                self.set_validation_text(setting, self.presenter.last_validation_error.errors()[0]["msg"])
            else:
                self.set_validation_text(setting, "")

        return set_model_data

    def get_invalid_inputs(self) -> list[str]:
        """Return all control inputs which are currently not valid.

        Returns
        -------
        list[str]
            A list of setting names which are currently not valid.

        """
        return [s for s in self.val_labels if self.val_labels[s].text() != ""]

    def set_validation_text(self, setting, text):
        """Set validation text on an invalid setting.

        Parameters
        ----------
        setting : str
            The setting which is invalid.
        text : str
            The error message to provide under the setting.

        """
        self.val_labels[setting].setText(text)
        if text == "":
            self.rows[setting].editor.setStyleSheet("")
        else:
            self.rows[setting].editor.setStyleSheet("color : red")
