import sys
import os

def configure_path():
    """
    Configure Python path to ensure all modules are loadable
    regardless of how the script is launched
    """
    # Get directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add to Python path if not already there
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

if __name__ == "__main__":
    # Ensure imports work properly
    configure_path()
    
    # Import and run the audio player app
    try:
        from audio_player import AudioMicPlayer
        app = AudioMicPlayer()
        app.run()
    except Exception as e:
        import traceback
        print(f"Error starting application: {e}")
        traceback.print_exc()
        
        # Keep console open on error if running as executable
        if getattr(sys, 'frozen', False):
            input("\nPress Enter to exit...")
