import PyInstaller.__main__
import shutil
from pathlib import Path
import os
import sys
import subprocess

def build_app():
    print("Starting build process for Audio Mic Player...")
    
    # Create dist and build directories if they don't exist
    Path("dist").mkdir(exist_ok=True)
    Path("build").mkdir(exist_ok=True)

    # Base PyInstaller options
    pyinstaller_args = [
        'main.py',                     # Main script entry point
        '--name=AudioMicPlayer',       # Name of the final executable
        '--onefile',                   # Create single executable
        '--noconsole',                 # Don't show console window
        '--clean',                     # Clean cache before building
        
        # Add required imports that PyInstaller might miss
        '--hidden-import=pydub.utils',
        '--hidden-import=customtkinter',
        '--hidden-import=ffmpeg_utils',
        '--hidden-import=wave',        # For faster WAV file loading
        '--hidden-import=PIL._tkinter_finder',  # Fix potential PIL issues
        '--hidden-import=numpy.random.common',  # Fix potential numpy issues
        '--hidden-import=numpy.random.bounded_integers',
        '--hidden-import=numpy.random.entropy',
        
        # Include additional data files
        '--add-data=config;config',
        
        # Optimization
        '--upx-dir=upx',  # If UPX is installed
    ]

    # Add icon if it exists
    icon_path = Path("icon.ico")
    if icon_path.exists():
        pyinstaller_args.extend([
            f'--add-data={icon_path};.',
            f'--icon={icon_path}'
        ])
    else:
        print("Warning: No icon.ico found - app will use default icon")

    # Run PyInstaller with progress feedback
    print("Running PyInstaller to create executable...")
    PyInstaller.__main__.run(pyinstaller_args)
    print("PyInstaller process completed.")

    # Create release folder structure
    print("Creating release folder structure...")
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    # Create required directories in release folder
    (release_dir / "cache").mkdir(exist_ok=True)
    (release_dir / "config").mkdir(exist_ok=True)
    (release_dir / "logs").mkdir(exist_ok=True)
    
    # Copy executable to release folder
    print("Copying executable to release folder...")
    if os.path.exists("dist/AudioMicPlayer.exe"):
        shutil.copy2(
            "dist/AudioMicPlayer.exe",
            release_dir / "AudioMicPlayer.exe"
        )
        print("Executable copied successfully!")
    else:
        print("ERROR: Executable not found! Build may have failed.")
        return False
    
    # Create ffmpeg folder and copy binaries if available
    ffmpeg_release_dir = release_dir / "ffmpeg" / "bin"
    ffmpeg_release_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to find and copy ffmpeg executables
    print("Searching for and copying FFmpeg...")
    ffmpeg_paths = [
        r"C:\ffmpeg\bin",
        r"C:\ffmpeg-7.1-essentials_build\ffmpeg-7.1-essentials_build\bin",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs\\ffmpeg\\bin'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'ffmpeg\\bin'),
    ]
    
    ffmpeg_copied = False
    for path in ffmpeg_paths:
        if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
            print(f"Found FFmpeg in {path}")
            try:
                for exe in ['ffmpeg.exe', 'ffprobe.exe']:
                    if os.path.exists(os.path.join(path, exe)):
                        print(f"Copying {exe}...")
                        shutil.copy2(
                            os.path.join(path, exe),
                            ffmpeg_release_dir / exe
                        )
                ffmpeg_copied = True
                print("FFmpeg binaries copied successfully!")
                break
            except Exception as e:
                print(f"Error copying FFmpeg: {e}")
    
    if not ffmpeg_copied:
        print("WARNING: Could not find FFmpeg binaries to include in the release.")
        print("The application may not work properly without FFmpeg.")
        print("Users will need to install FFmpeg separately.")

    # Copy default settings file if exists
    if os.path.exists("config/settings.json"):
        print("Copying default settings...")
        shutil.copy2("config/settings.json", release_dir / "config" / "settings.json")
    else:
        # Create minimal default settings file
        print("Creating default settings file...")
        import json
        default_settings = {
            "last_device": None,
            "cached_files": {},
            "voice_mode": False,
            "voice_quality": "medium",
            "theme": "dark_blue",
            "favorites": []
        }
        with open(release_dir / "config" / "settings.json", 'w') as f:
            json.dump(default_settings, f, indent=2)

    # Create README file if not exists
    readme_path = release_dir / "README.txt"
    if not os.path.exists(readme_path):
        print("Creating README file...")
        with open(readme_path, 'w') as f:
            f.write("Audio Mic Player\n")
            f.write("==============\n\n")
            f.write("This application allows you to play audio files through your microphone.\n")
            f.write("Perfect for sharing music in Discord, Zoom, or other voice chat applications.\n\n")
            f.write("Setup Instructions:\n")
            f.write("1. Install VB-Cable from https://vb-audio.com/Cable/\n")
            f.write("2. Enable Voice App Mode in settings\n")
            f.write("3. Select VB-Cable as your output device\n")
            f.write("4. In your voice app, select VB-Cable as your microphone\n\n")
            f.write("Troubleshooting:\n")
            f.write("- Make sure FFmpeg is installed or included in the ffmpeg/bin folder\n")
            f.write("- Check the logs folder for error messages if something isn't working\n\n")
            f.write("Enjoy!\n")
    
    # Create a batch launcher file to handle potential dependency issues
    launcher_path = release_dir / "Start AudioMicPlayer.bat"
    with open(launcher_path, 'w') as f:
        f.write('@echo off\n')
        f.write('echo Starting Audio Mic Player...\n')
        f.write('set PATH=%PATH%;%~dp0ffmpeg\\bin\n')  # Add ffmpeg to PATH
        f.write('start "" "%~dp0AudioMicPlayer.exe"\n')
        f.write('exit\n')
    
    # Create version info file
    with open(release_dir / "version.txt", 'w') as f:
        from datetime import datetime
        f.write(f"Audio Mic Player\n")
        f.write(f"Version: 1.0.0\n")
        f.write(f"Build date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("\nBuild completed successfully!")
    print(f"Release files are in the '{release_dir}' folder")
    print("\nThe release includes:")
    print("- AudioMicPlayer.exe (main executable)")
    print("- Start AudioMicPlayer.bat (launcher batch file)")
    print("- FFmpeg binaries (in ffmpeg/bin folder)")
    print("- Default config (in config folder)")
    print("- Cache folder for storing processed audio")
    print("- Logs folder for diagnostic information")
    print("- README.txt with setup instructions")
    print("- version.txt with build information")
    
    return True

if __name__ == "__main__":
    try:
        build_app()
    except Exception as e:
        print(f"Error during build process: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
