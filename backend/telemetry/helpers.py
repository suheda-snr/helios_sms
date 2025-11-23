import wave
import math
import logging

logger = logging.getLogger(__name__)

def _make_beep(path, freq=880, duration=0.4, volume=0.3, rate=44100):
    n_samples = int(rate * duration)
    amplitude = int(32767 * volume)
    try:
        with wave.open(str(path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            frames = bytearray()
            for i in range(n_samples):
                t = i / rate
                sample = int(amplitude * math.sin(2 * math.pi * freq * t))
                frames += sample.to_bytes(2, 'little', signed=True)
            wf.writeframes(frames)
    except Exception:
        logger.exception("Failed to create alert sound at %s", path)
        raise
