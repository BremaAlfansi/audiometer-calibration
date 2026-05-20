from core.audio_engine import AudioEngine


class DeviceManager:
    def __init__(self):
        self.audio = AudioEngine()

    def list_input_devices(self):
        return self.audio.get_devices()