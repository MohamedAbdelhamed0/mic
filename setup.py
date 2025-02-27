import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        "sounddevice",
        "numpy",
        "pydub",
        "ffmpeg-python",
        "customtkinter",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, 
                "-m", "pip", 
                "install", 
                package
            ])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return False
    
    return True

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print("FFmpeg is installed and working")
            return True
    except:
        pass
    
    print("FFmpeg is not installed or not in PATH")
    return False

def setup_app():
    """Set up the application for first use"""
    print("Setting up Audio Mic Player...")
    
    # Check requirements
    missing_packages = check_requirements()
    if missing_packages:
        print("Missing required packages:", ", ".join(missing_packages))
        success = install_packages(missing_packages)
        if not success:
            print("Failed to install some packages. Please install them manually.")
            return False
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("\nFFmpeg is required for this application.")
        print("Please install FFmpeg and make sure it's in your PATH.")
        print("Download from: https://ffmpeg.org/download.html")
    
    # Create necessary directories
    Path("config").mkdir(exist_ok=True)
    Path("cache").mkdir(exist_ok=True)
    
    print("\nSetup complete! You can now run the application.")
    return True

if __name__ == "__main__":
    setup_app()
    input("\nPress Enter to exit...")
