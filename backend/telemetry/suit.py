from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path
import time
import os
import wave
import math

try:
    from backend.mqtt import MQTTClient
except Exception:
    # fallback for running modules as scripts where package name isn't on sys.path
    from mqtt import MQTTClient

TELEMETRY_TOPIC = "tricorder/telemetry"

from .producer import WarningEngine
from .models import Telemetry


def _make_beep(path, freq=880.0, duration_s=0.4, volume=0.3, rate=44100):
    # create a short sine wave beep .wav file
    n_samples = int(rate * duration_s)
    amplitude = int(32767 * volume)
    with wave.open(str(path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for i in range(n_samples):
            t = float(i) / rate
            sample = int(amplitude * math.sin(2 * math.pi * freq * t))
            wf.writeframesraw(sample.to_bytes(2, byteorder='little', signed=True))


class TricorderBackend(QObject):
    telemetryUpdated = Signal(dict)
    # For backward compatibility with simple UIs we keep a string signal
    warningIssued = Signal(str)
    # Emit detailed warning dict when new warning raised
    warningRaised = Signal(dict)
    # Emit id when a warning is cleared
    warningCleared = Signal(str)
    # Emitted when active warnings list changes
    activeWarningsUpdated = Signal()

    def __init__(self, broker_host="localhost", broker_port=1883, client_id="tricorder-app"):
        super().__init__()

        # create assets dir for sounds/logs
        backend_dir = Path(__file__).resolve().parents[1]
        assets_dir = backend_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        self._alert_sound_path = assets_dir / "warning.wav"
        if not self._alert_sound_path.exists():
            try:
                _make_beep(self._alert_sound_path)
            except Exception:
                pass

        # Warning engine handles thresholds and active warnings
        self.engine = WarningEngine()
        # wire engine callbacks to Qt signals
        self.engine.on_raise = lambda info: (self._emit_warning_issued(info), self._emit_warning_raised(info))
        self.engine.on_clear = lambda wid: self._emit_warning_cleared(wid)
        self.engine.on_update = lambda: self.activeWarningsUpdated.emit()

        # MQTT setup
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        self.mqtt.connect()
        self.mqtt.loop_start()

    def _emit_warning_issued(self, info: dict):
        try:
            # simplified text signal
            self.warningIssued.emit(info.get('message', ''))
        except Exception:
            pass

    def _emit_warning_raised(self, info: dict):
        try:
            self.warningRaised.emit(info)
        except Exception:
            pass

    def _emit_warning_cleared(self, wid: str):
        try:
            self.warningCleared.emit(wid)
        except Exception:
            pass

    def _on_message(self, topic, payload):
        # lightweight debug print to help diagnose UI delivery issues
        try:
            print(f"TricorderBackend: telemetry received: {payload}")
        except Exception:
            pass
        if topic == TELEMETRY_TOPIC:
            self.telemetryUpdated.emit(payload)
            # keep engine input as plain dict for simplicity
            self.engine.process(payload)

    @Slot(str)
    def acknowledgeWarning(self, wid):
        self.engine.acknowledge(wid)

    @Slot(result='QVariant')
    def getActiveWarnings(self):
        # return list of warning dicts
        return self.engine.get_active_warnings()

    @Slot(result=str)
    def getAlertSoundPath(self):
        return str(self._alert_sound_path)
