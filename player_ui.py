import customtkinter as ctk
from tkinter import messagebox
from tkinter import filedialog
from pathlib import Path
import webbrowser
from audio_file_widget import AudioFileWidget

class PlayerUI:
    def __init__(self, app, window, theme_manager):
        self.app = app
        self.window = window
        self.theme_manager = theme_manager
        self.search_var = ctk.StringVar()
        self.voice_mode_var = ctk.BooleanVar(value=app.audio_controller.voice_mode)
        
        # UI elements that need to be accessed by PlayerController
        self.device_menu = None
        self.files_list = None
        self.play_pause_btn = None
        self.current_song_label = None
        self.global_progress = None
        self.time_elapsed = None
        self.time_remaining = None
        self.volume_slider = None
        self.sidebar_vol_slider = None
        self.loop_btn = None
        self.mute_btn = None
        self.sidebar_mute_btn = None
        self.vol_value_label = None
        self.voice_quality_menu = None
    
    def setup_ui(self):
        # Content container for everything except the player bar
        self.content_container = ctk.CTkFrame(
            self.window,
            fg_color=self.theme_manager.get_color("bg_primary"),
            corner_radius=0
        )
        self.content_container.grid(row=0, column=0, sticky="nsew")
        
        # Create header in content area
        header_frame = self.create_header_panel(self.content_container)
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Main content area
        content_area = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )
        content_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Split into left sidebar and right main panel
        left_panel = ctk.CTkFrame(
            content_area,
            fg_color=self.theme_manager.get_color("bg_secondary"),
            corner_radius=10
        )
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=0, expand=False)
        
        right_panel = ctk.CTkFrame(
            content_area,
            fg_color="transparent"
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Left sidebar - Settings and controls
        self.create_settings_panel(left_panel)
        
        # Right panel - File list and player
        self.create_file_panel(right_panel)
        
        # Create player panel separately, directly in the window's grid
        self.create_player_panel(self.window)
        
        # Controller-dependent initialization is now moved to connect_controller method
    
    def connect_controller(self, controller):
        """Connect the UI to the controller after both have been initialized"""
        # Setup command bindings for the UI components
        self.device_menu.configure(command=controller.on_device_change)
        self.voice_quality_menu.configure(command=controller.on_voice_quality_change)
        
        # Update trace for voice mode variable
        if self.voice_mode_var.trace_info():
            self.voice_mode_var.trace_remove("write", self.voice_mode_var.trace_info()[0][1])
        self.voice_mode_var.trace_add("write", lambda *args: controller.toggle_voice_mode())
        
        # Update trace for search variable - be careful about trace_info returning empty list
        if self.search_var.trace_info():
            self.search_var.trace_remove("write", self.search_var.trace_info()[0][1])
        self.search_var.trace_add("write", controller.on_search)
        
        # Configure button commands
        self.prev_btn.configure(command=controller.previous_track)
        self.play_pause_btn.configure(command=controller.toggle_global_playback)
        self.stop_btn.configure(command=controller.stop_global_playback)
        self.next_btn.configure(command=controller.next_track)
        self.loop_btn.configure(command=controller.toggle_global_loop)
        self.mute_btn.configure(command=controller.toggle_global_mute)
        self.sidebar_mute_btn.configure(command=controller.toggle_global_mute_with_label)
        
        # Configure slider commands
        self.global_progress.configure(command=controller.seek_global)
        self.volume_slider.configure(command=controller.set_global_volume)
        self.sidebar_vol_slider.configure(command=controller.set_global_volume_with_label)
        
        # Initialize the devices and file list
        controller.refresh_devices()
        controller.update_file_list()
    
    def create_header_panel(self, parent):
        """Create an attractive header panel with logo and app name"""
        header = ctk.CTkFrame(
            parent,
            fg_color=self.theme_manager.get_color("bg_tertiary"),
            corner_radius=10,
            height=60
        )
        
        # Make the header a fixed height
        header.pack_propagate(False)
        
        # Logo placeholder/icon
        logo_frame = ctk.CTkFrame(
            header,
            fg_color=self.theme_manager.get_color("accent_primary"),
            corner_radius=10,
            width=40,
            height=40
        )
        logo_frame.pack(side="left", padx=15)
        
        # Prevent logo from resizing
        logo_frame.pack_propagate(False)
        
        # Music icon in logo
        ctk.CTkLabel(
            logo_frame,
            text="♫",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # App title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=10, fill="y")
        
        ctk.CTkLabel(
            title_frame,
            text="AUDIO TO MIC",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.theme_manager.get_color("text_primary")
        ).pack(anchor="sw")
        
        ctk.CTkLabel(
            title_frame,
            text="PROFESSIONAL PLAYER",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(anchor="sw")
        
        # Theme selector on right side of header
        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.pack(side="right", padx=15)
        
        ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(side="left", padx=(0, 5))
        
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=self.theme_manager.get_all_themes(),
            command=self.app.change_theme,
            width=120,
            **self.get_dropdown_style()
        )
        theme_menu.pack(side="left")
        theme_menu.set(self.theme_manager.current_theme_name)
        
        return header
        
    def create_settings_panel(self, parent):
        """Create a settings sidebar panel"""
        # Device selection section
        device_section = ctk.CTkFrame(parent, fg_color="transparent")
        device_section.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(
            device_section,
            text="OUTPUT DEVICE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(anchor="w", pady=(0, 5))
        
        self.device_menu = ctk.CTkOptionMenu(
            device_section,
            values=[],
            **self.get_dropdown_style()
        )
        self.device_menu.pack(fill="x", padx=0, pady=(0, 5))
        
        refresh_btn = ctk.CTkButton(
            device_section,
            text="Refresh Devices",
            command=lambda: self.app.player_controller.refresh_devices() if hasattr(self.app, 'player_controller') else None,
            **self.get_button_style(),
            image=self.load_image("refresh_icon", "🔄")
        )
        refresh_btn.pack(fill="x", padx=0, pady=(5, 0))
        
        # Separator
        self.create_separator(parent)
        
        # Voice mode settings
        voice_section = ctk.CTkFrame(parent, fg_color="transparent")
        voice_section.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(
            voice_section,
            text="VOICE APP MODE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(anchor="w", pady=(0, 10))
        
        # Voice app toggle with improved styling
        voice_switch_frame = ctk.CTkFrame(voice_section, fg_color="transparent")
        voice_switch_frame.pack(fill="x", pady=5)
        
        voice_switch = ctk.CTkSwitch(
            voice_switch_frame,
            text="Enable Voice Mode",
            variable=self.voice_mode_var,
            onvalue=True,
            offvalue=False,
            progress_color=self.theme_manager.get_color("accent_primary"),
            button_color=self.theme_manager.get_color("accent_secondary"),
            button_hover_color=self.theme_manager.get_color("button_hover")
        )
        voice_switch.pack(side="left")
        
        # Quality setting with label
        quality_frame = ctk.CTkFrame(voice_section, fg_color="transparent")
        quality_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            quality_frame,
            text="Quality:",
            text_color=self.theme_manager.get_color("text_primary")
        ).pack(side="left")
        
        self.voice_quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=["low", "medium", "high"],
            **self.get_dropdown_style()
        )
        self.voice_quality_menu.set(self.app.audio_controller.voice_quality)
        self.voice_quality_menu.pack(side="right")
        
        # Voice app help & download buttons
        help_btn = ctk.CTkButton(
            voice_section,
            text="How to Use",
            command=lambda: self.app.player_controller.show_voice_help() if hasattr(self.app, 'player_controller') else None,
            **self.get_button_style()
        )
        help_btn.pack(fill="x", padx=0, pady=(5, 5))
        
        cable_btn = ctk.CTkButton(
            voice_section,
            text="Download VB-Cable",
            command=lambda: self.app.player_controller.get_vb_cable() if hasattr(self.app, 'player_controller') else None,
            **self.get_button_style()
        )
        cable_btn.pack(fill="x", padx=0, pady=(0, 5))
        
        # Separator
        self.create_separator(parent)
        
        # Volume control section
        volume_section = ctk.CTkFrame(parent, fg_color="transparent")
        volume_section.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(
            volume_section,
            text="VOLUME CONTROL",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(anchor="w", pady=(0, 10))
        
        # Volume slider with value display
        vol_slider_frame = ctk.CTkFrame(volume_section, fg_color="transparent")
        vol_slider_frame.pack(fill="x", pady=5)
        
        self.vol_value_label = ctk.CTkLabel(
            vol_slider_frame,
            text=f"{int(self.app.audio_controller.volume * 100)}%",
            width=40,
            text_color=self.theme_manager.get_color("text_primary")
        )
        self.vol_value_label.pack(side="right")
        
        # Fix the slider command to use lambda with existence check
        self.sidebar_vol_slider = ctk.CTkSlider(
            vol_slider_frame,
            from_=0,
            to=1,
            command=lambda value: self.app.player_controller.set_global_volume_with_label(value) if hasattr(self.app, 'player_controller') else None,
            **self.get_slider_style()
        )
        self.sidebar_vol_slider.set(self.app.audio_controller.volume)
        self.sidebar_vol_slider.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Mute button
        # Fix the mute button command similarly
        self.sidebar_mute_btn = ctk.CTkButton(
            volume_section,
            text="Mute" if self.app.audio_controller.muted else "Unmute",
            command=lambda: self.app.player_controller.toggle_global_mute_with_label() if hasattr(self.app, 'player_controller') else None,
            **self.get_button_style()
        )
        self.sidebar_mute_btn.pack(fill="x", padx=0, pady=(5, 0))
    
    def create_file_panel(self, parent):
        """Create file list panel with search and controls"""
        # Top controls area
        controls_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.theme_manager.get_color("bg_secondary"),
            corner_radius=10,
            height=50
        )
        controls_frame.pack(fill="x", padx=0, pady=(0, 10))
        controls_frame.pack_propagate(False)  # Don't resize the frame
        
        # Add file button with icon
        add_btn = ctk.CTkButton(
            controls_frame,
            text="Add Audio",
            command=lambda: self.app.player_controller.add_audio_file() if hasattr(self.app, 'player_controller') else None,
            **self.get_button_style(),
            image=self.load_image("add_icon", "➕"),
            width=120
        )
        add_btn.pack(side="left", padx=15, pady=10)
        
        # Search box on the right
        search_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        search_frame.pack(side="right", padx=15, pady=10, fill="y")
        
        # Search icon and label
        ctk.CTkLabel(
            search_frame,
            text="Search:",
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(side="left", padx=(0, 5))
        
        # Search entry with styling
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type to search...",
            textvariable=self.search_var,
            width=200,
            height=28,
            border_color=self.theme_manager.get_color("accent_primary"),
            fg_color=self.theme_manager.get_color("bg_tertiary")
        )
        search_entry.pack(side="left")
        
        # Files list with header
        files_container = ctk.CTkFrame(parent, fg_color="transparent")
        files_container.pack(fill="both", expand=True)
        
        # Files header with column labels
        files_header = ctk.CTkFrame(
            files_container,
            fg_color=self.theme_manager.get_color("bg_tertiary"),
            corner_radius=5,
            height=30
        )
        files_header.pack(fill="x", pady=(0, 5))
        files_header.pack_propagate(False)  # Keep fixed height
        
        # Column headers with appropriate widths
        ctk.CTkLabel(
            files_header,
            text="TRACK NAME",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(side="left", padx=50)
        
        ctk.CTkLabel(
            files_header,
            text="DURATION",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).pack(side="right", padx=(0, 110))
        
        # Files list with improved styling
        self.files_list = ctk.CTkScrollableFrame(
            files_container,
            fg_color=self.theme_manager.get_color("bg_secondary"),
            corner_radius=10
        )
        self.files_list.pack(fill="both", expand=True)
    
    def create_player_panel(self, parent):
        """Create an enhanced player control panel with large progress bar fixed at the bottom"""
        # Create a visually distinct player panel using grid for better anchoring
        self.global_player = ctk.CTkFrame(
            parent,
            fg_color=self.theme_manager.get_color("bg_tertiary"),
            corner_radius=0,  # No rounded corners for bottom bar
            height=100  # Fixed height
        )
        self.global_player.grid(row=1, column=0, sticky="ew")
        self.global_player.grid_propagate(False)  # Prevent resizing
        
        # Add a noticeable top border for visual separation
        top_border = ctk.CTkFrame(
            self.global_player,
            fg_color=self.theme_manager.get_color("accent_primary"),
            height=3  # Make it slightly thicker for visibility
        )
        top_border.pack(fill="x")
        
        # Top section: song info and progress bar
        top_section = ctk.CTkFrame(self.global_player, fg_color="transparent")
        top_section.pack(fill="x", padx=15, pady=(10, 5))
        
        # Current song info with better styling
        song_info = ctk.CTkFrame(top_section, fg_color="transparent")
        song_info.pack(fill="x")
        
        # Now playing label
        now_playing = ctk.CTkLabel(
            song_info,
            text="NOW PLAYING",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        now_playing.pack(anchor="w")
        
        # Song title with scroll effect if needed
        self.current_song_label = ctk.CTkLabel(
            song_info,
            text="No song playing",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.theme_manager.get_color("accent_primary")
        )
        self.current_song_label.pack(anchor="w")
        
        # Progress section with more pronounced design
        progress_section = ctk.CTkFrame(self.global_player, fg_color="transparent")
        progress_section.pack(fill="x", padx=15, pady=5)
        
        # Large, prominent progress bar
        progress_container = ctk.CTkFrame(progress_section, fg_color="transparent")
        progress_container.pack(fill="x", pady=5)
        
        # Time labels
        self.time_elapsed = ctk.CTkLabel(
            progress_container,
            text="0:00",
            width=35,
            text_color=self.theme_manager.get_color("accent_primary")
        )
        self.time_elapsed.pack(side="left", padx=(0, 5))
        
        # Progress container with background - make it stand out more
        progress_bg = ctk.CTkFrame(
            progress_container,
            fg_color=self.theme_manager.get_color("bg_primary"),
            corner_radius=8,
            border_width=1,
            border_color=self.theme_manager.get_color("accent_primary")
        )
        progress_bg.pack(side="left", fill="x", expand=True)
        
        # Actual slider on top of background
        self.global_progress = ctk.CTkSlider(
            progress_bg,
            from_=0,
            to=1,
            command=lambda value: self.app.player_controller.seek_global(value) if hasattr(self.app, 'player_controller') else None,
            height=20,
            button_length=20,
            progress_color=self.theme_manager.get_color("accent_primary"),
            button_color=self.theme_manager.get_color("accent_secondary"),
            button_hover_color=self.theme_manager.get_color("accent_secondary"),
            corner_radius=8
        )
        self.global_progress.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Remaining time
        self.time_remaining = ctk.CTkLabel(
            progress_container,
            text="-0:00",
            width=40,
            text_color=self.theme_manager.get_color("accent_primary")
        )
        self.time_remaining.pack(side="left", padx=(5, 0))
        
        # Button controls section
        controls_section = ctk.CTkFrame(self.global_player, fg_color="transparent")
        controls_section.pack(fill="x", padx=15, pady=(5, 10))
        
        # Center-aligned playback controls
        playback_frame = ctk.CTkFrame(controls_section, fg_color="transparent")
        playback_frame.pack(side="left")
        
        # Previous track button
        self.prev_btn = ctk.CTkButton(
            playback_frame,
            text="⏮",
            width=40,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.previous_track() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("button_bg"),
            hover_color=self.theme_manager.get_color("button_hover"),
        )
        self.prev_btn.pack(side="left", padx=5)
        
        # Play/Pause button - larger and more prominent
        self.play_pause_btn = ctk.CTkButton(
            playback_frame,
            text="▶",
            width=50,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.toggle_global_playback() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("accent_primary"),
            hover_color=self.theme_manager.get_color("accent_secondary"),
            text_color="#FFFFFF"
        )
        self.play_pause_btn.pack(side="left", padx=5)
        
        # Stop button - fixed formatting
        self.stop_btn = ctk.CTkButton(
            playback_frame,
            text="⏹",
            width=40,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.stop_global_playback() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("button_bg"),
            hover_color=self.theme_manager.get_color("button_hover"),
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Next track button - fixed formatting
        self.next_btn = ctk.CTkButton(
            playback_frame,
            text="⏭",
            width=40,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.next_track() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("button_bg"),
            hover_color=self.theme_manager.get_color("button_hover"),
        )
        self.next_btn.pack(side="left", padx=5)
        
        # Right controls group
        right_controls = ctk.CTkFrame(controls_section, fg_color="transparent")
        right_controls.pack(side="right")
        
        # Loop toggle button - fixed formatting
        self.loop_btn = ctk.CTkButton(
            right_controls,
            text="🔁",
            width=40,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.toggle_global_loop() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("button_bg"),
            hover_color=self.theme_manager.get_color("button_hover"),
        )
        self.loop_btn.pack(side="left", padx=5)
        
        # Fix for line 557 error - removed text fragment
        self.mute_btn = ctk.CTkButton(
            right_controls,
            text="🔊",
            width=40,
            height=30,
            corner_radius=15,
            command=lambda: self.app.player_controller.toggle_global_mute() if hasattr(self.app, 'player_controller') else None,
            fg_color=self.theme_manager.get_color("button_bg"),
            hover_color=self.theme_manager.get_color("button_hover"),
        )
        self.mute_btn.pack(side="left", padx=5)
        
        # Volume slider - fixed formatting
        volume_frame = ctk.CTkFrame(right_controls, fg_color="transparent", height=30)
        volume_frame.pack(side="left", padx=5, fill="y")
        
        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=1,
            command=lambda value: self.app.player_controller.set_global_volume(value) if hasattr(self.app, 'player_controller') else None,
            width=100,
            **self.get_slider_style()
        )
        self.volume_slider.set(self.app.audio_controller.volume)
        self.volume_slider.pack(side="left", expand=True, fill="both")
    
    def create_separator(self, parent):
        """Create a visual separator"""
        separator = ctk.CTkFrame(
            parent, 
            fg_color=self.theme_manager.get_color("bg_tertiary"),
            height=1
        )
        separator.pack(fill="x", padx=10, pady=5)
    
    def load_image(self, name, fallback_text=""):
        """Utility function to load icon images with fallback text"""
        # This would normally load an image, but we'll just return None
        # so CustomTkinter uses the fallback text
        return None
    
    def get_button_style(self):
        """Get common button style from theme"""
        return {
            "fg_color": self.theme_manager.get_color("button_bg"),
            "hover_color": self.theme_manager.get_color("button_hover"),
            "text_color": self.theme_manager.get_color("text_primary"),
            "height": 28,
            "corner_radius": 6
        }
    
    def get_dropdown_style(self):
        """Get common dropdown style from theme"""
        return {
            "fg_color": self.theme_manager.get_color("bg_tertiary"),
            "button_color": self.theme_manager.get_color("button_bg"),
            "button_hover_color": self.theme_manager.get_color("button_hover"),
            "text_color": self.theme_manager.get_color("text_primary"),
            "dropdown_fg_color": self.theme_manager.get_color("bg_tertiary"),
            "dropdown_hover_color": self.theme_manager.get_color("button_hover"),
            "dropdown_text_color": self.theme_manager.get_color("text_primary")
        }
    
    def get_slider_style(self):
        """Get common slider style from theme"""
        return {
            "progress_color": self.theme_manager.get_color("accent_primary"),
            "button_color": self.theme_manager.get_color("accent_secondary"),
            "button_hover_color": self.theme_manager.get_color("accent_secondary")
        }