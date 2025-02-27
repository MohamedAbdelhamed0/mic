import subprocess
import os
import sys
import platform

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
        
    # For frozen executables, ensure we don't use console
    if getattr(sys, 'frozen', False):
        kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW

    return subprocess.run(command, startupinfo=startupinfo, **kwargs)
