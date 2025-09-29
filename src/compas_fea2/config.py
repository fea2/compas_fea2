"""Minimal persistent settings for compas_fea2.

- Stores a tiny JSON config in ~/.compas_fea2/config.json (by default via Settings.from_config).
- HOME, DATA, DOCS are derived from the package location and are read-only defaults.
- TEMP is user-configurable and can be persisted with to_config().
- UNIT_SYSTEM is user-configurable and can be persisted and automatically applied on import.
- USE_UNITS is a global on/off switch for unit checking (default True).
- OUTPUT_MAGNITUDES is a global preference for returning magnitudes even when units are enabled (default False).

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

import json
import os

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
        UNIT_SYSTEM (str): Name of the active unit system (e.g. 'SI', 'SI-mm', 'Imperial').
        USE_UNITS (bool): Global on/off switch for unit checking (default True).
        OUTPUT_MAGNITUDES (bool): Preference for returning magnitudes even when units enabled (default False).
    """

    def __init__(self, config_dir, temp=None, unit_system="SI", use_units=True, output_magnitudes=False):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        self.DATA = os.path.abspath(os.path.join(self.HOME, "data"))
        self.DOCS = os.path.abspath(os.path.join(self.HOME, "docs"))
        self.TEMP = temp or os.path.abspath(os.path.join(self.HOME, "temp"))
        self.UNIT_SYSTEM = unit_system or "SI"

        self.USE_UNITS = use_units
        self.OUTPUT_MAGNITUDES = output_magnitudes

        self.VERBOSE = False
        self.GLOBAL_FRAME = Frame.worldXY()
        self.PRECISION = 2  # decimal places for output formatting

        self._apply_unit_system()

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
            settings = cls(os.path.join(os.path.expanduser("~"), ".compas_fea2"), unit_system="SI")
            settings.to_config()
            return settings
        else:
            with open(config_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        if isinstance(data, dict):
            use_units = data.get("use_units", True)
            output_magnitudes = data.get("output_magnitudes", False)
            return cls(
                config_dir=data.get("config_dir", os.path.join(os.path.expanduser("~"), ".compas_fea2")),
                temp=data.get("temp"),
                unit_system=data.get("unit_system", "SI"),
                use_units=use_units,
                output_magnitudes=output_magnitudes,
            )
        else:
            return cls(os.path.join(os.path.expanduser("~"), ".compas_fea2"), unit_system="SI")

    def to_config(self) -> None:
        """Persist the current configuration to config.json.

        Writes a JSON file with the keys required to recreate this instance via
        from_config: currently "config_dir" and "temp".
        """
        os.makedirs(self.config_dir, exist_ok=True)
        cfg = {
            "config_dir": self.config_dir,
            "temp": self.TEMP,
            "unit_system": self.UNIT_SYSTEM,
            "use_units": self.USE_UNITS,
            "output_magnitudes": self.OUTPUT_MAGNITUDES,
        }
        with open(self.config_file, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, sort_keys=True)

    def reset(self, persist: bool = True) -> None:
        """Reset settings to library defaults.

        - TEMP -> <HOME>/temp
        - VERBOSE -> False
        - GLOBAL_FRAME -> Frame.worldXY()
        - USE_UNITS -> True
        - OUTPUT_MAGNITUDES -> False

        Parameters:
            persist (bool): If True, write the defaults to config.json via to_config().
        """
        self.TEMP = os.path.abspath(os.path.join(self.HOME, "temp"))
        self.VERBOSE = False
        self.GLOBAL_FRAME = Frame.worldXY()
        self.USE_UNITS = True
        self.OUTPUT_MAGNITUDES = False

        if persist:
            self.to_config()

    def _apply_unit_system(self) -> None:
        """Apply the configured unit system to compas_fea2.units."""
        try:
            from compas_fea2.units import list_unit_systems
            from compas_fea2.units import set_unit_system

            set_unit_system(self.UNIT_SYSTEM)
        except Exception:
            # Fallback to SI if an unknown system was configured
            try:
                set_unit_system("SI")
                self.UNIT_SYSTEM = "SI"
            except Exception:
                # As a last resort, ignore (units subsystem may not be available at import time)
                pass

    def set_units(self, unit_system: str, *, persist: bool = True) -> None:
        """Change the active unit system and apply it immediately.

        Parameters
        ----------
        unit_system : str
            One of the known systems (e.g., 'SI', 'SI-mm', 'Imperial') or a custom name
            if your application provides it at runtime.
        persist : bool
            If True, write the new unit system to config.json.
        """
        self.UNIT_SYSTEM = unit_system
        self._apply_unit_system()
        if persist:
            self.to_config()

    def set_units_enabled(self, enabled: bool, *, persist: bool = True) -> None:
        """Enable or disable unit checking globally.

        Parameters
        ----------
        enabled : bool
            True to enable units, False to disable.
        persist : bool
            If True, write the change to config.json.
        """
        self.USE_UNITS = enabled
        if persist:
            self.to_config()

    def set_output_magnitudes(self, enabled: bool, *, persist: bool = True) -> None:
        """Set the preference for returning magnitudes even when units are enabled.

        Parameters
        ----------
        enabled : bool
            True to return magnitudes, False to return Quantity objects.
        persist : bool
            If True, write the change to config.json.
        """
        self.OUTPUT_MAGNITUDES = enabled
        if persist:
            self.to_config()


# Initialize settings at import time; create file with defaults if needed.
settings: Settings = Settings.from_config(os.path.join(os.path.expanduser("~"), ".compas_fea2"))
