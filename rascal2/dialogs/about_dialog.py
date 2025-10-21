import pathlib
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets

import rascal2
import rascal2.widgets
from rascal2.config import MatlabHelper, path_for
from rascal2.settings import get_global_settings


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define internal variables

        # Define main window
        self.setWindowTitle("About RasCAL 2")
        self.setMinimumWidth(750)
        self.setFixedHeight(380)

        self._rascal_label = QtWidgets.QLabel("information about RASCAL-2")
        self._rascal_label.setWordWrap(True)
        self._rascal_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        # Load RASCAL logo from appropriate image
        logo_label = QtWidgets.QLabel()
        logo_label.setScaledContents(True)
        # Load image into a QPixmap
        pixmap = QtGui.QPixmap(path_for("logo.png"))
        # Attach the pixmap to the logo label
        logo_label.setPixmap(pixmap)
        logo_label.setFixedSize(100, 105)

        # Format all widget into appropriate box layouts
        main_layout = QtWidgets.QVBoxLayout()

        # place for logo
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        # place for text
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self._rascal_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        # First row will contain logo and text about RasCal
        row1_layout = QtWidgets.QHBoxLayout()
        # arrange logo and text into appropriate ratio
        row1_layout.addLayout(left_layout, stretch=1)
        row1_layout.addLayout(right_layout, stretch=4)
        row1_layout.setSpacing(50)
        main_layout.addLayout(row1_layout)
        # ok button at the right of the image (should it be on the left?)
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(button_layout)
        main_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update_rascal_info(self, parent):
        """Obtain info about RASCAL (version, main settings etc.)
        retrieved from general class information
        """
        matlab_path = MatlabHelper().get_matlab_path()
        if not matlab_path:
            matlab_path = "None"

        log_file = pathlib.Path(get_global_settings().fileName()).parent / "rascal.log"

        # Main header. Format information about Rascal 2
        info_template = """
            <b><i><span style="font-family:Georgia; font-size:36pt; text-align:center;">
            RasCAL 2
            </span></i></b><br>
            <span style="font-family:Georgia; font-size:18pt;">
            A GUI for Reflectivity Algorithm Toolbox (RAT)
            </span><br><br>
               
            <span style="font-family:Georgia; font-size:12pt;">
               <table style="text-align:left;">
                   <tr><td>Version:    </td><td>{}</td></tr>
                   <tr><td>Matlab Path:</td><td>{}</td></tr>
                   <tr><td>Log File:   </td><td>{}</td></tr> 
               </table><br><br>

              Distributed under the BSD 3-Clause License<br>
              <p>Copyright &copy; 2018-{} ISIS Neutron and Muon Source.</p>
              All rights reserved
            </span>
            """
        this_time = datetime.now()
        label_text = info_template.format(rascal2.RASCAL2_VERSION, matlab_path, log_file, this_time.year)
        self._rascal_label.setText(label_text)
