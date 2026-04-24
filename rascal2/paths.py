import site
import sys
from pathlib import Path

from rascal2.settings import get_global_settings

if getattr(sys, "frozen", False):
    # we are running in a bundle
    SOURCE_PATH = Path(sys.executable).parent.parent
    SITE_PATH = SOURCE_PATH / "bin/_internal"
    if Path(SOURCE_PATH / "MacOS").is_dir():
        SOURCE_PATH = SOURCE_PATH / "Resources"
        SITE_PATH = SOURCE_PATH
    EXAMPLES_PATH = SOURCE_PATH / "examples"
else:
    SOURCE_PATH = Path(__file__).parent
    SITE_PATH = site.getsitepackages()[-1]
    EXAMPLES_PATH = SOURCE_PATH.parent / "examples"

STATIC_PATH = SOURCE_PATH / "static"
IMAGES_PATH = STATIC_PATH / "images"
MATLAB_ARCH_FILE = Path(SITE_PATH) / "matlab/engine/_arch.txt"
EXAMPLES_TEMP_PATH = Path(get_global_settings().fileName()).parent / "examples"


def path_for(filename: str):
    """Get full path for the given image file.

    Parameters
    ----------
    filename : str
        basename and extension of image.

    Returns
    -------
    full path : str
        full path of the image.
    """
    return (IMAGES_PATH / filename).as_posix()
