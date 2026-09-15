# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
import datetime

sys.path.insert(0, os.path.abspath("../.."))

from rascal2 import RASCAL2_VERSION


project = 'RasCAL-2'
copyright = u"2024-{}, ISIS Neutron and Muon Source".format(datetime.date.today().year)
author = 'ISIS Neutron and Muon Source'
version = RASCAL2_VERSION
# The full version, including alpha/beta/rc tags.
release = version
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_title = "RasCAL-2"
html_logo = "_static/logo.png"
html_favicon = "_static/logo.png"
html_static_path = ['_static']
html_css_files = ["custom.css"]
html_copy_source = False
html_show_sourcelink = False
html_theme_options = {
    "show_prev_next": False,
    "logo": {
        "text": "RasCAL-2",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/RascalSoftware/RasCAL-2",
            "icon": "fa-brands fa-github",
        },
    ],
}


rst_epilog = """
.. |Angstrom| replace:: :math:`\mathring{A}`
.. |tutorial data| raw:: html

   <a href="https://indico.stfc.ac.uk/event/792/contributions/4939/attachments/1739/7049/Virtual%20Reflectometry%20School%202026.zip" target="_blank">tutorial data</a>
"""
