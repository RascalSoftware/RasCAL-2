from PyQt6 import QtGui, QtWidgets, QtCore
import logging as log_class

import rascal2
from rascal2.config import MATLAB_HELPER, STATIC_PATH, path_for

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define internal variables

        # Define main window
        self.setWindowTitle("About RasCAL 2")
        self.setMinimumWidth(500)
        self.setMinimumHeight(250)

        self._rascal_label = QtWidgets.QLabel("RASCAL-2")
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
        main_layout.addStretch()
        # First row will contain logo and text about RasCal
        row1_layout = QtWidgets.QHBoxLayout()
        #
        left_layout = QtWidgets.QVBoxLayout() # place for logo
        left_layout.addWidget(logo_label,alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        #
        right_layout = QtWidgets.QVBoxLayout() # place for text
        right_layout.addWidget(self._rascal_label)
        # arrange logo and text into appropriate ratio
        row1_layout.addLayout(left_layout,stretch=1)
        row1_layout.addLayout(right_layout,stretch=4)
        row1_layout.setSpacing(50)
        main_layout.addLayout(row1_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()  # pushes button to the right
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        main_layout.addLayout(button_layout)
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
        logger = parent.logging
        for h in logger.handlers:
            if isinstance(h, log_class.FileHandler):
                log_file = h.baseFilename
            else:
                log_file = "None"

        Working_dir = "None"
        log_level  = "INFO"
        # Main header. Format information about Rascal 2
        info_template = """
               <b><i><span style="font-family:Georgia; font-size:42pt;">RasCAL 2</b></span><br><br>
               <span style="font-family:Georgia; "font-size=34pt;">            
                A GUI for Reflectivity Algorithm Toolbox<br><br>
                 <table style="text-align:left;">
                     <tr>
                       <td>Version:</td><td>{}</td>
                       </tr><tr>
                       <td>Matlab Path:</td><td>{}</td>
                       </tr><tr>
                       <td>Log Level:</td><td>{}</td>                       
                       </tr><tr>
                       <td>Log File:</td><td>{}</td>                       
                     </tr> 
                 </table><br><br>     
                </span>
                <span style="font-family:Georgia; "font-size=30pt;">
                Distributed under the BSD 3-Clause License<br>
                <p>Copyright &copy; 2018-2025 ISIS Neutron and Muon Source.</p>
                All rights reserved
                </span></i>
                """
        label_text = info_template.format(rascal2.RASCAL2_VERSION,matlab_path,log_level,log_file)
        self._rascal_label.setText(label_text)