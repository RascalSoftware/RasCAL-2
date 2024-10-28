"""Widget for the Project window."""

from enum import Enum
from copy import deepcopy

import RATapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for
from rascal2.widgets.delegates import ValidatedInputDelegate, ValueSpinBoxDelegate


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
        self.parent_model = self.parent.presenter.model

        self.parent_model.project_updated.connect(self.update_project_view)

        self.tabs = {
            "Parameters": ["parameters"],
            "Experimental Parameters": ["scalefactors", "bulk_in", "bulk_out"],
            "Layers": [],
            "Data": [],
            "Backgrounds": [],
            "Domains": [],
            "Contrasts": [],
        }
        self.view_tabs = {}
        self.edit_tabs = {}
        self.draft_project = None

        project_view = self.create_project_view()
        project_edit = self.create_edit_view()

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(project_view)
        self.stacked_widget.addWidget(project_edit)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def create_project_view(self) -> None:
        """Creates the project (non-edit) view"""
        project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(
            "Edit Project", self, objectName="bluebutton", icon=QtGui.QIcon(path_for("edit.png"))
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

        for tab, fields in self.tabs.items():
            widget = self.view_tabs[tab] = ProjectTabViewWidget(fields, self)
            self.project_tab.addTab(widget, tab)

        main_layout.addWidget(self.project_tab, 2, 0, 1, 6)
        project_widget.setLayout(main_layout)

        return project_widget

    def create_edit_view(self) -> None:
        """Creates the project edit view"""

        edit_project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        self.save_project_button = QtWidgets.QPushButton("Save Project", self, objectName="greybutton")
        self.save_project_button.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_button.clicked.connect(self.save_changes)

        self.cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="redbutton")
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

        self.calculation_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"calculation": s}))
        self.model_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"model": s}))
        self.geometry_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"geometry": s}))

        layout.addWidget(self.edit_geometry_label)
        layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(layout)

        self.edit_project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.edit_tabs[tab] = ProjectTabEditWidget(fields, self)
            self.edit_project_tab.addTab(widget, tab)

        main_layout.addWidget(self.edit_project_tab)

        edit_project_widget.setLayout(main_layout)

        return edit_project_widget

    def update_project_view(self) -> None:
        """Updates the project view."""
        # draft project is a dict containing all the attributes of the parent model,
        # because we don't want validation errors going off while editing the model is in-progress
        self.draft_project: dict = create_draft_project(self.parent_model.project) 

        self.calculation_type.setText(self.parent_model.project.calculation)
        self.model_type.setText(self.parent_model.project.model)
        self.geometry_type.setText(self.parent_model.project.geometry)

        self.calculation_combobox.setCurrentText(self.parent_model.project.calculation)
        self.model_combobox.setCurrentText(self.parent_model.project.model)
        self.geometry_combobox.setCurrentText(self.parent_model.project.geometry)

        for tab in self.tabs:
            self.view_tabs[tab].update_model(self.parent_model.project)
            self.edit_tabs[tab].update_model(self.draft_project)

        self.handle_domains_tab()

    def update_draft_project(self, new_values: dict) -> None:
        """
        Updates the draft project.

        Parameters
        ----------
        new_values: dict
            A dictionary of new values to update in the draft project.

        """
        self.draft_project.update(new_values)

    def handle_domains_tab(self) -> None:
        """Displays or hides the domains tab"""
        domain_tab_index = 5
        self.project_tab.setTabVisible(
            domain_tab_index, self.calculation_combobox.currentText() == Calculations.Domains
        )

    def show_project_view(self) -> None:
        """Show project view"""
        self.setWindowTitle("Project")
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")
        self.update_project_view()
        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes to the project."""
        self.parent.presenter.replace_project(self.draft_project)
        self.update_project_view()
        self.show_project_view()

    def cancel_changes(self) -> None:
        """Cancel changes to the project."""
        self.update_project_view()
        self.show_project_view()


class ClassListModel(QtCore.QAbstractTableModel):
    """Table model for a project ClassList field.

    Parameters
    ----------
    classlist : ClassList
        The initial classlist to represent in this model.
    parent : QtWidgets.QWidget
        The parent widget for the model.

    """

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.classlist = classlist
        self.item_type = classlist._class_handle
        self.headers = list(self.item_type.model_fields)
        self.edit_mode = False

        self.protected_indices = []
        if self.item_type is RATapi.models.Parameter:
            for i, item in enumerate(classlist):
                if isinstance(item, RATapi.models.ProtectedParameter):
                    self.protected_indices.append(i)

    def flags(self, index):
        flags = super().flags(index)
        if (
            self.item_type is RATapi.models.Parameter
            and self.classlist[index.row()].prior_type != "gaussian"
            and self.headers[index.column() - 1] in ["mu", "sigma"]
        ):
            return QtCore.Qt.ItemFlag.NoItemFlags
        if not (self.edit_mode and index.row() in self.protected_indices and index.column() == 1):
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable

        return flags

    def rowCount(self, parent=None) -> int:
        return len(self.classlist)

    def columnCount(self, parent=None) -> int:
        return len(self.headers) + 1

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()

            if col == 0:
                return ""

            param = self.headers[col - 1]
            data = getattr(self.classlist[row], param)
            # pyqt can't manually coerce enums to strings...
            if isinstance(data, Enum):
                return str(data)
            return data

    def setData(self, index, value, role) -> bool:
        if role == QtCore.Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            if col > 0:
                param = self.headers[col - 1]
                try:
                    setattr(self.classlist[row], param, value)
                except ValidationError:
                    return False
                return True

    def headerData(self, section, orientation, role):
        if (
            orientation == QtCore.Qt.Orientation.Horizontal
            and role == QtCore.Qt.ItemDataRole.DisplayRole
            and section != 0
        ):
            return self.headers[section - 1]
        return None

    def append_item(self):
        """Append an item to the ClassList."""
        self.classlist.append(self.item_type())
        self.endResetModel()

    def delete_item(self, i):
        """Delete an item in the ClassList."""
        self.classlist.pop(i)
        self.endResetModel()


class ProjectFieldWidget(QtWidgets.QWidget):
    """Widget to show a project ClassList."""

    def __init__(self, parent):
        super().__init__(parent)
        self.table = QtWidgets.QTableView(parent)
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )

        layout = QtWidgets.QVBoxLayout()
        # change to icon: remember to mention that plus.png in the icons is wonky
        self.add_button = QtWidgets.QPushButton("+")
        self.add_button.setHidden(True)
        self.add_button.pressed.connect(self.append_item)

        layout.addWidget(self.table)
        layout.addWidget(self.add_button)
        self.setLayout(layout)

    def update_model(self, classlist):
        """Update the table model to synchronise with the project field."""
        self.model = ClassListModel(classlist, self)

        self.table.setModel(self.model)
        self.table.hideColumn(0)
        self.set_item_delegates()
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def set_item_delegates(self):
        """Set item delegates and open persistent editors for the table."""
        for i, header in enumerate(self.model.headers):
            self.table.setItemDelegateForColumn(
                i + 1, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
            )
        for i in range(0, self.model.rowCount()):
            for j in range(2, self.model.columnCount()):
                self.table.openPersistentEditor(self.model.createIndex(i, j))

    def append_item(self):
        """Append an item to the model if the model exists."""
        if self.model is not None:
            self.model.append_item()

        # call edit again to fix persistent editors
        self.edit()

    def delete_item(self, index):
        """Delete an item at the index if the model exists.

        Parameters
        ----------
        index : int
            The row to be deleted.

        """
        if self.model is not None:
            self.model.delete_item(index)

        # call edit again to fix persistent editors
        self.edit()

    def edit(self):
        """Change the widget to be in edit mode."""
        self.model.edit_mode = True
        self.add_button.setHidden(False)
        self.table.showColumn(0)
        self.set_item_delegates()
        for i in range(0, self.model.rowCount()):
            if i not in self.model.protected_indices:
                self.table.setIndexWidget(self.model.createIndex(i, 0), self.make_delete_button(i))
                self.table.openPersistentEditor(self.model.createIndex(i, 1))

    def make_delete_button(self, index):
        """Make a button that deletes index `index` from the list."""
        button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("delete.png")))
        button.resize(button.sizeHint().width(), button.sizeHint().width())
        button.pressed.connect(lambda: self.delete_item(index))

        return button


class ParameterFieldWidget(ProjectFieldWidget):
    """Subclass of field widgets for parameters."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def set_item_delegates(self):
        for i, header in enumerate(self.model.headers):
            if header in ["min", "value", "max"]:
                self.table.setItemDelegateForColumn(i + 1, ValueSpinBoxDelegate(header, self.table))
            else:
                self.table.setItemDelegateForColumn(
                    i + 1, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
                )
        for i in range(0, self.model.rowCount()):
            for j in range(2, self.model.columnCount()):
                self.table.openPersistentEditor(self.model.createIndex(i, j))

    def update_model(self, classlist):
        super().update_model(classlist)
        procedure = self.parent.parent.parent_model.controls.procedure
        is_bayesian = procedure in ["ns", "dream"]
        bayesian_columns = ["prior_type", "mu", "sigma"]
        for item in bayesian_columns:
            index = self.model.headers.index(item)
            if is_bayesian:
                self.table.showColumn(index + 1)
            else:
                self.table.hideColumn(index + 1)


