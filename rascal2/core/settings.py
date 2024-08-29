"""Global settings for RasCAL."""

from enum import StrEnum
from os import PathLike
from pathlib import PurePath
from typing import Any

from pydantic import BaseModel, Field
from PyQt6 import QtCore


# we do this statically rather than making it an attribute of Settings
# because all fields in a Pydantic model must be pickleable
# so it's easier to keep this 'outside' the model
def get_global_settings() -> QtCore.QSettings:
    """Get the global settings QSettings object."""
    return QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "RasCAL-2",
        "RasCAL-2",
    )


class Styles(StrEnum):
    Light = "light"


class Settings(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """Model for system settings."""

    # The Settings object's own model fields contain the within-project settings.
    # The object itself contains the attribute `self.global_settings` which
    # holds the global settings QSettings object.

    # Pydantic gives two plaintext fields to play around with:
    # we use 'title' for setting group
    # and 'description' for human-readable setting name
    style: Styles = Field(default=Styles.Light, title="general", description="Style")
    editor_fontsize: int = Field(default=12, title="general", description="Editor Font Size", gt=0)
    terminal_fontsize: int = Field(default=12, title="general", description="Terminal Font Size", gt=0)

    def model_post_init(self, __context: Any):
        global_settings = get_global_settings()
        unset_settings = [s for s in self.model_fields if s not in self.model_fields_set]
        for setting in unset_settings:
            if global_name(setting) in global_settings.allKeys():
                setattr(self, setting, global_settings.value(global_name(setting)))

    def save(self, path: PathLike):
        """Save settings to a JSON file in the given path.

        Parameters
        ----------
        path : PathLike
            The path to the folder where settings will be saved.

        """
        file = PurePath(path, "settings.json")
        with open(file, "w") as f:
            f.write(self.model_dump_json())

    def set_global_settings(self):
        """Set local settings as global settings."""
        global_settings = get_global_settings()
        for setting in self.model_fields_set:
            global_settings.setValue(global_name(setting), getattr(self, setting))


def global_name(key: str) -> str:
    """Get the QSettings global name of a setting.

    Parameters
    ----------
    key : str
        The attribute name for the setting.

    Returns
    -------
    str
        The QSettings string for the setting.

    """
    group = Settings.model_fields[key].title
    if group:
        return f"{group}/{key}"
    return key
