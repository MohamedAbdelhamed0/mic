import sounddevice as sd

class DeviceManager:
    def __init__(self, default_device=None):
        self.current_device = None
        sd.default.samplerate = 44100
        sd.default.channels = 1
        
        if default_device is not None:
            try:
                self.set_device(default_device)
            except:
                self._ensure_valid_device()
        else:
            self._ensure_valid_device()
            
    def _ensure_valid_device(self):
        devices = self.get_output_devices()
        if not devices:
            raise RuntimeError("No output devices found")
        if self.current_device is None:
            # Try to use system default output first
            try:
                default_device = sd.query_devices(kind='output')
                self.current_device = default_device['index']
            except:
                self.current_device = devices[0][0]  # Fallback to first device
            
    def get_output_devices(self):
        devices = sd.query_devices()
        return [(i, device) for i, device in enumerate(devices) 
                if device['max_output_channels'] > 0]
    
    def set_device(self, device_id):
        try:
            # Test if device is valid
            sd.check_output_settings(
                device=device_id,
                channels=1,
                samplerate=44100
            )
            self.current_device = device_id
            sd.default.device[1] = device_id
            print(f"Successfully set device {device_id}")  # Debug print
        except sd.PortAudioError as e:
            print(f"Error setting device {device_id}: {e}")
            self._ensure_valid_device()
        
    def get_current_device(self):
        if self.current_device is None:
            self._ensure_valid_device()
        return self.current_device
