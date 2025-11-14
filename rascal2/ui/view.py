from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import EXAMPLES_PATH, get_logger, path_for, setup_logging, setup_settings
from rascal2.core.enums import UnsavedReply
from rascal2.dialogs.about_dialog import AboutDialog
from rascal2.dialogs.settings_dialog import SettingsDialog
from rascal2.dialogs.startup_dialog import PROJECT_FILES, LoadDialog, LoadR1Dialog, NewProjectDialog, StartupDialog
from rascal2.settings import MDIGeometries, Settings, get_global_settings
from rascal2.widgets import ControlsWidget, PlotWidget, SlidersViewWidget, TerminalWidget
from rascal2.widgets.project import ProjectWidget
from rascal2.widgets.startup import StartUpWidget

from .presenter import MainWindowPresenter

MAIN_WINDOW_TITLE = "RasCAL-2"


class MainWindowView(QtWidgets.QMainWindow):
    """Creates the main view for the RasCAL app"""

    def __init__(self):
        super().__init__()
        # Public interface
        self.disabled_elements = []
        self.show_sliders = False  # no one displays sliders initially

        self.setWindowTitle(MAIN_WINDOW_TITLE)

        window_icon = QtGui.QIcon(path_for("logo.png"))

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_view = QtWidgets.QUndoView(self.undo_stack)
        self.undo_view.setWindowTitle("Undo History")
        self.undo_view.setWindowIcon(window_icon)
        self.undo_view.setAttribute(QtCore.Qt.WidgetAttribute.WA_QuitOnClose, False)

        self.presenter = MainWindowPresenter(self)
        self.mdi = QtWidgets.QMdiArea()

        self.plot_widget = PlotWidget(self)
        self.terminal_widget = TerminalWidget()
        self.controls_widget = ControlsWidget(self)
        self.project_widget = ProjectWidget(self)
        self.sliders_view_widget = SlidersViewWidget(self)

        ## protected interface and public properties construction

        # define menu controlling switch between table and slider views
        self._sliders_menu_control_text = {
            "ShowSliders": "&Show Sliders",  # if state is show sliders, click will show them
            "HideSliders": "&Hide Sliders",
        }  # if state is show table, click will show sliders

        self.create_actions()

        main_menu = self.menuBar()
        self.add_submenus(main_menu)

        self.create_toolbar()
        self.create_status_bar()

        self.setMinimumSize(1024, 800)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.settings = Settings()
        self.logging = get_logger()
        self.startup_dlg = StartUpWidget(self)
        self.setCentralWidget(self.startup_dlg)

        self.about_dialog = AboutDialog(self)
        # dictionary of main widgets present in the main operation area controlled
        # by mdi interface.
        # There are other widgets (sliders_view) which are initially hidden.
        self._main_window_widgets = {
            "Plots": self.plot_widget,
            "Project": self.project_widget,
            "Terminal": self.terminal_widget,
            "Fitting Controls": self.controls_widget,
        }

    def closeEvent(self, event):
        if self.presenter.ask_to_save_project():
            event.accept()
        else:
            event.ignore()

    def show_project_dialog(self, dialog: StartupDialog):
        """Shows a startup dialog of a given type.

        Parameters
        ----------
        dialog : StartupDialog
            The dialog to show.
        """
        if self.startup_dlg.isVisible():
            self.startup_dlg.hide()

        if self.presenter.ask_to_save_project():
            project_dlg = dialog(self)
            project_dlg.show()

    def show_settings_dialog(self, tab_name=""):
        """Shows the settings dialog and makes tab with given name active.

        Parameters
        ----------
        tab_name : str, default ""
            The name of tab to make active.
        """
        settings_dlg = SettingsDialog(self)
        if tab_name:
            for i in range(settings_dlg.tab_widget.count()):
                if settings_dlg.tab_widget.tabText(i).lower() == tab_name.lower():
                    settings_dlg.tab_widget.setCurrentIndex(i)
                    break
        settings_dlg.show()

    def create_actions(self):
        """Creates the menu and toolbar actions"""

        self.new_project_action = QtGui.QAction("&New Project", self)
        self.new_project_action.setStatusTip("Create a new project")
        self.new_project_action.setIcon(QtGui.QIcon(path_for("new-project.png")))
        self.new_project_action.triggered.connect(lambda: self.show_project_dialog(NewProjectDialog))
        self.new_project_action.setShortcut(QtGui.QKeySequence.StandardKey.New)

        self.open_project_action = QtGui.QAction("&Open Project", self)
        self.open_project_action.setStatusTip("Open an existing project")
        self.open_project_action.setIcon(QtGui.QIcon(path_for("browse-dark.png")))
        self.open_project_action.triggered.connect(lambda: self.show_project_dialog(LoadDialog))
        self.open_project_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)

        self.open_r1_action = QtGui.QAction("Open &RasCAL-1 Project")
        self.open_r1_action.setStatusTip("Open a RasCAL-1 project")
        self.open_r1_action.triggered.connect(lambda: self.show_project_dialog(LoadR1Dialog))

        self.save_project_action = QtGui.QAction("&Save", self)
        self.save_project_action.setStatusTip("Save project")
        self.save_project_action.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_action.triggered.connect(lambda: self.presenter.save_project())
        self.save_project_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.save_project_action.setEnabled(False)
        self.disabled_elements.append(self.save_project_action)

        self.save_as_action = QtGui.QAction("Save To &Folder...", self)
        self.save_as_action.setStatusTip("Save project to a specified folder.")
        self.save_as_action.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_as_action.triggered.connect(lambda: self.presenter.save_project(save_as=True))
        self.save_as_action.setShortcut(QtGui.QKeySequence.StandardKey.SaveAs)
        self.disabled_elements.append(self.save_project_action)

        self.undo_action = self.undo_stack.createUndoAction(self, "&Undo")
        self.undo_action.setStatusTip("Undo the last action")
        self.undo_action.setIcon(QtGui.QIcon(path_for("undo.png")))
        self.undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)

        self.redo_action = self.undo_stack.createRedoAction(self, "&Redo")
        self.redo_action.setStatusTip("Redo the last undone action")
        self.redo_action.setIcon(QtGui.QIcon(path_for("redo.png")))
        self.redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)

        self.undo_view_action = QtGui.QAction("Undo &History", self)
        self.undo_view_action.setStatusTip("View undo history")
        self.undo_view_action.triggered.connect(self.show_undo_view)
        self.undo_view_action.setEnabled(False)
        self.disabled_elements.append(self.undo_view_action)

        self.export_results_action = QtGui.QAction("Export Results", self)
        self.export_results_action.setStatusTip("Export Results to a specified file.")
        self.export_results_action.triggered.connect(lambda: self.presenter.export_results())
        self.export_results_action.setEnabled(False)
        self.disabled_elements.append(self.export_results_action)

        self.settings_action = QtGui.QAction("Settings", self)
        self.settings_action.setStatusTip("Settings")
        self.settings_action.setIcon(QtGui.QIcon(path_for("settings.png")))
        self.settings_action.triggered.connect(lambda: self.show_settings_dialog())
        self.settings_action.setEnabled(False)
        self.disabled_elements.append(self.settings_action)

        open_help_action = QtGui.QAction("&Help", self)
        open_help_action.setStatusTip("Open Documentation")
        open_help_action.setIcon(QtGui.QIcon(path_for("help.png")))
        open_help_action.triggered.connect(self.open_docs)
        self.open_help_action = open_help_action

        # done this way expecting the value "display_sliders" being stored
        # in configuration in a future.
        if self.show_sliders:
            # if show_sliders state is True, action will be hide
            show_or_hide_slider_action = QtGui.QAction(self._sliders_menu_control_text["HideSliders"], self)
        else:
            # if display_sliders state is False, action will be show
            show_or_hide_slider_action = QtGui.QAction(self._sliders_menu_control_text["ShowSliders"], self)
        show_or_hide_slider_action.setStatusTip("Show or Hide Sliders")
        show_or_hide_slider_action.triggered.connect(lambda: self.show_or_hide_sliders(None))
        self._show_or_hide_slider_action = show_or_hide_slider_action
        self._show_or_hide_slider_action.setEnabled(False)
        self.disabled_elements.append(self._show_or_hide_slider_action)

        open_about_action = QtGui.QAction("&About", self)
        open_about_action.setStatusTip("Report RAT version&info")
        open_about_action.triggered.connect(self.open_about_info)
        self.open_about_action = open_about_action

        self.exit_action = QtGui.QAction("E&xit", self)
        self.exit_action.setStatusTip(f"Quit {MAIN_WINDOW_TITLE}")
        self.exit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        # Window menu actions
        self.tile_windows_action = QtGui.QAction("Tile Windows", self)
        self.tile_windows_action.setStatusTip("Arrange windows in the default grid.")
        self.tile_windows_action.setIcon(QtGui.QIcon(path_for("tile.png")))
        self.tile_windows_action.triggered.connect(self.mdi.tileSubWindows)
        self.tile_windows_action.setEnabled(False)
        self.disabled_elements.append(self.tile_windows_action)

        self.reset_windows_action = QtGui.QAction("Reset to Default")
        self.reset_windows_action.setStatusTip("Reset the windows to their default arrangement.")
        self.reset_windows_action.triggered.connect(self.reset_mdi_layout)
        self.reset_windows_action.setEnabled(False)
        self.disabled_elements.append(self.reset_windows_action)

        self.save_default_windows_action = QtGui.QAction("Save Current Window Positions")
        self.save_default_windows_action.setStatusTip("Set the current window positions as default.")
        self.save_default_windows_action.triggered.connect(self.save_mdi_layout)
        self.save_default_windows_action.setEnabled(False)
        self.disabled_elements.append(self.save_default_windows_action)

        # Terminal menu actions
        self.clear_terminal_action = QtGui.QAction("Clear Terminal", self)
        self.clear_terminal_action.setStatusTip("Clear text in the terminal")
        self.clear_terminal_action.triggered.connect(self.terminal_widget.clear)

        self.setup_matlab_action = QtGui.QAction("Setup MATLAB", self)
        self.setup_matlab_action.setStatusTip("Set the path of the MATLAB executable")
        self.setup_matlab_action.triggered.connect(lambda: self.show_settings_dialog(tab_name="Matlab"))

    def add_submenus(self, main_menu: QtWidgets.QMenuBar):
        """Add sub menus to the main menu bar"""

        main_menu.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)

        file_menu = main_menu.addMenu("&File")
        file_menu.setObjectName("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.open_r1_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_project_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_results_action)
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = main_menu.addMenu("&Edit")
        edit_menu.setObjectName("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addAction(self.undo_view_action)

        windows_menu = main_menu.addMenu("&Windows")
        windows_menu.setObjectName("&Windows")
        windows_menu.addAction(self.tile_windows_action)
        windows_menu.addAction(self.reset_windows_action)
        windows_menu.addAction(self.save_default_windows_action)
        windows_menu.setEnabled(False)
        self.disabled_elements.append(windows_menu)

        tools_menu = main_menu.addMenu("&Tools")
        tools_menu.setObjectName("&Tools")
        tools_menu.addAction(self._show_or_hide_slider_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.clear_terminal_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.setup_matlab_action)

        help_menu = main_menu.addMenu("&Help")
        help_menu.setObjectName("&Help")
        help_menu.addAction(self.open_about_action)
        help_menu.addAction(self.open_help_action)

    def show_or_hide_sliders(self, do_show_sliders=None):
        """Depending on current state, show or hide sliders for
        table properties within Project class view.

        do_show_sliders -- if provided, sets self.show_sliders logical variable
                              into the requested state (True/False), forcing sliders
                              widget to appear/disappear
        """
        if do_show_sliders is None:
            self.show_sliders = not self.show_sliders
        else:
            self.show_sliders = do_show_sliders

        # ignore show/hide operations if project and its mdi container are not defined
        if self.sliders_view_widget.mdi_holder is None:
            return

        if self.show_sliders:
            self._show_or_hide_slider_action.setText(self._sliders_menu_control_text["HideSliders"])
            self.sliders_view_widget.show()
        else:
            self._show_or_hide_slider_action.setText(self._sliders_menu_control_text["ShowSliders"])
            self.sliders_view_widget.hide()

    def open_about_info(self):
        """Opens about menu containing information about RASCAL gui"""
        self.about_dialog.update_rascal_info(self)
        self.about_dialog.show()

    def show_undo_view(self):
        self.undo_view.showNormal()
        self.undo_view.raise_()

    def open_docs(self):
        """Opens the documentation"""
        url = QtCore.QUrl("https://rascalsoftware.github.io/RAT-Docs/dev/index.html")
        QtGui.QDesktopServices.openUrl(url)

    def create_toolbar(self):
        """Creates the toolbar"""
        self.toolbar = self.addToolBar("ToolBar")
        self.toolbar.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.new_project_action)
        self.toolbar.addAction(self.open_project_action)
        self.toolbar.addAction(self.save_project_action)
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
        self.toolbar.addAction(self.settings_action)
        self.toolbar.addAction(self.open_help_action)

    def create_status_bar(self):
        """Creates the status bar"""
        sb = QtWidgets.QStatusBar()
        self.setStatusBar(sb)

    def setup_mdi(self):
        """Creates the multi-document interface"""
        # if windows are already created, don't set them up again,
        # just refresh the widget data
        if len(self.mdi.subWindowList()) == 5:
            self.init_mdi_widgets()
            return

        self.init_mdi_widgets()

        for title, widget in reversed(self._main_window_widgets.items()):
            widget.setWindowTitle(title)
            window = self.mdi.addSubWindow(
                widget, QtCore.Qt.WindowType.WindowMinMaxButtonsHint | QtCore.Qt.WindowType.WindowTitleHint
            )
            window.setWindowTitle(title)
        #  Add sliders view widget separately, as it will behave and is controlled differently from other
        # mdi windows
        self.mdi.addSubWindow(
            self.sliders_view_widget,
            QtCore.Qt.WindowType.WindowMinMaxButtonsHint | QtCore.Qt.WindowType.WindowTitleHint,
        )
        self.sliders_view_widget.setWindowTitle("Sliders View")

        self.reset_mdi_layout()
        self.startup_dlg = self.takeCentralWidget()
        self.setCentralWidget(self.mdi)

    def init_mdi_widgets(self):
        """Performs initialization of MDI widgets that relies on the Project existing."""
        self.controls_widget.setup_controls()
        self.project_widget.show_project_view()
        self.plot_widget.clear()
        self.terminal_widget.clear()
        self.terminal_widget.write_startup()
        self.sliders_view_widget.init()

    def reset_mdi_layout(self):
        """Reset MDI layout to the default."""

        main_widget_names = self._main_window_widgets.keys()
        if self.settings.mdi_defaults is None:
            # logic expects "Sliders View" the only widget in the mdi list
            slider_view_wrapper = None
            for window in self.mdi.subWindowList():
                if window.windowTitle() in main_widget_names:
                    window.showNormal()
                else:
                    window.hide()
                    slider_view_wrapper = window
            self.mdi.tileSubWindows()
            self.sliders_view_widget.mdi_holder = slider_view_wrapper
        else:
            # reliability check. Can we have project saved previously with mdi defaults
            # and initialized here newer entering the "if mdi_defaults" loop above?
            if self.sliders_view_widget.mdi_holder is None:
                for window in self.mdi.subWindowList():
                    if window.windowTitle() == "Sliders View":
                        self.sliders_view_widget.mdi_holder = window

            for window in self.mdi.subWindowList():
                # get corresponding MDIGeometries entry for the widget
                widget_name = window.windowTitle().replace(" ", "")
                x, y, width, height, minimized = getattr(self.settings.mdi_defaults, widget_name)
                if minimized:
                    window.showMinimized()
                else:
                    window.showNormal()
                window.setGeometry(x, y, width, height)

    def save_mdi_layout(self):
        """Set current MDI geometries as the default."""
        geoms = {}
        for window in self.mdi.subWindowList():
            # get corresponding MDIGeometries entry for the widget
            widget_name = window.windowTitle().replace(" ", "")
            geom = window.geometry()
            geoms[widget_name] = (geom.x(), geom.y(), geom.width(), geom.height(), window.isMinimized())

        self.settings.mdi_defaults = MDIGeometries.model_validate(geoms)

    def init_settings_and_log(self, save_path: str):
        """Initialise settings and logging for the project.

        Parameters
        ----------
        save_path : str
            The save path for the project.

        """
        proj_path = Path(save_path)
        self.settings = setup_settings(proj_path)

        if proj_path.is_relative_to(EXAMPLES_PATH):
            log_path = Path(get_global_settings().fileName()).parent
        else:
            log_path = proj_path / "logs"

        log_path.mkdir(parents=True, exist_ok=True)
        self.logging = setup_logging(log_path / "rascal.log", self.terminal_widget)

    def enable_elements(self):
        """Enable the elements that are disabled on startup."""
        for element in self.disabled_elements:
            element.setEnabled(True)
        self.disabled_elements = []

    def handle_results(self, results=None):
        """Handle the results of a RAT run.

        Parameters
        ----------
        results : Optional[Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]]
            The calculation results.

        """
        self.controls_widget.run_button.setChecked(False)
        if results is not None:
            self.controls_widget.chi_squared.setText(f"{results.calculationResults.sumChi:.6g}")

    def set_editing_enabled(self, enabled: bool):
        """Disable or enable project editing, for example during a run.

        Parameters
        ----------
        enabled : bool
            indicates if project editing is enabled.

        """
        self.controls_widget.fit_settings.setEnabled(enabled)
        self.controls_widget.procedure_dropdown.setEnabled(enabled)
        self.undo_action.setEnabled(enabled and self.undo_stack.canUndo())
        self.redo_action.setEnabled(enabled and self.undo_stack.canRedo())
        self.project_widget.set_editing_enabled(enabled)

    def get_project_folder(self) -> str | None:
        """Get a specified folder from the user.

        Returns
        -------
        str
            The chosen project folder.
        """
        project_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if project_folder:
            if Path(project_folder).is_relative_to(EXAMPLES_PATH):
                message = "Files cannot be saved in the examples directory. Please select another directory to save in."
                QtWidgets.QMessageBox.warning(
                    self,
                    "Select Folder",
                    message,
                    QtWidgets.QMessageBox.StandardButton.Ok,
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                return ""

            if any(Path(project_folder, file).exists() for file in PROJECT_FILES):
                overwrite = self.show_confirm_dialog(
                    "Confirm Overwrite", "A project already exists in this folder, do you want to replace it?"
                )
                if not overwrite:
                    # return to file selection
                    project_folder = self.get_project_folder()
                    return project_folder  # must manually return else all the rejected overwrites will save at once!!

            return project_folder

        return None

    def get_save_file(self, caption, directory, file_filter) -> str:
        """Get a specified file to save to from the user.

        Parameters
        ----------
        caption : str
            The caption used for the save dialog.
        directory : str
            The working directory of the save dialog.
        file_filter : str
            The file types selected in the dialog.

        Returns
        -------
        str
            The chosen file.
        """
        save_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption, directory, QtCore.QObject.tr(file_filter))

        if Path(save_file).is_relative_to(EXAMPLES_PATH):
            message = "Files cannot be saved in the examples directory. Please select another directory to save in."
            QtWidgets.QMessageBox.warning(
                self, caption, message, QtWidgets.QMessageBox.StandardButton.Ok, QtWidgets.QMessageBox.StandardButton.Ok
            )
            return ""

        return save_file

    def show_confirm_dialog(self, title: str, message: str) -> bool:
        """Ask the user to confirm an action.

        Parameters
        ----------
        title : str
            The title of the confirm dialog.
        message : str
            The message to ask the user.

        Returns
        -------
        bool
            Whether the confirmation was affirmative.
        """
        buttons = QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel
        reply = QtWidgets.QMessageBox.question(
            self, title, message, buttons, QtWidgets.QMessageBox.StandardButton.Cancel
        )

        return reply == QtWidgets.QMessageBox.StandardButton.Ok

    def show_unsaved_dialog(self, message: str) -> UnsavedReply:
        """Warn the user of unsaved changes, and ask whether to save those changes.

        Parameters
        ----------
        message : str
            The message to inform the user of unsaved changes.

        Returns
        -------
        rascal2.core.enums.UnsavedReply
            The user's response to the warning.
        """
        buttons = (
            QtWidgets.QMessageBox.StandardButton.Save
            | QtWidgets.QMessageBox.StandardButton.Discard
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        reply = QtWidgets.QMessageBox.warning(
            self, MAIN_WINDOW_TITLE, message, buttons, QtWidgets.QMessageBox.StandardButton.Cancel
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Save:
            return UnsavedReply.Save
        elif reply == QtWidgets.QMessageBox.StandardButton.Discard:
            return UnsavedReply.Discard
        else:
            return UnsavedReply.Cancel
