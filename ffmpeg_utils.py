import subprocess
import os
import sys
import platform
import threading
from pydub import AudioSegment

def run_ffmpeg_command(command, **kwargs):
    """
    Run ffmpeg commands without showing console windows.
    
    Args:
        command: List of command arguments
        **kwargs: Additional kwargs for subprocess.run
    
    Returns:
        CompletedProcess instance
    """
    startupinfo = None
    
    # Hide console window on Windows
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    
    # Ensure stderr is redirected to prevent console windows
    if 'stderr' not in kwargs:
        kwargs['stderr'] = subprocess.PIPE
        
    # For all platforms, ensure we don't create new console windows
    if platform.system() == 'Windows':
        kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW

    return subprocess.run(command, startupinfo=startupinfo, **kwargs)

def apply_ffmpeg_patches():
    """Apply all necessary patches to suppress ffmpeg console windows"""
    # Patch AudioSegment to use our hidden ffmpeg process
    original_converter = AudioSegment.converter
    
    # Save the original subprocess.run function
    original_run = subprocess.run
    
    # Create a patched version of subprocess.run
    def patched_run(cmd, *args, **kwargs):
        # If this is an ffmpeg command, use our hidden window version
        if isinstance(cmd, list) and any('ffmpeg' in str(x).lower() for x in cmd):
            return run_ffmpeg_command(cmd, *args, **kwargs)
        # Otherwise use the original run function
        return original_run(cmd, *args, **kwargs)
    
    # Apply the patch
    subprocess.run = patched_run
    
    # Also patch Popen for additional coverage
    original_popen = subprocess.Popen
    
    def patched_popen(cmd, *args, **kwargs):
        if isinstance(cmd, list) and any('ffmpeg' in str(x).lower() for x in cmd):
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                kwargs['startupinfo'] = startupinfo
                
                # Add creationflags if not present
                if 'creationflags' not in kwargs:
                    kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW
            
            # Redirect output
            if 'stderr' not in kwargs:
                kwargs['stderr'] = subprocess.PIPE
            if 'stdout' not in kwargs:
                kwargs['stdout'] = subprocess.PIPE
                
        return original_popen(cmd, *args, **kwargs)
    
    # Apply the Popen patch
    subprocess.Popen = patched_popen

def process_audio_in_thread(input_path, output_path, format="wav", callback=None):
    """
    Process audio file conversion in a background thread to prevent UI freezing.
    
    Args:
        input_path: Path to source audio file
        output_path: Path where converted file will be saved
        format: Output audio format
        callback: Function to call when conversion completes
    """
    def conversion_thread():
        try:
            # Load audio with hidden ffmpeg process
            audio = AudioSegment.from_file(input_path)
            
            # Optimize: convert to mono for better performance
            if audio.channels > 1:
                audio = audio.set_channels(1)
                
            # Export with optimized settings
            audio.export(
                output_path, 
                format=format,
                parameters=["-q:a", "0"]  # Use high quality, fast encoding
            )
            
            if callback:
                callback(True, None)
        except Exception as e:
            if callback:
                callback(False, str(e))
    
    # Run in thread
    thread = threading.Thread(target=conversion_thread)
    thread.daemon = True
    thread.start()
    return thread
