from PySide6.QtCore import QObject, Signal, Slot, QTimer
from pathlib import Path
import time
import os
import wave
import math
from mqtt.client import MQTTClient
# Import detect_warnings from the new vitals module. Use multiple fallbacks
try:
    from backend.telemetry.vitals import detect_warnings
except Exception:
    try:
        from .vitals import detect_warnings
    except Exception:
        try:
            from vitals import detect_warnings
        except Exception:
            def detect_warnings(telemetry, thresholds):
                return {}

# Import MissionManager robustly so running `python backend\main.py` works both
# when modules are executed as packages and when run as scripts.
try:
    # normal package import when running as module (backend.telemetry.suit)
    from backend.missions import MissionManager
except Exception:
    try:
        # relative import when executed as package
        from ..missions import MissionManager
    except Exception:
        try:
            # fallback when running from backend/ directory as script
            from missions import MissionManager
        except Exception:
            MissionManager = None

TELEMETRY_TOPIC = "tricorder/telemetry"


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
        self._log_path = backend_dir / "warnings.log"
        self._alert_sound_path = assets_dir / "warning.wav"
        if not self._alert_sound_path.exists():
            try:
                _make_beep(self._alert_sound_path)
            except Exception:
                pass

        # configurable thresholds
        self.thresholds = {
            "o2_low": 19.0,
            "battery_low": 15.0,
            "co2_high": 1.0,  # percent
            "suit_temp_low": -20.0,
            "suit_temp_high": 45.0,
        }

        # Active warnings tracked by id -> info dict
        self.active_warnings = {}

        # Keep last telemetry payload available for QML to query after engine loads
        self._last_telemetry = {}

        # Mission manager for mission planning/execution
        try:
            self.missionManager = MissionManager(self)
        except Exception:
            self.missionManager = None

        # Seed demo missions for UI and testing if mission manager is available
        try:
            if self.missionManager:
                # Create a repair mission with a few tasks
                mid = self.missionManager.createMission("Repair Panel", 600, 900)
                self.missionManager.addTask(mid, "Approach panel", "Move to the damaged panel", 60)
                self.missionManager.addTask(mid, "Secure tether", "Attach safety tether", 30)
                self.missionManager.addTask(mid, "Replace module", "Swap out faulty module", 300)

                # Create an inspection mission
                mid2 = self.missionManager.createMission("Inspect Antenna", 300, 600)
                self.missionManager.addTask(mid2, "Scan for damage", "Run diagnostic scan", 120)
                self.missionManager.addTask(mid2, "Document", "Take photos and logs", 60)
        except Exception:
            pass

        # MQTT setup
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        self.mqtt.connect()
        self.mqtt.loop_start()

        # Emit an initial telemetry payload so UI has values before MQTT/simulator runs
        try:
            initial = {
                'o2': 98.6,
                'battery': 88,
                'co2': 0.04,
                'leak': False,
                'suit_temp': 21.5,
                'external_temp': -60.0,
            }
            # store and send initial telemetry to QML and check warnings
            self._last_telemetry = initial
            try:
                self.telemetryUpdated.emit(initial)
            except Exception:
                pass
            self._check_warnings(initial)
        except Exception:
            pass

    def _on_message(self, topic, payload):
        if topic == TELEMETRY_TOPIC:
            # The MQTT client runs in a background thread. Emitting Qt signals
            # or manipulating Qt objects from that thread can cause
            # "Signal source has been deleted" or other thread-safety errors.
            # Schedule the emissions to run on the Qt main thread instead.
            try:
                # store last telemetry so QML can query it if needed
                self._last_telemetry = payload
                QTimer.singleShot(0, lambda payload=payload: self.telemetryUpdated.emit(payload))
                QTimer.singleShot(0, lambda payload=payload: self._check_warnings(payload))
            except Exception:
                # Fallback to direct call if scheduling fails
                try:
                    self.telemetryUpdated.emit(payload)
                except Exception:
                    pass
                try:
                    self._check_warnings(payload)
                except Exception:
                    pass

    def _log(self, text):
        try:
            with open(self._log_path, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
        except Exception:
            pass

    def _raise_warning(self, wid, message, severity="critical", cause=None):
        now = time.time()
        if wid in self.active_warnings:
            # update timestamp
            self.active_warnings[wid]['last_seen'] = now
            return

        info = {
            'id': wid,
            'message': message,
            'severity': severity,
            'cause': cause,
            'timestamp': now,
            'acknowledged': False,
        }
        self.active_warnings[wid] = info
        # emit both simplified and detailed signals
        try:
            self.warningIssued.emit(message)
        except Exception:
            pass
        try:
            self.warningRaised.emit(info)
        except Exception:
            pass
        self.activeWarningsUpdated.emit()
        self._log(f"RAISE {wid}: {message} (cause={cause})")

    def _clear_warning(self, wid):
        if wid in self.active_warnings:
            self._log(f"CLEAR {wid}: {self.active_warnings[wid].get('message')}")
            del self.active_warnings[wid]
            try:
                self.warningCleared.emit(wid)
            except Exception:
                pass
            self.activeWarningsUpdated.emit()

    @Slot(str)
    def acknowledgeWarning(self, wid):
        if wid in self.active_warnings:
            self.active_warnings[wid]['acknowledged'] = True
            self._log(f"ACK {wid}")
            self.activeWarningsUpdated.emit()

    @Slot(result='QVariant')
    def getActiveWarnings(self):
        # return list of warning dicts
        return list(self.active_warnings.values())

    @Slot(result='QVariant')
    def getLastTelemetry(self):
        # Return the last known telemetry payload (may be empty dict)
        return self._last_telemetry

    @Slot(result=str)
    def getAlertSoundPath(self):
        return str(self._alert_sound_path)

    def _check_warnings(self, telemetry):
        # Delegate detection logic to the vitals module and then reconcile
        try:
            current = detect_warnings(telemetry, self.thresholds)
        except Exception:
            current = {}

        for key, (msg, sev) in current.items():
            self._raise_warning(key, msg, severity=sev, cause=None)

        to_clear = [wid for wid in list(self.active_warnings.keys()) if wid not in current]
        for wid in to_clear:
            self._clear_warning(wid)