class AbstractProjectTabWidget(QtWidgets.QWidget):
    """Widget that combines multiple ProjectFieldWidgets to create a tab of the project window.

    Subclasses must reimplement the function update_model.

    Parameters
    ----------
    fields : list[str]
        The fields to display in the tab.
    parent : QtWidgets.QWidget
        The parent to this widget.

    """

    def __init__(self, fields: list[str], parent):
        super().__init__(parent)
        self.parent = parent
        self.fields = fields
        headers = [f.replace("_", " ").title() for f in self.fields]
        self.tables = {}

        layout = QtWidgets.QVBoxLayout()
        for field, header in zip(self.fields, headers):
            header = QtWidgets.QLabel(header)
            if field in RATapi.project.parameter_class_lists:
                self.tables[field] = ParameterFieldWidget(self)
            else:
                self.tables[field] = ProjectFieldWidget(self)
            layout.addWidget(header)
            layout.addWidget(self.tables[field])

        scroll_area = QtWidgets.QScrollArea()
        # one widget must be given, not a layout,
        # or scrolling won't work properly!
        tab_widget = QtWidgets.QFrame()
        tab_widget.setLayout(layout)
        scroll_area.setWidget(tab_widget)
        scroll_area.setWidgetResizable(True)

        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(scroll_area)

        self.setLayout(widget_layout)

    def update_model(self, new_model):
        """Update the model for each table.

        Parameters
        ----------
        new_model
            The new model data.

        """
        raise NotImplementedError


