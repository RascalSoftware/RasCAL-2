# Standard library
from datetime import datetime
import logging as log_class

# Third-party
from PyQt6 import QtCore, QtGui, QtWidgets

# Local application
import rascal2
import rascal2.widgets

from rascal2.config import MATLAB_HELPER, path_for
from rascal2.settings import LogLevels

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define internal variables

        # Define main window
        self.setWindowTitle("About RasCAL 2")
        self.setMinimumWidth(800)
        self.setMaximumHeight(400)

        self._rascal_label = QtWidgets.QLabel("information about RASCAL-2")
        self._rascal_label.setWordWrap(True)

        # Load RASCAL logo from appropriate image
        logo_label = QtWidgets.QLabel()
        # Load image into a QPixmap
        pixmap = QtGui.QPixmap(path_for("logo_small.png"))
        # Attach the pixmap to the logo label
        logo_label.setPixmap(pixmap)
        logo_label.setMinimumSize(100,105)

        # Format all widget into appropriate box layouts
        main_layout = QtWidgets.QVBoxLayout()

        # place for logo
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(logo_label,alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        # place for text
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self._rascal_label,alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        # First row will contain logo and text about RasCal
        row1_layout = QtWidgets.QHBoxLayout()
        # arrange logo and text into appropriate ratio
        row1_layout.addLayout(left_layout,stretch=1)
        row1_layout.addLayout(right_layout,stretch=4)
        row1_layout.setSpacing(50)
        main_layout.addLayout(row1_layout)
        # ok button at the right of the image (should it be on the left?)
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button,alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(button_layout)
        main_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        #main_layout.setContentsMargins(0, 0, 0, 0)
        #main_layout.setSpacing(10)
        self.setLayout(main_layout)

    def update_rascal_info(self,parent):
        """Obtain info about RASCAL (version, main settings etc.)
        retrieved from general class information
        """
        #self._Working_dir = parent.settings.get("Working_dir")
        matlab_path = MATLAB_HELPER.get_matlab_path()
        if not matlab_path:
            matlab_path = "None"

        log_file = "None"
        log_level = "None"
        logger = parent.logging
        for h in logger.handlers:
            if isinstance(h, log_class.FileHandler):
                log_file = h.baseFilename
                log_level  = str(LogLevels(logger.level))

        #working_dir = "None" # Do we want to add this to the info too?

        # Main header. Format information about Rascal 2
        info_template = """
            <b><i><span style="font-family:Georgia; font-size:42pt; text-align:center;">
            RasCAL 2
            </span></i></b><br>
            <span style="font-family:Georgia; font-size:20pt;">
            A GUI for Reflectivity Algorithm Toolbox (RAT)
            </span><br><br>
               
            <span style="font-family:Georgia; font-size:12pt;">
               <table style="text-align:left;">
                   <tr><td>Version:    </td><td>{}</td></tr>
                   <tr><td>Matlab Path:</td><td>{}</td></tr>
                   <tr><td>Log Level:  </td><td>{}</td></tr>
                   <tr><td>Log File:   </td><td>{}</td></tr> 
               </table><br><br>

              Distributed under the BSD 3-Clause License<br>
              <p>Copyright &copy; 2018-{} ISIS Neutron and Muon Source.</p>
              All rights reserved
            </span>
            """
        this_time = datetime.now()
        label_text = info_template.format(rascal2.RASCAL2_VERSION,
            matlab_path,log_level,log_file,this_time.year)
        self._rascal_label.setText(label_text)

    @property
    def rascal_info(self):
        """ Obtain information about RASCAL stored in the rascal label"""
        return self._rascal_label.text()
