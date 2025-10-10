from PyQt6 import QtGui, QtWidgets, QtCore
import logging as log_class


from rascal2.config import MATLAB_HELPER, STATIC_PATH, path_for

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define internal variables
        self._version = "1.0.0"
        self._Matlab_path = "None"
        self._Log_File = "None"
        self._Working_dir = "None"

        # Main header. Format information about Rascal 2
        Info_template = """
               <b><i><span style="font-family:Georgia; font-size:42pt;">RasCAL 2</b></span><br>
               <span style="font-family:Georgia; "font-size=38pt;">            
                A GUI for Reflectivity Algorithm Toolbox<br><br>
                 <table style="text-align:left;">
                     <tr>
                       <td>Version:</td><td>{}</td>
                       </tr><tr>
                       <td>Matlab Path:</td><td>{}</td>
                       </tr><tr>
                       <td>Log File:</td><td>{}</td>
                     </tr> 
                 </table><br><br>     
                </span>
                <span style="font-family:Georgia; "font-size=32pt;">
                Distributed under the BSD 3-Clause License<br>
                <p>Copyright &copy; 2018-2025 ISIS Neutron and Muon Source.</p>
                All rights reserved
                </span></i>
                """
        # Define main window
        self.setWindowTitle("About RasCAL 2")
        self.setMinimumWidth(500)
        self.setMinimumHeight(250)

        label_text = Info_template.format(self._version,self._Matlab_path,self._Log_File)
        rascal_label = QtWidgets.QLabel(label_text)
        rascal_label.setWordWrap(True)

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
        right_layout.addWidget(rascal_label)
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
        self._Matlab_path = MATLAB_HELPER.get_matlab_path()
        if not self._Matlab_path:
            self._Matlab_path = "None"
        logger = parent.logging
        for h in logger.handlers:
            if isinstance(h, log_class.FileHandler):
                self._Log_File = h.baseFilename
            else:
                self._Log_File = "None"
