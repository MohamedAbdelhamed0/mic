import customtkinter as ctk
from pathlib import Path
import time
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
        
        # Remove button
        self.remove_btn = ctk.CTkButton(
            controls,
            text="✕",
            width=28,
            height=28, 
            corner_radius=14,
            fg_color="#3a3a5e",
            hover_color="#f72585",
            command=lambda: self.on_remove(self.file_name)
        )
        self.remove_btn.pack(side="left", padx=2)
        
        # Add hover effect
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        # Try to load duration info
        self.load_duration_info()
    
    def load_duration_info(self):
        """Load duration information for display"""
        try:
            # Load audio just to get duration
            audio = AudioSegment.from_file(self.file_path)
            duration_sec = len(audio) / 1000
            self.duration = duration_sec
            mins = int(duration_sec // 60)
            secs = int(duration_sec % 60)
            self.duration_label.configure(text=f"{mins}:{secs:02d}")
        except Exception:
            self.duration_label.configure(text="--:--")
    
    def toggle_play(self):
        if self.is_playing:
            self.audio_controller.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶")
        else:
            # Stop any other playing tracks first
            if self.audio_controller.current_widget and self.audio_controller.current_widget != self:
                self.audio_controller.current_widget.update_play_button("▶")
                self.audio_controller.current_widget.is_playing = False
            
            # Start this track
            self.audio_controller.load_audio(self.file_path, self)
            self.audio_controller.play(self.is_looping)
            self.is_playing = True
            self.play_btn.configure(text="⏸")
        
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
        """Update just the play button symbol"""
        self.play_btn.configure(text=symbol)
    
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
