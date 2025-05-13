
import json
import logging

logging.basicConfig(level=logging.INFO)


class ConfigManager:
    """Handles loading and saving bot configuration."""

    def __init__(self, config_file="config.json"):
        """
        Initialize the ConfigManager with the given config file.

        Args:
            config_file (str): The path to the configuration file (default is "config.json").
        """
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding='UTF-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("⚠️ Config file not found!")
            return {}

    def save_config(self):
        with open(self.config_file, "w", encoding='UTF-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()