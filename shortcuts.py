class KeyboardShortcuts:
    def __init__(self, app):
        self.app = app
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""
        window = self.app.window
        
        # Space = Play/Pause
        window.bind("<space>", lambda e: self.app.toggle_global_playback())
        
        # Left/right arrow keys = Seek backward/forward
        window.bind("<Left>", lambda e: self.seek_backward())
        window.bind("<Right>", lambda e: self.seek_forward())
        
        # Up/down arrow keys = Volume up/down
        window.bind("<Up>", lambda e: self.volume_up())
        window.bind("<Down>", lambda e: self.volume_down())
        
        # M = Toggle mute
        window.bind("m", lambda e: self.app.toggle_global_mute())
        
        # L = Toggle loop
        window.bind("l", lambda e: self.app.toggle_global_loop())
        
        # Media keys (may not work on all systems)
        window.bind("<XF86AudioPlay>", lambda e: self.app.toggle_global_playback())
        window.bind("<XF86AudioStop>", lambda e: self.app.stop_global_playback())
        window.bind("<XF86AudioPrev>", lambda e: self.app.previous_track())
        window.bind("<XF86AudioNext>", lambda e: self.app.next_track())
        
    def seek_backward(self):
        """Seek 5 seconds backward"""
        if self.app.audio_controller.is_playing:
            current = self.app.audio_controller.position
            self.app.audio_controller.seek(max(0, current - 5))
            
    def seek_forward(self):
        """Seek 5 seconds forward"""
        if self.app.audio_controller.is_playing:
            current = self.app.audio_controller.position
            self.app.audio_controller.seek(min(self.app.audio_controller.duration, current + 5))
            
    def volume_up(self):
        """Increase volume by 5%"""
        current = self.app.audio_controller.volume
        self.app.audio_controller.set_volume(min(1.0, current + 0.05))
        self.app.volume_slider.set(self.app.audio_controller.volume)
        
    def volume_down(self):
        """Decrease volume by 5%"""
        current = self.app.audio_controller.volume
        self.app.audio_controller.set_volume(max(0, current - 0.05))
        self.app.volume_slider.set(self.app.audio_controller.volume)
