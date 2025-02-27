import customtkinter as ctk
from pathlib import Path
import time
import threading
from pydub import AudioSegment

class AudioFileWidget(ctk.CTkFrame):
    def __init__(self, parent, file_name, file_path, on_remove, audio_controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.file_name = file_name
        self.file_path = file_path
        self.on_remove = on_remove
        self.audio_controller = audio_controller
        self.is_playing = False
        self.is_selected = False
        self.is_looping = self.audio_controller.is_looping
        self.duration = 0  # Will be set when loaded
        self.setup_ui()
        
        # Load duration in background to prevent UI freezing
        self.load_duration_thread = threading.Thread(target=self.load_duration_info_bg)
        self.load_duration_thread.daemon = True
        self.load_duration_thread.start()
        
    def setup_ui(self):
        # Main file container with a little spacing
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", expand=True, padx=5, pady=2)
        
        # Left side: Play indicator and file name
        left_frame = ctk.CTkFrame(content, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Play indicator - shows when track is active
        self.playing_indicator = ctk.CTkFrame(
            left_frame,
            width=4,
            height=20,
            corner_radius=2,
            fg_color="transparent"  # Initially invisible
        )
        self.playing_indicator.pack(side="left", padx=(0, 6))
        
        # Play button with circular styling
        self.play_btn = ctk.CTkButton(
            left_frame,
            text="▶",
            width=30,
            height=30,
            command=self.toggle_play,
            fg_color="#3a3a5e",
            hover_color="#4a4a6e",
            corner_radius=15  # Make it circular
        )
        self.play_btn.pack(side="left", padx=(0, 8))
        
        # MOVED: Remove button next to play button as requested
        self.remove_btn = ctk.CTkButton(
            left_frame,
            text="✕",
            width=28,
            height=28, 
            corner_radius=14,
            fg_color="#3a3a5e",
            hover_color="#f72585",
            command=lambda: self.on_remove(self.file_name)
        )
        self.remove_btn.pack(side="left", padx=(0, 8))
        
        # File name label
        self.file_label = ctk.CTkLabel(
            left_frame,
            text=self.file_name,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color="#edf2f4"
        )
        self.file_label.pack(side="left", fill="x", expand=True)
        
        # Right side: Controls
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.pack(side="right")
        
        # Duration label
        self.duration_label = ctk.CTkLabel(
            controls,
            text="--:--",
            width=45,
            font=ctk.CTkFont(size=10),
            text_color="#8d99ae"
        )
        self.duration_label.pack(side="left", padx=5)
        
        # Favorite/star button (optional feature)
        self.fav_btn = ctk.CTkButton(
            controls,
            text="★",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="#3a3a5e",
            hover_color="#4a4a6e",
            command=self.toggle_favorite
        )
        self.fav_btn.pack(side="left", padx=2)
        
        # Add hover effect
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        # Try to load duration info
        self.load_duration_info()
    
    def load_duration_info_bg(self):
        """Load duration information in background thread to prevent UI freezing"""
        try:
            # Check if this is a WAV file to use a faster method
            if self.file_path.lower().endswith('.wav'):
                # Use Wave module which is much faster for WAV files
                import wave
                with wave.open(self.file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration_sec = frames / float(rate)
            else:
                # Fallback to pydub for other formats
                audio = AudioSegment.from_file(self.file_path)
                duration_sec = len(audio) / 1000
                
            self.duration = duration_sec
            mins = int(duration_sec // 60)
            secs = int(duration_sec % 60)
            
            # Update the UI in the main thread
            self.after(0, lambda: self.duration_label.configure(text=f"{mins}:{secs:02d}"))
        except Exception as e:
            print(f"Error loading duration for {self.file_name}: {e}")
            self.after(0, lambda: self.duration_label.configure(text="--:--"))
    
    def load_duration_info(self):
        """Placeholder that starts the background loading"""
        # The actual loading happens in the background thread
        # This just sets a waiting indicator
        self.duration_label.configure(text="...")
    
    def toggle_play(self):
        print(f"[DEBUG] Toggle play clicked for {self.file_name}, current state: {self.is_playing}")
        if self.is_playing:
            print(f"[DEBUG] Pausing track: {self.file_name}")
            self.audio_controller.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶")
        else:
            # Stop any other playing tracks first
            prev_widget = self.audio_controller.current_widget
            if prev_widget and prev_widget != self:
                print(f"[DEBUG] Stopping previous track to play: {self.file_name}")
                # FIXED: Safely stop previous track, avoid direct widget calls
                self.audio_controller.stop_previous_widget()
            
            # Start this track
            print(f"[DEBUG] Starting to play track: {self.file_name}")
            try:
                # Ensure we fully stop any previous playback first
                self.audio_controller.stop()
                self.audio_controller.load_audio(self.file_path, self)
                self.audio_controller.play(self.is_looping)
                self.is_playing = True
                self.play_btn.configure(text="⏸")
                print(f"[DEBUG] Track started successfully: {self.file_name}")
            except Exception as e:
                print(f"[ERROR] Failed to play track {self.file_name}: {e}")
        
        # Update widget appearance
        self.update_ui_state()
    
    def stop_playback(self):
        """External call to stop playback"""
        if self.is_playing:
            self.is_playing = False
            self.play_btn.configure(text="▶")
            self.update_ui_state()
    
    def playback_finished(self):
        """Called when playback naturally ends"""
        self.is_playing = False
        self.play_btn.configure(text="▶")
        self.update_ui_state()
        
        # If the main app has registered a callback for this
        if hasattr(self.audio_controller, 'playback_ended_callback') and self.audio_controller.playback_ended_callback:
            self.audio_controller.playback_ended_callback(self)
    
    def update_ui_state(self):
        """Update the UI appearance based on state"""
        if self.is_playing:
            self.configure(fg_color="#252550")  # Highlight active track
            self.playing_indicator.configure(fg_color="#f72585")  # Show indicator with accent color
        else:
            self.configure(fg_color="#252538")  # Default background
            self.playing_indicator.configure(fg_color="transparent")  # Hide indicator
    
    def update_play_button(self, symbol):
        """Update just the play button symbol with safety check"""
        try:
            if self.winfo_exists():  # Check if widget still exists before changing
                self.play_btn.configure(text=symbol)
        except Exception as e:
            print(f"[ERROR] Failed to update play button: {e}")
    
    def update_loop_button(self):
        """Update loop button appearance based on global state"""
        self.is_looping = self.audio_controller.is_looping
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        # This is just a placeholder for a potential feature
        favorited = getattr(self, 'favorited', False)
        self.favorited = not favorited
        self.fav_btn.configure(
            fg_color="#f72585" if self.favorited else "#3a3a5e"
        )
    
    def on_enter(self, event):
        """Mouse enter event - highlight"""
        if not self.is_playing:
            self.configure(fg_color="#303050")
    
    def on_leave(self, event):
        """Mouse leave event - normal color"""
        if not self.is_playing:
            self.configure(fg_color="#252538")
