import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages persistent application settings using a JSON configuration file.
    """

    def __init__(self, config_file: str = "settings.json"):
        """
        Initializes the ConfigManager.

        Args:
            config_file (str): The path to the JSON configuration file.
        """
        self.config_path = Path(config_file)
        self.settings: Dict[str, Any] = {}
        
        self.load_settings()

    def load_settings(self) -> None:
        """
        Loads settings from the JSON configuration file into memory.
        Initializes default settings if the file does not exist.
        """
        if not self.config_path.exists():
            self._set_defaults()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
                self._validate_profiles()
        except Exception as e:
            logger.error(f"Failed to load settings from {self.config_path}: {e}")
            self._set_defaults()

    def save_settings(self, new_settings: Dict[str, Any] = None) -> None:
        """
        Saves the current memory settings to the JSON configuration file.

        Args:
            new_settings (Dict[str, Any], optional): Dictionary of settings to update before saving.
        """
        if new_settings:
            self.settings.update(new_settings)

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings to {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific setting value.

        Args:
            key (str): The setting key.
            default (Any, optional): The default value to return if the key is not found.

        Returns:
            Any: The value of the requested setting.
        """
        return self.settings.get(key, default)

    def _set_defaults(self) -> None:
        """
        Initializes default settings.
        """
        self.settings = {
            "language": "en",
            "profiles": {
                "Default Game": {
                    "versions": {},
                    "last_v1": "",
                    "last_v2": ""
                }
            },
            "current_profile": "Default Game",
            "filters_in": {},
            "filters_out": {}
        }

    def _validate_profiles(self) -> None:
        """
        Ensures that loaded profiles have the correct structure, 
        performing structural migrations if necessary.
        """
        profiles = self.settings.get("profiles", {})
        for p_name, p_data in profiles.items():
            if "versions" not in p_data:
                v1_name = p_data.get("v1_name", "V1")
                v2_name = p_data.get("v2_name", "V2")
                profiles[p_name] = {
                    "versions": {
                        v1_name: p_data.get("v1_path", ""), 
                        v2_name: p_data.get("v2_path", "")
                    },
                    "last_v1": v1_name,
                    "last_v2": v2_name
                }
        self.settings["profiles"] = profiles