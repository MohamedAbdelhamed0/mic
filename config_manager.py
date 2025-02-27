import json
from pathlib import Path
import os
import shutil

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Clean up cache by verifying entries
        self.clean_cache_on_startup()
        
    def load_settings(self):
        if self.config_file.exists():
            try:
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
                    if "cached_files" not in settings:
                        settings["cached_files"] = {}
                    return settings
            except json.JSONDecodeError:
                print("Error loading settings file, using defaults")
                # Create a backup of the corrupted file
                if self.config_file.exists():
                    backup_path = self.config_dir / f"settings_backup_{int(time.time())}.json"
                    shutil.copy2(self.config_file, backup_path)
                    
        # Return default settings
        return {
            "last_device": None, 
            "cached_files": {},
            "voice_mode": False,
            "voice_quality": "medium",
            "theme": "dark_blue",
            "favorites": []
        }
    
    def save_settings(self, settings):
        """Save settings with backup mechanism"""
        # Create temp file first
        temp_file = self.config_dir / "settings.tmp"
        try:
            with open(temp_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # If successful, replace the actual file
            if temp_file.exists():
                if self.config_file.exists():
                    self.config_file.unlink()
                temp_file.rename(self.config_file)
        except Exception as e:
            print(f"Error saving settings: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def clean_cache_on_startup(self):
        """Verify cache files exist and clean up broken entries"""
        try:
            if not self.config_file.exists():
                return
                
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
            
            if "cached_files" not in settings:
                return
                
            # Check each cached file
            files_to_remove = []
            for file_name, file_path in settings["cached_files"].items():
                if not os.path.exists(file_path):
                    files_to_remove.append(file_name)
            
            # Remove missing files
            for file_name in files_to_remove:
                del settings["cached_files"][file_name]
            
            # Save updated settings
            self.save_settings(settings)
        except Exception as e:
            print(f"Error cleaning cache: {e}")