class ProjectTabViewWidget(AbstractProjectTabWidget):
    """Widget for a project tab in display mode."""

    def update_model(self, new_model: RATapi.Project):
        for field, table in self.tables.items():
            classlist = getattr(new_model, field)
            table.update_model(classlist)


class ProjectTabEditWidget(AbstractProjectTabWidget):
    """Widget for a project tab in edit mode."""

    def update_model(self, new_model: dict):
        for field, table in self.tables.items():
            classlist = new_model[field]
            table.update_model(classlist)
            table.edit()


def create_draft_project(project: RATapi.Project) -> dict:
    """Create a draft project (dictionary of project attributes) from a Project.

    Parameters
    ----------
    project : RATapi.Project
        The project to create a draft from.

    Returns
    -------
    dict
        The draft project.

    """
    # in an ideal world, we could just copy and dump the Project with something like
    # project.model_copy(deep=True).model_dump()
    # but some references get shared for some reason: e.g. draft_project['parameters'].append
    # will point towards project.parameters.append (???) and so on
   
    draft_project = {}
    for field in RATapi.Project.model_fields:
        attr = getattr(project, field)
        if isinstance(attr, RATapi.ClassList):
            draft_project[field] = RATapi.ClassList(deepcopy(attr.data))
            if hasattr(draft_project[field], '_class_handle') and issubclass(draft_project[field]._class_handle, RATapi.models.ProtectedParameter):
                draft_project[field]._class_handle = RATapi.models.Parameter
        else:
            draft_project[field] = attr
    return draft_project

