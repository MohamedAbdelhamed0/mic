import PyInstaller.__main__
import shutil
from pathlib import Path
import os

def build_app():
    # Create dist and build directories if they don't exist
    Path("dist").mkdir(exist_ok=True)
    Path("build").mkdir(exist_ok=True)

    # Base PyInstaller options
    pyinstaller_args = [
        'main.py',  # Main script entry point
        '--name=AudioMicPlayer',
        '--onefile',  # Create single executable
        '--noconsole',  # Don't show console window
        '--clean',  # Clean cache before building
        # Add required imports
        '--hidden-import=pydub.utils',
        '--hidden-import=customtkinter',
        '--hidden-import=ffmpeg_utils',
        # Include additional data files
        '--add-data=config;config',
    ]

    # Add icon if it exists
    icon_path = Path("icon.ico")
    if (icon_path.exists()):
        pyinstaller_args.extend([
            f'--add-data={icon_path};.',
            f'--icon={icon_path}'
        ])

    # Run PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

    # Create release folder
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # Copy executable to release folder
    shutil.copy2(
        "dist/AudioMicPlayer.exe",
        release_dir / "AudioMicPlayer.exe"
    )

    # Copy readme if exists
    if Path("README.md").exists():
        shutil.copy2("README.md", release_dir / "README.md")

    print("Build completed! Release files are in the 'release' folder.")

if __name__ == "__main__":
    build_app()
