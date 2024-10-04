"""Global settings for RasCAL."""

import logging
from enum import IntEnum, StrEnum
from os import PathLike
from pathlib import Path
from typing import Any, TypeAlias

from pydantic import BaseModel, Field
from PyQt6 import QtCore


# we do this statically rather than making it an attribute of Settings because all fields in a Pydantic model
# must be pickleable, so it's easier to keep this 'outside' the model
def get_global_settings() -> QtCore.QSettings:
    """Get the global settings QSettings object."""
    return QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "RasCAL-2",
        "RasCAL-2",
    )


def delete_local_settings(path: str | PathLike) -> None:
    """Delete the "settings.json" file.

    Parameters
    ----------
    path: str or PathLike
        The path to the folder where the settings are saved.
    """
    file = Path(path, "settings.json")
    file.unlink(missing_ok=True)


class SettingsGroups(StrEnum):
    """The groups of the RasCAL-2 settings, used to set tabs in the dialog"""

    General = "General"
    Logging = "Logging"
    Terminal = "Terminal"
    Windows = "Windows"


class Styles(StrEnum):
    """Visual styles for RasCAL-2."""

    Light = "light"


class LogLevels(IntEnum):
    """Debug log-levels with human readable string names."""

    Debug = logging.DEBUG
    Info = logging.INFO
    Warning = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL

    def __str__(self):
        names = {
            LogLevels.Debug: "DEBUG",
            LogLevels.Info: "INFO",
            LogLevels.Warning: "WARNING",
            LogLevels.Error: "ERROR",
            LogLevels.Critical: "CRITICAL",
        }
        return names[self]

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(getattr(logging, value.upper()))
        raise ValueError("Not a known logging level.")


# WindowGeometry is a tuple (x, y, width, height, minimized)
# where 'minimized' is True iff the window is minimized
WindowGeometry: TypeAlias = tuple[int, int, int, int, bool]


class MDIGeometries(BaseModel):
    """Model for storing window positions and sizes."""

    plots: WindowGeometry = Field(max_length=5, min_length=5)
    project: WindowGeometry = Field(max_length=5, min_length=5)
    terminal: WindowGeometry = Field(max_length=5, min_length=5)
    controls: WindowGeometry = Field(max_length=5, min_length=5)


class Settings(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """Model for system settings.

    If a setting is not provided, it will fallback to the global default.

    Notes
    -----
    For each system setting, the model field `title` contains the setting group,
    and the model field `description` gives an English name for the setting.
    The model fields for a setting can be accessed via Settings.model_fields[setting].

    """

    # The Settings object's own model fields contain the within-project settings.
    # The global settings are read and written via this object using `set_global_settings`.
    style: Styles = Field(default=Styles.Light, title=SettingsGroups.General, description="Style")
    editor_fontsize: int = Field(default=12, title=SettingsGroups.General, description="Editor Font Size", gt=0)

    log_path: str = Field(default="logs/rascal.log", title=SettingsGroups.Logging, description="Path to Log File")
    log_level: LogLevels = Field(default=LogLevels.Info, title=SettingsGroups.Logging, description="Minimum Log Level")

    clear_terminal: bool = Field(
        default=True, title=SettingsGroups.Terminal, description="Clear Terminal when Run Starts"
    )
    terminal_fontsize: int = Field(default=12, title=SettingsGroups.Terminal, description="Terminal Font Size", gt=0)

    mdi_defaults: MDIGeometries = Field(
        default=None, title=SettingsGroups.Windows, description="Default Window Geometries"
    )

    def model_post_init(self, __context: Any):
        global_settings = get_global_settings()
        unset_settings = [s for s in self.model_fields if s not in self.model_fields_set]
        for setting in unset_settings:
            if global_name(setting) in global_settings.allKeys():
                setattr(self, setting, global_settings.value(global_name(setting)))
                self.model_fields_set.remove(setting)  # we don't want global defaults to count as manually set!

    def save(self, path: str | PathLike):
        """Save settings to a JSON file in the given path.

        Parameters
        ----------
        path : str or PathLike
            The path to the folder where settings will be saved.

        """
        Path(path, "settings.json").write_text(self.model_dump_json(exclude_unset=True))

    def set_global_settings(self):
        """Set manually-set local settings as global settings."""
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


def update_recent_projects(path: str | None = None) -> list[str]:
    """Update the saved recent project paths.

    Recent projects are stored as a list of the ten most recent, ordered oldest to newest.
    Only the most recent three will be visible; the rest are a buffer for projects being
    deleted.

    Parameters
    ----------
    path : str, optional
        The path of the most recently saved project to add, or None if no project is being saved.

    Returns
    -------
    str
        The updated recent project list.

    """
    recent_projects: list[str] = get_global_settings().value("internal/recent_projects")
    if not recent_projects:
        recent_projects = []

    if path is not None:
        if path in recent_projects:
            recent_projects.remove(path)
        recent_projects.append(str(path))

    for project in recent_projects:
        if not Path(project).exists():
            recent_projects.remove(project)

    recent_projects = recent_projects[-10:]

    get_global_settings().setValue("internal/recent_projects", recent_projects)
    return recent_projects
