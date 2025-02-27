import customtkinter as ctk
from pathlib import Path
import numpy as np
from pydub import AudioSegment
import webbrowser
import subprocess
from tkinter import messagebox, filedialog
from audio_file_widget import AudioFileWidget
from ffmpeg_utils import run_ffmpeg_command

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
        """Update the global progress bar and time information with improved visuals"""
        try:
            if self.audio_controller.is_playing:
                position = self.audio_controller.position
                duration = self.audio_controller.duration
                
                if (duration > 0):  # Avoid division by zero
                    self.ui.global_progress.set(position / duration)
                
                # Update time labels with more readable format
                mins_elapsed = int(position // 60)
                secs_elapsed = int(position % 60)
                
                mins_remaining = int((duration - position) // 60)
                secs_remaining = int((duration - position) % 60)
                
                # Set the elapsed and remaining time labels
                self.ui.time_elapsed.configure(text=f"{mins_elapsed}:{secs_elapsed:02d}")
                self.ui.time_remaining.configure(text=f"-{mins_remaining}:{secs_remaining:02d}")
                
                # Update play/pause button state
                self.ui.play_pause_btn.configure(
                    text="⏸" if not self.audio_controller.is_paused else "▶",
                    fg_color=self.theme_manager.get_color("accent_secondary") if not self.audio_controller.is_paused 
                    else self.theme_manager.get_color("accent_primary")
                )
                
                # Update current playing song info
                if self.audio_controller.current_widget:
                    file_name = self.audio_controller.current_widget.file_name
                    self.ui.current_song_label.configure(text=file_name)
                    
                    # Highlight the current playing track in the list
                    self.update_playing_highlight()
            else:
                # Reset time display when nothing is playing
                self.ui.time_elapsed.configure(text="0:00")
                self.ui.time_remaining.configure(text="-0:00")
                self.ui.play_pause_btn.configure(
                    text="▶",
                    fg_color=self.theme_manager.get_color("accent_primary")
                )
            
            # Reschedule the timer
            self.app.callback_timer_id = self.app.window.after(50, self.update_global_progress)
        except Exception as e:
            print(f"Error updating progress: {e}")
            # Reschedule even on error
            self.app.callback_timer_id = self.app.window.after(1000, self.update_global_progress)
    
    def update_playing_highlight(self):
        """Ensure the currently playing track is highlighted in the list"""
        for widget in self.get_file_widgets():
            if widget == self.audio_controller.current_widget:
                widget.configure(fg_color=self.theme_manager.get_color("accent_primary"))
                widget.playing_indicator.configure(fg_color=self.theme_manager.get_color("accent_secondary"))
            else:
                widget.configure(fg_color=self.theme_manager.get_color("bg_secondary"))
                widget.playing_indicator.configure(fg_color="transparent")
    
    def on_search(self, *args):
        """Filter files based on search text"""
        self.update_file_list()
    
    def seek_global(self, position):
        """Global seek function for the progress bar"""
        if self.audio_controller.current_widget:
            self.audio_controller.seek(float(position))
    
    def toggle_global_playback(self):
        """Toggle play/pause for currently active track"""
        if self.audio_controller.is_playing:
            if self.audio_controller.is_paused:
                self.audio_controller.resume()
                self.ui.play_pause_btn.configure(text="⏸")
            else:
                self.audio_controller.pause()
                self.ui.play_pause_btn.configure(text="▶")
        elif self.audio_controller.current_widget:
            # If a track was selected but stopped, restart it
            self.audio_controller.current_widget.toggle_play()
            self.ui.play_pause_btn.configure(text="⏸")
        else:
            # Play first track if nothing is selected
            widgets = self.get_file_widgets()
            if widgets:
                widgets[0].toggle_play()
                self.ui.play_pause_btn.configure(text="⏸")
    
    def stop_global_playback(self):
        """Stop the currently playing track"""
        if self.audio_controller.is_playing:
            self.audio_controller.stop()
            self.ui.play_pause_btn.configure(text="▶")
            self.ui.current_song_label.configure(text="No song playing")
    
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
        print(f"Audio ended, loop state: {self.is_looping}")
        if self.audio_controller.is_looping:
            # If looping is enabled, restart the same track after a small delay
            self.app.window.after(100, lambda: widget.toggle_play())
        else:
            # Auto-play next track
            self.next_track()
    
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
        """Play the next track in the list"""
        widgets = self.get_file_widgets()
        if not widgets:
            return
            
        if self.audio_controller.current_widget in widgets:
            current_index = widgets.index(self.audio_controller.current_widget)
            next_index = (current_index + 1) % len(widgets)
            widgets[next_index].toggle_play()
        else:
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
        """Add a new audio file to the player"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")]
        )
        if file_path:
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
            
            try:
                print("Loading audio file...")
                # Modify AudioSegment to use the wrapper
                AudioSegment.converter = "ffmpeg"
                
                # Fix: Set ffmpeg parameters to suppress console windows
                # Try different methods to load the file
                try:
                    audio = AudioSegment.from_mp3(file_path)
                except:
                    try:
                        audio = AudioSegment.from_file(file_path)
                    except:
                        audio = AudioSegment.from_file(file_path, format="mp3")

                print(f"Audio details:")
                print(f"- Format: {audio.channels} channels")
                print(f"- Sample width: {audio.sample_width} bytes")
                print(f"- Frame rate: {audio.frame_rate} Hz")
                print(f"- Duration: {len(audio)/1000:.2f} seconds")
                
                print("Converting and caching file...")
                audio.export(cache_path, format="wav")
                print("File cached successfully")
                
                self.app.settings["cached_files"][file_name] = cache_path
                self.app.config_manager.save_settings(self.app.settings)
                self.update_file_list()
                print("=== Audio file added successfully ===\n")
                
            except Exception as e:
                error_msg = f"Failed to add audio file: {str(e)}"
                print(f"Error: {error_msg}")
                print(f"Exception type: {type(e).__name__}")
                print(f"Full exception details: {repr(e)}")
                messagebox.showerror(
                    "Error", 
                    "Failed to add audio file. Please ensure ffmpeg is installed.\n"
                    f"Error details: {str(e)}"
                )
    
    def update_file_list(self):
        """Update the list of audio files in the UI"""
        # Clear existing widgets in files_list
        for widget in self.ui.files_list.winfo_children():
            widget.destroy()
        
        self.app.file_widgets = {}
        
        # Filter by search text if provided
        search_text = self.ui.search_var.get().lower()
        
        # Add each file as an AudioFileWidget
        for file_name, file_path in self.app.settings["cached_files"].items():
            # Apply search filter if needed
            if search_text and search_text not in file_name.lower():
                continue
                
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
