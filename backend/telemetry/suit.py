from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path
import wave
import math

try:
    from backend.mqtt import MQTTClient
except ImportError:
    from mqtt import MQTTClient

from .producer import WarningEngine


def _make_beep(path, freq=880, duration=0.4, volume=0.3, rate=44100):
    n_samples = int(rate * duration)
    amplitude = int(32767 * volume)
    with wave.open(str(path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for i in range(n_samples):
            t = i / rate
            sample = int(amplitude * math.sin(2 * math.pi * freq * t))
            wf.writeframesraw(sample.to_bytes(2, 'little', signed=True))


class TricorderBackend(QObject):
    telemetryUpdated = Signal(dict)
    warningIssued = Signal(str)
    warningRaised = Signal(dict)
    warningCleared = Signal(str)
    activeWarningsUpdated = Signal()

    def __init__(self, broker_host="localhost", broker_port=1883, client_id="tricorder-app"):
        super().__init__()
        
        # Create alert sound
        backend_dir = Path(__file__).resolve().parents[1]
        assets_dir = backend_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        self._alert_sound = assets_dir / "warning.wav"
        if not self._alert_sound.exists():
            try:
                _make_beep(self._alert_sound)
            except: pass
        
        # Warning engine
        self.engine = WarningEngine()
        self.engine.on_raise = lambda info: (
            self.warningIssued.emit(info.get('message', '')),
            self.warningRaised.emit(info)
        )
        self.engine.on_clear = lambda wid: self.warningCleared.emit(wid)
        self.engine.on_update = lambda: self.activeWarningsUpdated.emit()
        
        # MQTT connection
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        if self.mqtt.connect():
            self.mqtt.loop_start()

    def _on_message(self, topic, payload):
        print(f"Telemetry: {payload}")
        self.telemetryUpdated.emit(payload)
        self.engine.process(payload)

    @Slot(str)
    def acknowledgeWarning(self, wid):
        self.engine.acknowledge(wid)

    @Slot(result='QVariant')
    def getActiveWarnings(self):
        return self.engine.get_active_warnings()

    @Slot(result=str)
    def getAlertSoundPath(self):
        return str(self._alert_sound)
