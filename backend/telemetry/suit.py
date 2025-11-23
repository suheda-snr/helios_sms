from PySide6.QtCore import QObject, Signal, Slot, QTimer
from pathlib import Path
import time
import os
import wave
import math
from mqtt.client import MQTTClient
import uuid
import json

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
    # Missions
    missionsUpdated = Signal()
    missionProgress = Signal(dict)

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
        # persistence path for missions
        self._missions_path = assets_dir / "missions.json"
        # try to load persisted missions
        try:
            self._load_missions()
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

        # Missions tracked by id -> mission dict
        self.missions = {}

        # Timer to update running missions every second
        self._mission_timer = QTimer()
        self._mission_timer.setInterval(1000)
        self._mission_timer.timeout.connect(self._on_mission_tick)
        # Start timer — it's lightweight and will only act when missions are running
        try:
            self._mission_timer.start()
        except Exception:
            pass

        # MQTT setup
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        self.mqtt.connect()
        self.mqtt.loop_start()

    def _on_message(self, topic, payload):
        if topic == TELEMETRY_TOPIC:
            self.telemetryUpdated.emit(payload)
            self._check_warnings(payload)
        elif topic == "tricorder/commands":
            # handle incoming commands such as acknowledgements from other frontends
            try:
                if isinstance(payload, dict) and payload.get('type') == 'ack':
                    wid = payload.get('id')
                    if wid and wid in self.active_warnings:
                        self.active_warnings[wid]['acknowledged'] = True
                        self._log(f"ACK (remote) {wid}")
                        self.activeWarningsUpdated.emit()
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

    def _on_mission_tick(self):
        # Update elapsed times for running missions and emit progress
        now = time.time()
        updated = False
        for mid, m in list(self.missions.items()):
            if m.get('state') == 'running':
                start = m.get('start_time')
                if start:
                    m['elapsed'] = m.get('elapsed', 0) + 1
                    # If we've reached duration, mark as stopped
                    if m.get('duration') is not None and m['elapsed'] >= m['duration']:
                        m['state'] = 'stopped'
                        m['start_time'] = None
                        # persist mission change
                        try:
                            self._save_missions()
                        except Exception:
                            pass
                    # emit progress per mission
                    try:
                        self.missionProgress.emit(m)
                    except Exception:
                        pass
                    updated = True
        if updated:
            try:
                self.missionsUpdated.emit()
            except Exception:
                pass

    @Slot(str, 'QVariant', 'QVariant', 'QVariant', result='QVariant')
    def createMission(self, name, duration_seconds, tasks, description=None):
        """Create a mission with ordered tasks. `tasks` expected as list of strings or dicts.
        `description` is optional string."""
        mid = str(uuid.uuid4())
        # normalize tasks (robust to QVariant/Mapping/JS objects from QML)
        tlist = []
        # QML may pass a QJSValue or a JSON string. If it's a JSON string, parse it first.
        converted_tasks = tasks
        try:
            if isinstance(tasks, str):
                # tasks passed as JSON string from QML
                converted_tasks = json.loads(tasks)
            else:
                tv = getattr(tasks, 'toVariant', None)
                if callable(tv):
                    converted_tasks = tv()
        except Exception:
            converted_tasks = tasks

        try:
            # try to iterate tasks if it's a sequence-like
            for t in converted_tasks or []:
                title = None
                completed = False
                try:
                    if isinstance(t, dict):
                        title = t.get('title', '')
                        completed = bool(t.get('completed', False))
                    else:
                        # try mapping-like get
                        get = getattr(t, 'get', None)
                        if callable(get):
                            title = get('title', None)
                            completed = bool(get('completed', False))
                        else:
                            # try attribute access
                            title = getattr(t, 'title', None)
                            completed = getattr(t, 'completed', False)
                            if title is None:
                                # try indexing
                                try:
                                    title = t['title']
                                except Exception:
                                    title = None
                except Exception:
                    title = None

                if title is None:
                    # fallback to string representation
                    try:
                        title = str(t)
                    except Exception:
                        title = ""

                tlist.append({'title': title, 'completed': bool(completed)})
        except Exception:
            # fallback empty
            tlist = []

        # debug: show converted tasks shape
        try:
            print(f"createMission: converted_tasks_type={type(converted_tasks)} normalized_count={len(tlist)}")
        except Exception:
            pass
        # normalize duration: handle NaN/invalid values
        try:
            duration_val = int(duration_seconds) if duration_seconds is not None else None
        except Exception:
            duration_val = None

        mission = {
            'id': mid,
            'name': name,
            'duration': duration_val,
            'description': description,
            'tasks': tlist,
            'state': 'stopped',
            'start_time': None,
            'elapsed': 0,
            'created_at': time.time(),
        }
        self.missions[mid] = mission
        try:
            self.missionsUpdated.emit()
        except Exception:
            pass
        # debug logging
        try:
            print(f"createMission: name={name!r} duration={duration_val!r} tasks_in={repr(tasks)} -> normalized_count={len(tlist)}")
            self._log(f"CREATE_MISSION {mid} name={name} tasks={len(tlist)}")
            for t in tlist:
                self._log(f"  TASK: {t.get('title')} completed={t.get('completed')}" )
        except Exception:
            pass
        try:
            self._save_missions()
        except Exception:
            pass
        return mission

    @Slot(str)
    def startMission(self, mid):
        m = self.missions.get(mid)
        if not m:
            return
        if m.get('state') != 'running':
            m['state'] = 'running'
            m['start_time'] = time.time()
            try:
                self.missionsUpdated.emit()
            except Exception:
                pass
            try:
                self._save_missions()
            except Exception:
                pass

    @Slot(str)
    def pauseMission(self, mid):
        m = self.missions.get(mid)
        if not m:
            return
        if m.get('state') == 'running':
            # stop timer and preserve elapsed
            m['state'] = 'paused'
            m['start_time'] = None
            try:
                self.missionsUpdated.emit()
            except Exception:
                pass
            try:
                self._save_missions()
            except Exception:
                pass

    @Slot(str)
    def stopMission(self, mid):
        m = self.missions.get(mid)
        if not m:
            return
        m['state'] = 'stopped'
        m['start_time'] = None
        m['elapsed'] = 0
        try:
            self.missionsUpdated.emit()
        except Exception:
            pass
        try:
            self._save_missions()
        except Exception:
            pass

    @Slot(str, int)
    def toggleTaskComplete(self, mid, index):
        m = self.missions.get(mid)
        if not m:
            return
        try:
            task = m['tasks'][int(index)]
            task['completed'] = not bool(task.get('completed'))
            try:
                self.missionsUpdated.emit()
            except Exception:
                pass
        except Exception:
            pass
        try:
            self._save_missions()
        except Exception:
            pass

    @Slot(str, str)
    def addTaskToMission(self, mid, title):
        """Append a new task (title) to mission `mid`."""
        m = self.missions.get(mid)
        if not m:
            return
        try:
            m.setdefault('tasks', []).append({'title': str(title), 'completed': False})
            self.missionsUpdated.emit()
            self._save_missions()
        except Exception:
            pass

    @Slot(str, int)
    def removeTaskFromMission(self, mid, index):
        m = self.missions.get(mid)
        if not m:
            return
        try:
            if 0 <= int(index) < len(m.get('tasks', [])):
                m['tasks'].pop(int(index))
                self.missionsUpdated.emit()
                self._save_missions()
        except Exception:
            pass

    @Slot(result='QVariant')
    def getMissions(self):
        try:
            # return missions sorted by creation time for predictable ordering
            return sorted(list(self.missions.values()), key=lambda m: m.get('created_at', 0))
        except Exception:
            return list(self.missions.values())

    def _save_missions(self):
        try:
            # ensure serializable copy
            serial = []
            for m in self.missions.values():
                # shallow copy is fine; values are primitives/lists/dicts
                serial.append(m)
            tmp = str(self._missions_path) + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(serial, f, ensure_ascii=False, indent=2)
            # atomic replace
            os.replace(tmp, str(self._missions_path))
        except Exception:
            pass

    def _load_missions(self):
        try:
            if not self._missions_path.exists():
                return
            with open(str(self._missions_path), 'r', encoding='utf-8') as f:
                data = json.load(f)
            # convert list to dict by id
            for m in data:
                if isinstance(m, dict) and m.get('id'):
                    # ensure tasks list exists
                    if 'tasks' not in m or not isinstance(m['tasks'], list):
                        m['tasks'] = []
                    self.missions[m['id']] = m
        except Exception:
            pass
