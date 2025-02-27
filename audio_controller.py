import sounddevice as sd
import numpy as np
from pydub import AudioSegment
import threading
import time

class AudioController:
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.current_stream = None
        self.is_playing = False
        self.is_paused = False
        self.is_looping = False
        self.volume = 1.0
        self.position = 0
        self.duration = 0
        self.samples = None
        self.sample_rate = None
        self.play_thread = None
        self.muted = False
        self.last_volume = 1.0
        self.current_device = None
        self.active_file_path = None
        self.current_widget = None
        self.voice_mode = False
        self.voice_quality = "medium"  # low, medium, high
        self.playback_ended_callback = None
        
    def stop_previous_widget(self):
        """Safely stop previous widget without directly calling UI methods"""
        print("[DEBUG] Safely stopping previous widget")
        if self.current_widget:
            try:
                # Check if widget still exists
                if hasattr(self.current_widget, 'winfo_exists') and self.current_widget.winfo_exists():
                    self.current_widget.is_playing = False
                    self.current_widget.update_play_button("▶")
                    self.current_widget.update_ui_state()
                else:
                    print("[DEBUG] Previous widget no longer exists, skipping UI update")
            except Exception as e:
                print(f"[ERROR] Error updating previous widget: {e}")
                # Reset the current widget if it's invalid
                self.current_widget = None

    def load_audio(self, file_path, widget=None):
        print(f"[DEBUG] Loading audio: {file_path}")
        
        # Check if the widget is valid before setting it
        if widget:
            try:
                if hasattr(widget, 'winfo_exists') and not widget.winfo_exists():
                    print("[WARNING] Attempted to load audio with destroyed widget")
                    widget = None
            except Exception:
                widget = None
        
        if self.current_widget and self.current_widget != widget:
            # Safely stop previous playback using the dedicated method
            self.stop_previous_widget()
        
        self.current_widget = widget
        self.active_file_path = file_path
        
        # Check if file exists before loading
        try:
            with open(file_path, 'rb') as f:
                pass
        except Exception as e:
            print(f"[ERROR] File does not exist or can't be opened: {file_path}, Error: {e}")
            return 0
            
        print(f"[DEBUG] Loading audio file from: {file_path}")
        
        try:
            # Load audio with appropriate format for voice applications if needed
            audio = AudioSegment.from_file(file_path)
            
            # When in voice mode, optimize for voice applications
            if self.voice_mode:
                print(f"[DEBUG] Processing for voice mode, quality: {self.voice_quality}")
                # Convert to mono
                if audio.channels > 1:
                    audio = audio.set_channels(1)
                    
                # Set appropriate sample rate for voice applications
                if self.voice_quality == "low":
                    target_rate = 16000
                elif self.voice_quality == "medium":
                    target_rate = 24000
                else:  # high
                    target_rate = 48000
                    
                # Convert sample rate if needed
                if audio.frame_rate != target_rate:
                    audio = audio.set_frame_rate(target_rate)
                    
                # Normalize audio to prevent clipping
                normalized_audio = audio.normalize()
                
                # Apply subtle compression for voice applications
                compressed_audio = self._apply_compression(normalized_audio)
                audio = compressed_audio
            else:
                print("[DEBUG] Processing for standard playback")
                # For regular playback, just ensure it's mono
                if audio.channels > 1:
                    audio = audio.set_channels(1)
            
            print(f"[DEBUG] Audio loaded. Channels: {audio.channels}, Rate: {audio.frame_rate}, Duration: {len(audio)/1000:.2f}s")
            
            self.samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            self.samples = self.samples / np.iinfo(audio.array_type).max
            self.sample_rate = audio.frame_rate
            self.duration = len(self.samples) / self.sample_rate
            self.position = 0
            return self.duration
        except Exception as e:
            print(f"[ERROR] Failed to load audio: {e}")
            # Reset to prevent issues
            self.samples = None
            self.duration = 0
            return 0
    
    def _apply_compression(self, audio):
        """Apply gentle compression to make audio more suitable for voice applications"""
        # This is a simple gain reduction for louder parts
        # For more advanced compression, we'd need to use a proper DSP library
        try:
            # Convert to numpy array for processing
            samples = np.array(audio.get_array_of_samples())
            sample_width = audio.sample_width
            
            # Calculate threshold (75% of max possible amplitude)
            max_possible_amplitude = 2**(8 * sample_width - 1) - 1
            threshold = 0.75 * max_possible_amplitude
            
            # Apply soft compression (gain reduction) above threshold
            mask = abs(samples) > threshold
            samples[mask] = np.sign(samples[mask]) * (
                threshold + (abs(samples[mask]) - threshold) * 0.5
            )
            
            # Convert back to AudioSegment
            compressed_audio = audio._spawn(samples.tobytes())
            return compressed_audio
        except Exception as e:
            print(f"[ERROR] Compression failed, using original audio: {e}")
            return audio
        
    def play(self, loop=False):
        print(f"[DEBUG] Play called, looping: {loop}, paused state: {self.is_paused}")
        if self.is_paused:
            self.resume()
            return
        
        # Check if we have valid audio to play
        if self.samples is None or len(self.samples) == 0:
            print("[ERROR] No audio data to play")
            return
            
        self.is_looping = loop
        self.stop()  # Ensure any previous playback is stopped
        self.is_playing = True
        self.is_paused = False
        
        print(f"[DEBUG] Starting play thread for {self.active_file_path}")
        self.play_thread = threading.Thread(target=self._play_audio)
        self.play_thread.daemon = True
        self.play_thread.start()
    
    def resume(self):
        """Resume playback after pausing"""
        print(f"[DEBUG] Resuming from position: {self.position:.2f}s")
        self.is_paused = False
        
    def _play_audio(self):
        try:
            device_id = self.device_manager.get_current_device()
            print(f"[DEBUG] Starting playback on device: {device_id}")
            
            # Configure stream with appropriate parameters for voice if needed
            if self.voice_mode:
                # Smaller buffer sizes for lower latency in voice applications
                buffer_size = 512
                # Use appropriate sample rate based on quality setting
                if self.voice_quality == "low":
                    buffer_size = 256
                elif self.voice_quality == "high":
                    buffer_size = 1024
            else:
                # Standard buffer size for regular music playback
                buffer_size = 1024
            
            # Ensure we're not creating a stream if we already have one
            if self.current_stream is not None:
                print("[DEBUG] Closing existing stream before creating new one")
                try:
                    self.current_stream.stop()
                    self.current_stream.close()
                except Exception as e:
                    print(f"[ERROR] Error closing existing stream: {e}")
                self.current_stream = None
            
            # Create stream with explicit settings
            print(f"[DEBUG] Creating new audio stream with rate={self.sample_rate}, device={device_id}")
            self.current_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                device=device_id,
                dtype=np.float32,
                blocksize=buffer_size  # Use appropriate buffer size
            )
            
            self.current_stream.start()
            print("[DEBUG] Audio stream started successfully")
            
            while self.is_playing:
                if not self.is_paused:
                    chunk_size = buffer_size  # Use our configured buffer size
                    start = int(self.position * self.sample_rate)
                    end = start + chunk_size
                    
                    if end >= len(self.samples):
                        if self.is_looping:
                            print("[DEBUG] Looping playback - restarting from beginning")
                            self.position = 0
                            continue
                        else:
                            print("[DEBUG] Reached end of audio - stopping playback")
                            self.stop()
                            if self.current_widget:
                                print(f"[DEBUG] Notifying widget that playback is finished")
                                self.current_widget.after(0, self.current_widget.playback_finished)
                            break
                    
                    # Apply volume control and mute
                    volume_multiplier = 0.0 if self.muted else self.volume
                    chunk = self.samples[start:end] * volume_multiplier
                    
                    # For voice mode, ensure we don't clip
                    if self.voice_mode and not self.muted:
                        # Simple peak normalization to prevent distortion
                        max_val = np.max(np.abs(chunk))
                        if max_val > 0.95:  # If we're close to clipping
                            chunk = chunk * (0.95 / max_val)
                    
                    try:
                        if self.current_stream:
                            self.current_stream.write(chunk.astype(np.float32))
                            self.position += chunk_size / self.sample_rate
                        else:
                            print("[ERROR] Stream was closed unexpectedly")
                            break
                    except Exception as e:
                        print(f"[ERROR] Error writing to stream: {e}")
                        break
                else:
                    time.sleep(0.1)  # Sleep when paused to prevent CPU usage
                    
        except Exception as e:
            print(f"[ERROR] Stream error: {e}")
            self.stop()
            if self.current_widget:
                self.current_widget.after(0, self.current_widget.playback_finished)
    
    def pause(self):
        print(f"[DEBUG] Pausing at position: {self.position:.2f}s")
        self.is_paused = True
        
    def stop(self):
        print("[DEBUG] Stopping playback")
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        
        # Close the stream
        if self.current_stream:
            try:
                print("[DEBUG] Closing audio stream")
                self.current_stream.stop()
                self.current_stream.close()
            except Exception as e:
                print(f"[ERROR] Error closing stream: {e}")
            finally:
                self.current_stream = None
                print("[DEBUG] Stream closed and set to None")
            
    def seek(self, position):
        if self.duration > 0:
            new_position = min(max(0, position), 1) * self.duration
            print(f"[DEBUG] Seeking to position: {new_position:.2f}s")
            self.position = new_position
        else:
            print("[DEBUG] Can't seek - no duration information")
            self.position = 0
        
    def set_volume(self, volume):
        self.volume = min(max(0, volume), 1.0)
        print(f"[DEBUG] Volume set to: {self.volume:.2f}")
        if not self.muted:
            self.last_volume = self.volume
            
    def toggle_mute(self):
        self.muted = not self.muted
        print(f"[DEBUG] Mute toggled: {self.muted}")
        if self.muted:
            self.last_volume = self.volume
            self.volume = 0
        else:
            self.volume = self.last_volume
            
    def restart_playback(self):
        """Restart playback with new device settings"""
        print("[DEBUG] Restarting playback with new settings")
        if self.active_file_path and self.is_playing:
            was_playing = True
            was_paused = self.is_paused
            current_position = self.position
            
            print(f"[DEBUG] Stopping for restart, was_paused: {was_paused}, position: {current_position:.2f}s")
            self.stop()
            
            print(f"[DEBUG] Reloading audio: {self.active_file_path}")
            self.load_audio(self.active_file_path, self.current_widget)
            
            self.position = current_position
            
            if was_playing:
                print("[DEBUG] Resuming playback after restart")
                self.play(self.is_looping)
                if was_paused:
                    self.pause()
                
    def set_playback_ended_callback(self, callback):
        """Set a callback to be called when playback ends naturally"""
        print(f"[DEBUG] Setting playback ended callback: {callback}")
        self.playback_ended_callback = callback

    def set_voice_quality(self, quality):
        """Set voice quality mode (low, medium, high)"""
        print(f"[DEBUG] Changing voice quality from {self.voice_quality} to {quality}")
        
        # Only take action if the quality actually changed
        if quality == self.voice_quality:
            print("[DEBUG] Voice quality unchanged, no action needed")
            return
            
        self.voice_quality = quality
        
        # Restart playback with new settings if in voice mode and playing
        if self.voice_mode and self.active_file_path and self.is_playing:
            print("[DEBUG] Restarting playback with new voice quality settings")
            # Save current state
            was_playing = True
            was_paused = self.is_paused
            current_position = self.position
            
            # Stop playback
            self.stop()
            
            # Reload with new settings
            self.load_audio(self.active_file_path, self.current_widget)
            
            # Restore position
            self.position = current_position
            
            # Resume playback if it was active
            if was_playing:
                self.play(self.is_looping)
                if was_paused:
                    self.pause()
    
    def set_voice_mode(self, enabled):
        """Enable or disable voice application mode"""
        print(f"[DEBUG] Setting voice mode to: {enabled}")
        self.voice_mode = enabled
        
        if self.active_file_path and self.is_playing:
            # Reload and restart playback with new settings
            was_playing = True
            current_position = self.position
            was_paused = self.is_paused
            
            self.stop()
            self.load_audio(self.active_file_path, self.current_widget)
            self.position = current_position
            
            if was_playing:
                self.play(self.is_looping)
                if was_paused:
                    self.pause()
