import threading
import time
import uuid
from dataclasses import asdict
from typing import Optional

from backend.common.mqtt import MQTTClient
from backend.common.topics import TRICORDER_MISSION_COMMANDS, TRICORDER_MISSION_STATE
from .models import Mission, Task


class MissionManager:

    STATE_TOPIC = TRICORDER_MISSION_STATE
    COMMAND_TOPIC = TRICORDER_MISSION_COMMANDS

    def __init__(self, mqtt_host="localhost", mqtt_port=1883, client_id="mission-manager", state_change_callback=None):
        self._mqtt = MQTTClient(mqtt_host, mqtt_port, client_id)
        # configure default topic and message callback
        try:
            self._mqtt.DEFAULT_TOPIC = self.COMMAND_TOPIC
            self._mqtt.on_message_callback = self._on_mqtt_message
        except Exception:
            pass
        if self._mqtt.connect():
            try:
                self._mqtt.loop_start()
            except Exception:
                pass

        self._missions = {}
        self._lock = threading.Lock()
        self._running = True
        self._ticker = threading.Thread(target=self._ticker_loop, daemon=True)
        self._ticker.start()
        # optional callback that will be invoked when state is published
        self._state_change_callback = state_change_callback

    def shutdown(self):
        self._running = False
        try:
            self._mqtt.disconnect()
        except Exception:
            pass

    def create_mission(self, name: str, max_duration_seconds: Optional[int] = None) -> Mission:
        m = Mission(id=str(uuid.uuid4()), name=name, max_duration_seconds=max_duration_seconds)
        with self._lock:
            self._missions[m.id] = m
        self._publish_state(m.id)
        return m

    def add_task(self, mission_id: str, title: str, description: Optional[str] = None, projected_seconds: Optional[int] = None) -> Optional[Task]:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                return None
            t = Task(id=str(uuid.uuid4()), title=title, description=description, projected_seconds=projected_seconds)
            m.tasks.append(t)
        self._publish_state(mission_id)
        return t

    def start_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m or m.started:
                return False
            m.started = True
            m.paused = False
        self._publish_state(mission_id)
        return True

    def pause_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m or not m.started or m.paused:
                return False
            m.paused = True
        self._publish_state(mission_id)
        return True

    def stop_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                return False
            m.started = False
            m.paused = False
        self._publish_state(mission_id)
        return True

    def complete_task(self, mission_id: str, task_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                return False
            for t in m.tasks:
                if t.id == task_id:
                    t.completed = True
                    self._publish_state(mission_id)
                    return True
        return False

    def _publish_state(self, mission_id: Optional[str] = None):
        payload = {}
        with self._lock:
            if mission_id:
                m = self._missions.get(mission_id)
                if not m:
                    return
                payload = {"mission": asdict(m)}
            else:
                payload = {"missions": [asdict(m) for m in self._missions.values()]}
        try:
            self._mqtt.publish(self.STATE_TOPIC, payload)
        except Exception:
            pass

        # call local state-change callback if provided
        try:
            if self._state_change_callback:
                try:
                    self._state_change_callback(payload)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_mqtt_message(self, topic, payload):
        action = payload.get("action")
        if not action:
            return
        if action == "create_mission":
            name = payload.get("name", "Unnamed")
            max_d = payload.get("max_duration_seconds")
            m = self.create_mission(name, max_d)
            self._publish_state(m.id)
        elif action == "add_task":
            mid = payload.get("mission_id")
            if not mid:
                return
            self.add_task(mid, payload.get("title", "Task"), payload.get("description"), payload.get("projected_seconds"))
        elif action == "start":
            self.start_mission(payload.get("mission_id"))
        elif action == "pause":
            self.pause_mission(payload.get("mission_id"))
        elif action == "stop":
            self.stop_mission(payload.get("mission_id"))
        elif action == "complete_task":
            self.complete_task(payload.get("mission_id"), payload.get("task_id"))

    def _ticker_loop(self):
        while self._running:
            time.sleep(1)
            updated = []
            with self._lock:
                for m in self._missions.values():
                    if m.started and not m.paused:
                        m.elapsed_seconds += 1
                        updated.append(m.id)
            for mid in updated:
                self._publish_state(mid)


if __name__ == "__main__":
    mm = MissionManager()
    print("MissionManager running — listening for commands on tricorder/mission/commands")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down mission manager...")
        mm.shutdown()
