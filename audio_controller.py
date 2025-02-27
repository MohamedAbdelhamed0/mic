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
        
    def load_audio(self, file_path, widget=None):
        if self.current_widget and self.current_widget != widget:
            # Stop previous playback
            self.current_widget.stop_playback()
        
        self.current_widget = widget
        self.active_file_path = file_path
        
        # Load audio with appropriate format for voice applications if needed
        audio = AudioSegment.from_file(file_path)
        
        # When in voice mode, optimize for voice applications
        if self.voice_mode:
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
            # For regular playback, just ensure it's mono
            if audio.channels > 1:
                audio = audio.set_channels(1)
        
        self.samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        self.samples = self.samples / np.iinfo(audio.array_type).max
        self.sample_rate = audio.frame_rate
        self.duration = len(self.samples) / self.sample_rate
        self.position = 0
        return self.duration
    
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
            print(f"Compression failed, using original audio: {e}")
            return audio
        
    def play(self, loop=False):
        if self.is_paused:
            self.resume()
            return
            
        self.is_looping = loop
        self.stop()
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_audio)
        self.play_thread.daemon = True
        self.play_thread.start()
    
    def resume(self):
        """Resume playback after pausing"""
        self.is_paused = False
        
    def _play_audio(self):
        try:
            device_id = self.device_manager.get_current_device()
            print(f"Starting playback on device: {device_id}")
            
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
            
            # Create stream with explicit settings
            self.current_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                device=device_id,
                dtype=np.float32,
                blocksize=buffer_size  # Use appropriate buffer size
            )
            
            self.current_stream.start()
            
            while self.is_playing:
                if not self.is_paused:
                    chunk_size = buffer_size  # Use our configured buffer size
                    start = int(self.position * self.sample_rate)
                    end = start + chunk_size
                    
                    if end >= len(self.samples):
                        if self.is_looping:
                            print("Looping playback")
                            self.position = 0
                            continue
                        else:
                            self.stop()
                            if self.current_widget:
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
                    
                    self.current_stream.write(chunk.astype(np.float32))
                    self.position += chunk_size / self.sample_rate
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Stream error: {e}")
            self.stop()
            if self.current_widget:
                self.current_widget.after(0, self.current_widget.playback_finished)
    
    def pause(self):
        self.is_paused = True
        
    def stop(self):
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        if self.current_stream:
            try:
                self.current_stream.stop()
                self.current_stream.close()
            except Exception as e:
                print(f"Error closing stream: {e}")
            finally:
                self.current_stream = None
            
    def seek(self, position):
        self.position = min(max(0, position), self.duration)
        
    def set_volume(self, volume):
        self.volume = min(max(0, volume), 1.0)
        if not self.muted:
            self.last_volume = self.volume
            
    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.last_volume = self.volume
            self.volume = 0
        else:
            self.volume = self.last_volume
            
    def restart_playback(self):
        """Restart playback with new device settings"""
        if self.active_file_path and self.is_playing:
            was_playing = True
            current_position = self.position
            self.stop()
            self.load_audio(self.active_file_path)
            self.position = current_position
            if was_playing:
                self.play(self.is_looping)
                
    def set_voice_mode(self, enabled):
        """Enable or disable voice application mode"""
        self.voice_mode = enabled
        if self.active_file_path and self.is_playing:
            # Reload and restart playback with new settings
            was_playing = True
            current_position = self.position
            self.stop()
            self.load_audio(self.active_file_path, self.current_widget)
            self.position = current_position
            if was_playing:
                self.play(self.is_looping)
                
    def set_voice_quality(self, quality):
        """Set voice quality mode (low, medium, high)"""
        self.voice_quality = quality
        if self.voice_mode and self.active_file_path and self.is_playing:
            # Reload and restart playback with new settings
            was_playing = True
            current_position = self.position
            self.stop()
            self.load_audio(self.active_file_path, self.current_widget)
            self.position = current_position
            if was_playing:
                self.play(self.is_looping)
                
    def set_playback_ended_callback(self, callback):
        """Set a callback to be called when playback ends naturally"""
        self.playback_ended_callback = callback
