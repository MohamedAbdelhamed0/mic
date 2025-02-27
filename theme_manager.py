class ThemeManager:
    """Manages app themes and colors for consistent styling"""
    
    # Color schemes
    THEMES = {
        "dark_blue": {
            "bg_primary": "#1a1a2e",
            "bg_secondary": "#252538",
            "bg_tertiary": "#1e1e30",
            "accent_primary": "#4cc9f0",
            "accent_secondary": "#f72585",
            "button_bg": "#3a3a5e",
            "button_hover": "#4a4a6e",
            "text_primary": "#edf2f4",
            "text_secondary": "#8d99ae"
        },
        "dark_purple": {
            "bg_primary": "#240046",
            "bg_secondary": "#3c096c",
            "bg_tertiary": "#2d0049",
            "accent_primary": "#7b2cbf",
            "accent_secondary": "#ff9e00",
            "button_bg": "#5a189a",
            "button_hover": "#7b2cbf",
            "text_primary": "#edf2f4",
            "text_secondary": "#c8b6ff"
        },
        "dark_green": {
            "bg_primary": "#1a281f",
            "bg_secondary": "#2a403a",
            "bg_tertiary": "#1f3329",
            "accent_primary": "#2d6a4f",
            "accent_secondary": "#d8f3dc",
            "button_bg": "#40916c",
            "button_hover": "#52b788",
            "text_primary": "#edf2f4",
            "text_secondary": "#b7e4c7"
        }
    }
    
    def __init__(self):
        self.current_theme_name = "dark_blue"  # Default theme
        self.current_theme = self.THEMES[self.current_theme_name]
    
    def get_color(self, color_key):
        """Get a color from the current theme"""
        return self.current_theme.get(color_key, "#ffffff")  # White as fallback
    
    def set_theme(self, theme_name):
        """Change the current theme"""
        if theme_name in self.THEMES:
            self.current_theme_name = theme_name
            self.current_theme = self.THEMES[theme_name]
            return True
        return False
        
    def get_button_style(self):
        """Get standard button styling"""
        return {
            "fg_color": self.get_color("button_bg"),
            "hover_color": self.get_color("button_hover"),
            "text_color": self.get_color("text_primary")
        }
        
    def get_slider_style(self):
        """Get standard slider styling"""
        return {
            "progress_color": self.get_color("accent_primary"),
            "button_color": self.get_color("accent_secondary"),
            "button_hover_color": self.get_color("button_hover")
        }
        
    def get_all_themes(self):
        """Get list of all available themes"""
        return list(self.THEMES.keys())
