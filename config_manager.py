import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    def load_settings(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
                # Add default settings if not present
                if "voice_mode" not in settings:
                    settings["voice_mode"] = False
                if "voice_quality" not in settings:
                    settings["voice_quality"] = "medium"
                if "theme" not in settings:
                    settings["theme"] = "dark_blue"
                if "favorites" not in settings:
                    settings["favorites"] = []
                return settings
        return {
            "last_device": None, 
            "cached_files": {},
            "voice_mode": False,
            "voice_quality": "medium",
            "theme": "dark_blue",
            "favorites": []
        }
    
    def save_settings(self, settings):
        with open(self.config_file, 'w') as f:
            json.dump(settings, f)
