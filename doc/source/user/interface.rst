User Interface
==============
Starting the RasCAL-2 software would show a splash screen while the software is loading. When loading is complete,
the startup screen will be shown.

.. image:: /images/startup_screen.png
   :scale: 80
   :alt: RasCAL Startup Screen
   :align: center

At the top of the startup screen is the title bar which will show the name of the software and the project name and
path if a project is opened. Below the title bar is the menu bar and toolbar, which provides access to a number of
operations. At the center of the screen are options for creating or loading a RasCAL project.

.. note:: Some operating systems can change the location and look of title and menu bar.

Menus and Toolbar
-----------------
RasCAL-2 provides access to some actions in a menu bar under the tile bar. These actions are grouped into 5
groups explained below. Clicking on a menu item will perform its associated action.

.. note:: On startup, some menu items like the **Windows** menu will be disabled. These menu items will be enabled
   after a project is created or loaded.

1. **File**
    * **New Project**: Create a new project.
    * **Open Project**: Open an existing project or example project
    * **Open RasCAL-1 Project**: Open a RasCAL-1 project.
    * **Save**: Save changes to the current project.
    * **Save To Folder**: Save current project to another folder.
    * **Export as Script**: Export the project as a python script.
    * **Export Fits**: Export the results as CSV files.
    * **Settings**: Open the settings dialog.
    * **Exit**: Close the RasCAL application.
2. **Edit**
    * **Undo**: Undo the last action.
    * **Redo**: Redo the last undone action.
    * **Undo History**: View the action history.
3. **Windows**
    * **Tile Windows**: Arrange windows in a tile formation.
    * **Reset to Default**: Reset the windows locations and sizes to the user saved defaults.
    * **Save Current Window Positions**: Save the current positions and sizes of the windows as the user default.
4. **Tools**
    * **Show Sliders/Hide Sliders**: Show or hide slider view in the project window. see :ref:`about_sliders`.
    * **Clear Terminal**: Clears the text in the terminal window.
5. **Help**
    * **Help**: Open the documentation website in the browser.
    * **Check for Update**: Check online for new RasCAL-2 version.
    * **About**: Show information about RasCAL-2.

RasCAL-2 also provides access to some actions in a toolbar below the menu bar. The toolbar actions are **New Project**,
**Open Project**, **Save**, **Undo**, **Redo**, **Settings**, and **Help**. Clicking on the appropriate icon in the
toolbar will perform its associated action.

Window Management
-----------------
After creating or loading a project, the interface will display 4 sub-windows arranged by default in 2x2 irregular
grid. The sub-windows are

* Plot window (top left)
* Project window (top right)
* Terminal window (bottom left)
* Controls window (bottom right)

These sub-windows can be rearranged by clicking on the title bar of the sub-window and dragging the sub-window. The
sub-window can also be resized, minimised and maximized similar to the main window. It can be useful to make a
sub-window bigger or smaller to suit a workflow, after which the arrangement can be saved by clicking
**Windows > Save Current Window Positions** in the menu, this will make that arrangement the default and RasCAL will
use that saved arrangement whenever the software is started.

If you move a sub-window and want to revert back to you saved arrangement, click **Windows > Reset to Default** in the
menu. If you want to revert to the original arrangement, click **Windows > Tile Windows** then click
**Windows > Save Current Window Positions** in the menu to save the arrangement.


.. note:: The sub-windows cannot be dragged outside the boundary of the main software window but only within the
   centre area of the main window.
