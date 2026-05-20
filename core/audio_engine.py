import sounddevice as sd
import numpy as np


class AudioEngine:
    def __init__(self):
        self.sample_rate = 48000
        self.duration = 0.5
        self.device_index = None

    def get_devices(self):
        devices = sd.query_devices()

        valid_devices = []
        seen_names = set()

        ignore_keywords = [
            "microsoft sound mapper",
            "primary sound capture driver"
        ]

        for idx, device in enumerate(devices):
            name = device["name"]
            max_input = device["max_input_channels"]

            if max_input <= 0:
                continue

            lower_name = name.lower()

            if any(
                keyword in lower_name
                for keyword in ignore_keywords
            ):
                continue

            if name in seen_names:
                continue

            seen_names.add(name)

            valid_devices.append((idx, name))

        return valid_devices

    def set_device(self, device_index):
        self.device_index = device_index

    def capture(self):
        if self.device_index is None:
            raise RuntimeError(
                "No input device selected."
            )

        frames = int(
            self.sample_rate * self.duration
        )

        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            device=self.device_index
        )

        sd.wait()

        return np.squeeze(recording)