import customtkinter as ctk
from pathlib import Path
import numpy as np
from pydub import AudioSegment
import webbrowser
import subprocess
from tkinter import messagebox, filedialog
from audio_file_widget import AudioFileWidget
from ffmpeg_utils import run_ffmpeg_command, process_audio_in_thread

class PlayerController:
    def __init__(self, app, audio_controller, ui, device_manager, theme_manager):
        self.app = app
        self.audio_controller = audio_controller
        self.ui = ui
        self.device_manager = device_manager
        self.theme_manager = theme_manager
        
        # Set initial state for loop functionality
        self.is_looping = self.audio_controller.is_looping
        
        # Set initial volume in UI
        self.ui.volume_slider.set(self.audio_controller.volume)
        self.ui.sidebar_vol_slider.set(self.audio_controller.volume)
        
    def update_global_progress(self):
        """Update the global progress bar and time information with reduced updates for better performance"""
        try:
            if self.audio_controller.is_playing:
                position = self.audio_controller.position
                duration = self.audio_controller.duration
                
                if (duration > 0):  # Avoid division by zero
                    self.ui.global_progress.set(position / duration)
                
                # Update time labels only if they've changed significantly
                # This reduces unnecessary UI updates for better performance
                mins_elapsed = int(position // 60)
                secs_elapsed = int(position % 60)
                
                mins_remaining = int((duration - position) // 60)
                secs_remaining = int((duration - position) % 60)
                
                # Create formatted time strings
                elapsed_str = f"{mins_elapsed}:{secs_elapsed:02d}"
                remaining_str = f"-{mins_remaining}:{secs_remaining:02d}"
                
                # Only update if changed
                if self.ui.time_elapsed.cget("text") != elapsed_str:
                    self.ui.time_elapsed.configure(text=elapsed_str)
                if self.ui.time_remaining.cget("text") != remaining_str:
                    self.ui.time_remaining.configure(text=remaining_str)
                
                # Update play/pause button state only when paused state changes
                play_pause_text = "⏸" if not self.audio_controller.is_paused else "▶"
                if self.ui.play_pause_btn.cget("text") != play_pause_text:
                    self.ui.play_pause_btn.configure(
                        text=play_pause_text,
                        fg_color=self.theme_manager.get_color("accent_secondary") if not self.audio_controller.is_paused 
                        else self.theme_manager.get_color("accent_primary")
                    )
                
                # Update current playing song info only if changed
                if self.audio_controller.current_widget:
                    file_name = self.audio_controller.current_widget.file_name
                    if self.ui.current_song_label.cget("text") != file_name:
                        self.ui.current_song_label.configure(text=file_name)
                        self.update_playing_highlight()
            else:
                # Reset time display when nothing is playing
                if self.ui.time_elapsed.cget("text") != "0:00":
                    self.ui.time_elapsed.configure(text="0:00")
                if self.ui.time_remaining.cget("text") != "-0:00":
                    self.ui.time_remaining.configure(text="-0:00")
                if self.ui.play_pause_btn.cget("text") != "▶":
                    self.ui.play_pause_btn.configure(
                        text="▶",
                        fg_color=self.theme_manager.get_color("accent_primary")
                    )
            
            # Reschedule the timer with REDUCED frequency for better performance
            self.app.callback_timer_id = self.app.window.after(100, self.update_global_progress)
        except Exception as e:
            print(f"Error updating progress: {e}")
            # Reschedule even on error
            self.app.callback_timer_id = self.app.window.after(1000, self.update_global_progress)
    
    def update_playing_highlight(self):
        """Ensure the currently playing track is highlighted in the list with safety checks"""
        try:
            widgets = self.get_file_widgets()
            current_widget = self.audio_controller.current_widget
            
            for widget in widgets:
                if widget == current_widget:
                    # Check if widget still exists before updating
                    if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                        widget.configure(fg_color=self.theme_manager.get_color("accent_primary"))
                        widget.playing_indicator.configure(fg_color=self.theme_manager.get_color("accent_secondary"))
                else:
                    if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                        widget.configure(fg_color=self.theme_manager.get_color("bg_secondary"))
                        widget.playing_indicator.configure(fg_color="transparent")
        except Exception as e:
            print(f"[ERROR] Error updating highlighting: {e}")
    
    def on_search(self, *args):
        """Filter files based on search text"""
        self.update_file_list()
    
    def seek_global(self, position):
        """Global seek function for the progress bar"""
        if self.audio_controller.current_widget:
            self.audio_controller.seek(float(position))
    
    def toggle_global_playback(self):
        """Toggle play/pause for currently active track"""
        print("[DEBUG] Toggle global playback called")
        
        if self.audio_controller.is_playing:
            if self.audio_controller.is_paused:
                print("[DEBUG] Resuming paused playback")
                self.audio_controller.resume()
                self.ui.play_pause_btn.configure(text="⏸")
            else:
                print("[DEBUG] Pausing active playback")
                self.audio_controller.pause()
                self.ui.play_pause_btn.configure(text="▶")
        elif self.audio_controller.current_widget:
            # If a track was selected but stopped, restart it
            print(f"[DEBUG] Restarting last track: {self.audio_controller.current_widget.file_name}")
            self.audio_controller.current_widget.toggle_play()
            self.ui.play_pause_btn.configure(text="⏸")
        else:
            # Play first track if nothing is selected
            widgets = self.get_file_widgets()
            if widgets:
                print(f"[DEBUG] Playing first track: {widgets[0].file_name}")
                widgets[0].toggle_play()
                self.ui.play_pause_btn.configure(text="⏸")
            else:
                print("[DEBUG] No tracks available to play")
    
    def stop_global_playback(self):
        """Stop the currently playing track"""
        print("[DEBUG] Stopping global playback")
        if self.audio_controller.is_playing:
            current_widget = self.audio_controller.current_widget
            self.audio_controller.stop()
            self.ui.play_pause_btn.configure(text="▶")
            self.ui.current_song_label.configure(text="No song playing")
            
            # Update the widget UI state
            if current_widget:
                print(f"[DEBUG] Updating UI state for widget: {current_widget.file_name}")
                current_widget.is_playing = False
                current_widget.play_btn.configure(text="▶")
                current_widget.update_ui_state()
                
            print("[DEBUG] Playback stopped successfully")
    
    def set_global_volume(self, value):
        """Set the global volume level"""
        self.audio_controller.set_volume(float(value))
        # Update the other volume slider if it exists
        try:
            self.ui.sidebar_vol_slider.set(float(value))
        except:
            pass
    
    def set_global_volume_with_label(self, value):
        """Set the global volume level and update the label"""
        self.set_global_volume(value)
        self.ui.vol_value_label.configure(text=f"{int(float(value) * 100)}%")
    
    def toggle_global_mute(self):
        """Toggle mute for all playback"""
        self.audio_controller.toggle_mute()
        self.ui.mute_btn.configure(text="🔈" if self.audio_controller.muted else "🔊")
        # Update sidebar mute button if it exists
        try:
            self.ui.sidebar_mute_btn.configure(text="Unmute" if self.audio_controller.muted else "Mute")
        except:
            pass
    
    def toggle_global_mute_with_label(self):
        """Toggle mute for all playback and update the button label"""
        self.toggle_global_mute()
    
    def toggle_global_loop(self):
        """Toggle loop state for current track"""
        self.audio_controller.is_looping = not self.audio_controller.is_looping
        self.is_looping = self.audio_controller.is_looping  # Keep local state in sync
        
        # Update loop button appearance
        self.ui.loop_btn.configure(
            fg_color=self.theme_manager.get_color("accent_primary") if self.audio_controller.is_looping 
            else self.theme_manager.get_color("button_bg")
        )
        
        # Update loop state in current widget if exists
        if self.audio_controller.current_widget:
            self.audio_controller.current_widget.is_looping = self.audio_controller.is_looping
            self.audio_controller.current_widget.update_loop_button()
    
    def on_audio_ended(self, widget):
        """Called when audio playback ends"""
        print(f"[DEBUG] Audio ended, loop state: {self.is_looping}, track: {widget.file_name}")
        
        try:
            if self.audio_controller.is_looping:
                # If looping is enabled, restart the same track after a small delay
                print(f"[DEBUG] Looping track: {widget.file_name}")
                self.app.window.after(100, lambda: widget.toggle_play())
            else:
                # Auto-play next track
                print(f"[DEBUG] Auto-playing next track after: {widget.file_name}")
                self.next_track()
        except Exception as e:
            print(f"[ERROR] Error in on_audio_ended: {e}")
    
    def get_file_widgets(self):
        """Get all current file widgets"""
        return [w for w in self.ui.files_list.winfo_children() 
                if isinstance(w, AudioFileWidget)]
    
    def previous_track(self):
        """Play the previous track in the list"""
        widgets = self.get_file_widgets()
        if not widgets:
            return
            
        if self.audio_controller.current_widget in widgets:
            current_index = widgets.index(self.audio_controller.current_widget)
            prev_index = (current_index - 1) % len(widgets)
            widgets[prev_index].toggle_play()
        else:
            widgets[-1].toggle_play()  # Play the last track
    
    def next_track(self):
        """Play the next track in the list with safety checks"""
        widgets = self.get_file_widgets()
        if not widgets:
            print("[DEBUG] No tracks available to play next")
            return
        
        # Make sure the current widget is actually valid
        current_widget = self.audio_controller.current_widget
        if current_widget and (not hasattr(current_widget, 'winfo_exists') or not current_widget.winfo_exists()):
            print("[DEBUG] Current widget no longer exists")
            current_widget = None
            self.audio_controller.current_widget = None
            
        if current_widget in widgets:
            current_index = widgets.index(current_widget)
            next_index = (current_index + 1) % len(widgets)
            print(f"[DEBUG] Playing next track: {widgets[next_index].file_name}")
            
            # Stop current track first to ensure clean state
            if self.audio_controller.is_playing:
                self.audio_controller.stop()
                
            # Play next track
            widgets[next_index].toggle_play()
        else:
            print(f"[DEBUG] No current track - playing first: {widgets[0].file_name}")
            widgets[0].toggle_play()  # Play the first track
    
    def refresh_devices(self):
        """Refresh the list of audio output devices"""
        devices = self.device_manager.get_output_devices()
        device_list = [f"{i}: {device['name']}" for i, device in devices]
        self.ui.device_menu.configure(values=device_list)
        
        # Set current device in dropdown
        current_device = self.device_manager.get_current_device()
        for device_str in device_list:
            if device_str.startswith(str(current_device)):
                self.ui.device_menu.set(device_str)
                break
    
    def on_device_change(self, selection):
        """Change the output audio device"""
        try:
            device_id = int(selection.split(':')[0])
            print(f"Selecting device: {device_id}")
            
            # Set new device
            self.device_manager.set_device(device_id)
            
            # Save to settings immediately
            self.app.settings["last_device"] = device_id
            self.app.config_manager.save_settings(self.app.settings)
            
            # Restart any active playback with new device
            self.audio_controller.restart_playback()
            
            print(f"Current device after selection: {self.device_manager.get_current_device()}")
        except Exception as e:
            print(f"Error changing device: {e}")
            messagebox.showerror("Error", f"Failed to change device: {str(e)}")
    
    def add_audio_file(self):
        """Add a new audio file to the player with improved processing"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a")]
        )
        if not file_path:
            return
            
        print(f"\n=== Adding audio file: {file_path} ===")
        
        # Verify file exists and is readable
        try:
            with open(file_path, 'rb') as f:
                pass
        except Exception as e:
            print(f"Error: Cannot read file: {e}")
            messagebox.showerror("Error", f"Cannot read file: {str(e)}")
            return

        file_name = Path(file_path).name
        cache_path = str(self.app.config_manager.cache_dir / file_name)
        print(f"Cache path: {cache_path}")
        
        # Check if file is already cached with the same name
        if file_name in self.app.settings["cached_files"]:
            cached_file = Path(self.app.settings["cached_files"][file_name])
            if cached_file.exists():
                print("File already cached, reusing")
                # Update file list and exit
                self.update_file_list()
                return
                
        # Show a loading indicator or status message
        loading_label = ctk.CTkLabel(
            self.ui.files_list,
            text=f"Converting {file_name}...",
            fg_color=self.theme_manager.get_color("bg_secondary"),
            corner_radius=6
        )
        loading_label.pack(fill="x", padx=5, pady=3)
        self.ui.files_list.update()  # Force UI update to show loading message
        
        # Process the file in a background thread
        def on_conversion_complete(success, error_msg):
            # Remove loading indicator
            loading_label.destroy()
            
            if success:
                print("File cached successfully")
                self.app.settings["cached_files"][file_name] = cache_path
                self.app.config_manager.save_settings(self.app.settings)
                self.update_file_list()
                print("=== Audio file added successfully ===\n")
            else:
                messagebox.showerror(
                    "Error", 
                    f"Failed to add audio file: {error_msg}\n\n"
                    "Please ensure ffmpeg is installed properly."
                )
                
        # Start conversion in background thread
        process_audio_in_thread(
            input_path=file_path,
            output_path=cache_path,
            format="wav",
            callback=on_conversion_complete
        )
    
    def update_file_list(self):
        """Update the list of audio files in the UI with improved performance"""
        print("[DEBUG] Updating file list")
        
        # Clear existing widgets in files_list
        for widget in self.ui.files_list.winfo_children():
            widget.destroy()
        
        self.app.file_widgets = {}
        
        # Filter by search text if provided
        search_text = self.ui.search_var.get().lower()
        if search_text:
            print(f"[DEBUG] Filtering by search: '{search_text}'")
        
        # Verify cache files exist before adding to UI
        valid_files = {}
        for file_name, file_path in self.app.settings["cached_files"].items():
            # Apply search filter if needed
            if search_text and search_text not in file_name.lower():
                continue
                
            # Check if file actually exists
            path_obj = Path(file_path)
            if path_obj.exists():
                valid_files[file_name] = file_path
            else:
                # File was deleted or moved, remove from settings
                print(f"[DEBUG] Removing missing file from cache: {file_name}")
                del self.app.settings["cached_files"][file_name]
                
        # Save cleaned up settings
        if len(valid_files) != len(self.app.settings["cached_files"]):
            self.app.config_manager.save_settings(self.app.settings)
        
        # Add each valid file as an AudioFileWidget
        print(f"[DEBUG] Adding {len(valid_files)} files to UI")
        for file_name, file_path in valid_files.items():
            file_widget = AudioFileWidget(
                self.ui.files_list,
                file_name,
                file_path,
                self.remove_file,
                self.audio_controller,
                fg_color=self.theme_manager.get_color("bg_secondary"),
                corner_radius=6
            )
            file_widget.pack(fill="x", padx=5, pady=3)
            
            # Set the loop state to match the global state
            file_widget.is_looping = self.audio_controller.is_looping
            
            self.app.file_widgets[file_name] = file_widget
            
        print("[DEBUG] File list updated successfully")
    
    def remove_file(self, file_name):
        """Remove an audio file from the player"""
        if file_name in self.app.settings["cached_files"]:
            cache_path = Path(self.app.settings["cached_files"][file_name])
            if cache_path.exists():
                cache_path.unlink()
            del self.app.settings["cached_files"][file_name]
            self.app.config_manager.save_settings(self.app.settings)
            self.update_file_list()
    
    def toggle_voice_mode(self):
        """Toggle voice application mode"""
        voice_mode = self.ui.voice_mode_var.get()
        self.audio_controller.set_voice_mode(voice_mode)
        
        # Save to settings
        self.app.settings["voice_mode"] = voice_mode
        self.app.config_manager.save_settings(self.app.settings)
        
        if voice_mode:
            messagebox.showinfo(
                "Voice Application Mode Enabled",
                "For best results with Discord or other voice apps:\n\n"
                "1. Select 'VB-Cable' as your output device here\n"
                "2. In Discord, select 'VB-Cable' as your input device\n"
                "3. Adjust quality as needed for clarity"
            )
    
    def on_voice_quality_change(self, quality):
        """Change voice quality settings"""
        self.audio_controller.set_voice_quality(quality)
        
        # Save to settings
        self.app.settings["voice_quality"] = quality
        self.app.config_manager.save_settings(self.app.settings)
    
    def show_voice_help(self):
        """Show help instructions for voice mode"""
        messagebox.showinfo(
            "Voice Application Setup Help",
            "To use this player with Discord or other voice apps:\n\n"
            "1. Download & install VB-Cable from the website\n"
            "2. Enable 'Voice App Mode' switch\n"
            "3. Select 'VB-Cable' as your output device in this app\n"
            "4. In Discord, select 'VB-Cable' as your microphone input\n"
            "5. Adjust quality setting based on your needs:\n"
            "   - Low: Better for slow connections\n"
            "   - Medium: Good balance for most users\n"
            "   - High: Best quality, requires good connection"
        )
    
    def get_vb_cable(self):
        """Open the VB-Cable download website"""
        try:
            webbrowser.open("https://vb-audio.com/Cable/")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Couldn't open browser: {str(e)}\n\n"
                "Please visit: https://vb-audio.com/Cable/ to download VB-Cable"
            )
