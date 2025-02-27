import customtkinter as ctk
from pathlib import Path
import atexit
import signal
import psutil
import os
import sys
import subprocess
from config_manager import ConfigManager
from device_manager import DeviceManager
from audio_controller import AudioController
from theme_manager import ThemeManager
from shortcuts import KeyboardShortcuts
from tkinter import messagebox
from player_ui import PlayerUI
from player_controller import PlayerController
from pydub import AudioSegment

class AudioMicPlayer:
    def __init__(self):
        self.setup_ffmpeg()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        self.theme_manager = ThemeManager()
        self.callback_timer_id = None
        
        # Set theme from settings
        if "theme" in self.settings:
            self.theme_manager.set_theme(self.settings["theme"])
        
        # Initialize device manager with cached device
        self.device_manager = DeviceManager(self.settings.get("last_device"))
        self.audio_controller = AudioController(self.device_manager)
        self.current_playback = None
        self.is_playing = False
        self.audio_files = {}
        self.file_widgets = {}  # Dictionary to track file widgets
        
        # Load voice mode settings
        self.audio_controller.voice_mode = self.settings.get("voice_mode", False)
        self.audio_controller.voice_quality = self.settings.get("voice_quality", "medium")
        
        # Setup window and UI
        self.setup_window()
        self.initialize_components()
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def setup_ffmpeg(self):
        """Initialize ffmpeg path and configure pydub to avoid console windows"""
        try:
            # Try to find ffmpeg in common locations
            ffmpeg_paths = [
                r"C:\ffmpeg-7.1-essentials_build\ffmpeg-7.1-essentials_build\bin",
                r"C:\ffmpeg-7.1-essentials_build\ffmpeg-7.1-essentials_build",
                r"C:\ffmpeg\bin",
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs\\ffmpeg\\bin'),
                os.path.join(os.environ.get('PROGRAMFILES', ''), 'ffmpeg\\bin'),
            ]
            
            ffmpeg_found = False
            for path in ffmpeg_paths:
                if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
                    os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                    print(f"Found ffmpeg in: {path}")
                    ffmpeg_found = True
                    break

            # If ffmpeg found, configure pydub to use subprocess without console window
            if ffmpeg_found:
                # Configure pydub to avoid console windows
                AudioSegment.converter = os.path.join(path, "ffmpeg.exe")
                
                # Apply special handling when app is frozen (in executable)
                if getattr(sys, 'frozen', False):
                    # This ensures subprocess calls don't open console windows
                    from ffmpeg_utils import run_ffmpeg_command
                    # Monkey patch subprocess.run that pydub might use internally
                    original_run = subprocess.run
                    def patched_run(cmd, *args, **kwargs):
                        if isinstance(cmd, list) and any('ffmpeg' in str(x) for x in cmd):
                            return run_ffmpeg_command(cmd, *args, **kwargs)
                        return original_run(cmd, *args, **kwargs)
                    subprocess.run = patched_run
            else:
                # If not found, show error
                messagebox.showerror(
                    "FFmpeg Not Found",
                    "Please move ffmpeg to the correct location:\n"
                    "1. Create folder: C:\\ffmpeg\\bin\n"
                    "2. Copy ffmpeg.exe, ffprobe.exe from:\n"
                    "   C:\\ffmpeg-7.1-essentials_build\\ffmpeg-7.1-essentials_build\\bin\n"
                    "3. Paste them into: C:\\ffmpeg\\bin"
                )
                
        except Exception as e:
            print(f"Warning: ffmpeg setup failed: {e}")
    
    def setup_window(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.window = ctk.CTk()
        self.window.title("Audio to Mic Player")
        self.window.geometry("780x580")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.configure(fg_color=self.theme_manager.get_color("bg_primary"))
        
        # Configure grid layout
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=0)
    
    def initialize_components(self):
        # Initialize UI first without controller connections
        self.player_ui = PlayerUI(self, self.window, self.theme_manager)
        self.player_ui.setup_ui()
        
        # Initialize controller
        self.player_controller = PlayerController(
            self, 
            self.audio_controller,
            self.player_ui, 
            self.device_manager,
            self.theme_manager
        )
        
        # Now connect the UI to the controller
        self.player_ui.connect_controller(self.player_controller)
        
        # Set callback for playback ending
        self.audio_controller.set_playback_ended_callback(self.player_controller.on_audio_ended)
        
        # Initialize keyboard shortcuts
        self.shortcuts = KeyboardShortcuts(self)
        
        # Start progress update timer
        self.start_progress_timer()
    
    def start_progress_timer(self):
        # Cancel existing timer if any
        self.cancel_progress_timer()
        # Start new timer
        self.callback_timer_id = self.window.after(50, self.player_controller.update_global_progress)
    
    def cancel_progress_timer(self):
        if self.callback_timer_id:
            try:
                self.window.after_cancel(self.callback_timer_id)
            except Exception:
                pass
            self.callback_timer_id = None
    
    def change_theme(self, theme_name):
        """Change the application theme"""
        # Cancel any pending callbacks before destroying UI
        self.cancel_progress_timer()
        
        self.theme_manager.set_theme(theme_name)
        self.settings["theme"] = theme_name
        self.config_manager.save_settings(self.settings)
        
        # First, remove all widgets
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Clear widget references
        self.file_widgets = {}
        
        # Update window background
        self.window.configure(fg_color=self.theme_manager.get_color("bg_primary"))
        
        # Rebuild the entire UI
        self.initialize_components()
    
    def cleanup(self):
        self.cancel_progress_timer()
        if self.audio_controller:
            self.audio_controller.stop()
        
        # Kill any zombie processes more aggressively
        try:
            current_process = psutil.Process(os.getpid())
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
                    
            # Wait briefly for processes to terminate
            gone, alive = psutil.wait_procs(children, timeout=1)
            
            # Force kill any remaining processes
            for process in alive:
                try:
                    process.kill()
                except:
                    pass
        except Exception as e:
            print(f"Error cleaning up processes: {e}")
    
    def signal_handler(self, signum, frame):
        self.cleanup()
        self.window.quit()
    
    def on_closing(self):
        self.cleanup()
        self.window.quit()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AudioMicPlayer()
    app.run()
