"""Minimal persistent settings for compas_fea2.

- Stores a tiny JSON config in ~/.compas_fea2/config.json (by default via Settings.from_config).
- HOME, DATA, DOCS are derived from the package location and are read-only defaults.
- TEMP is user-configurable and can be persisted with to_config().

Quick usage:
    from compas_fea2.config import settings
    # Read paths
    print(settings.HOME, settings.DATA, settings.TEMP)
    # Change TEMP and persist
    settings.TEMP = "/path/to/temp"
    settings.to_config()
    # Reset to defaults and persist
    settings.reset(persist=True)
"""

from __future__ import annotations

import os
import json
from compas.geometry import Frame


class Settings:
    """Container for configuration and resolved project paths.

    Attributes:
        HOME (str): Root of the package (fixed, derived from file location).
        DATA (str): DATA folder under HOME (fixed).
        DOCS (str): DOCS folder under HOME (fixed).
        TEMP (str): Temporary folder (user-configurable; persisted in config.json).
        VERBOSE (bool): Runtime verbosity flag (not persisted by default).
        GLOBAL_FRAME (Frame): Global reference frame (runtime only).
    """

    def __init__(self, config_dir, temp=None):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        self.DATA = os.path.abspath(os.path.join(self.HOME, "data"))
        self.DOCS = os.path.abspath(os.path.join(self.HOME, "docs"))
        self.TEMP = temp or os.path.abspath(os.path.join(self.HOME, "temp"))

        self.VERBOSE = False
        self.GLOBAL_FRAME = Frame.worldXY()
        self.PRECISION = 2  # decimal places for output formatting

    @classmethod
    def from_config(cls, config_dir):
        """Load settings from a config directory.

        - If config_dir/config.json does not exist, a file is created with defaults
          and those values are returned.
        - If the file exists, values are read and used to initialize Settings.

        Parameters:
            config_dir (str): Directory where config.json lives.

        Returns:
            Settings: Initialized settings instance.
        """
        config_file = os.path.join(config_dir, "config.json")
        if not os.path.exists(config_file):
            settings = cls(os.path.join(os.path.expanduser("~"), ".compas_fea2"))
            settings.to_config()
            return settings
        else:
            with open(config_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        return cls(**data) if isinstance(data, dict) else settings()

    def to_config(self) -> None:
        """Persist the current configuration to config.json.

        Writes a JSON file with the keys required to recreate this instance via
        from_config: currently "config_dir" and "temp".
        """
        os.makedirs(self.config_dir, exist_ok=True)
        cfg = {
            "config_dir": self.config_dir,
            "temp": self.TEMP,
        }
        with open(self.config_file, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, sort_keys=True)

    def reset(self, persist: bool = True) -> None:
        """Reset settings to library defaults.

        - TEMP -> <HOME>/temp
        - VERBOSE -> False
        - GLOBAL_FRAME -> Frame.worldXY()

        Parameters:
            persist (bool): If True, write the defaults to config.json via to_config().
        """
        self.TEMP = os.path.abspath(os.path.join(self.HOME, "temp"))
        self.VERBOSE = False
        self.GLOBAL_FRAME = Frame.worldXY()

        if persist:
            self.to_config()


# Initialize settings at import time; create file with defaults if needed.
settings: Settings = Settings.from_config(os.path.join(os.path.expanduser("~"), ".compas_fea2"))
