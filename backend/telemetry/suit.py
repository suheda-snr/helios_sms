from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path
import time
import os
import wave
import math
from mqtt.client import MQTTClient

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

        # MQTT setup
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        self.mqtt.connect()
        self.mqtt.loop_start()

    def _on_message(self, topic, payload):
        if topic == TELEMETRY_TOPIC:
            self.telemetryUpdated.emit(payload)
            self._check_warnings(payload)

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

    @Slot(result=str)
    def getAlertSoundPath(self):
        return str(self._alert_sound_path)

    def _check_warnings(self, telemetry):
        # Determine current condition-based warnings
        current = {}

        o2 = telemetry.get('o2')
        battery = telemetry.get('battery')
        co2 = telemetry.get('co2')
        leak = telemetry.get('leak')
        suit_temp = telemetry.get('suit_temp')

        # LOW O2
        if o2 is not None and o2 < self.thresholds['o2_low']:
            current['low_o2'] = (f"LOW O2 ({o2}%)", 'critical')

        # LOW BATTERY
        if battery is not None and battery < self.thresholds['battery_low']:
            current['low_batt'] = (f"LOW BATTERY ({battery}%)", 'critical')

        # HIGH CO2
        if co2 is not None and co2 > self.thresholds['co2_high']:
            current['high_co2'] = (f"HIGH CO2 ({co2}%)", 'warning')

        # SUIT LEAK
        if leak:
            current['suit_leak'] = ("SUIT LEAK DETECTED", 'critical')

        # Temp extremes
        if suit_temp is not None:
            if suit_temp < self.thresholds['suit_temp_low']:
                current['temp_low'] = (f"SUIT TEMP LOW ({suit_temp}C)", 'warning')
            if suit_temp > self.thresholds['suit_temp_high']:
                current['temp_high'] = (f"SUIT TEMP HIGH ({suit_temp}C)", 'warning')

        # Root-cause example: if leak and low o2 => ATM LOSS: LEAK
        if 'suit_leak' in current and 'low_o2' in current:
            current['atm_loss'] = ("ATMOSPHERE LOSS - LEAK", 'critical')
            # optionally remove the individual low_o2/suit_leak to avoid duplicates
            current.pop('low_o2', None)
            current.pop('suit_leak', None)

        # Compare current to active_warnings: raise new ones, clear missing ones
        # Add / update current
        for key, (msg, sev) in current.items():
            self._raise_warning(key, msg, severity=sev, cause=None)

        # Clear warnings that are no longer present
        to_clear = [wid for wid in list(self.active_warnings.keys()) if wid not in current]
        for wid in to_clear:
            # only clear if not acknowledged or if acknowledged and resolved
            self._clear_warning(wid)
