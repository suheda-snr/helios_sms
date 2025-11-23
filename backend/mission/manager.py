import threading
import time
import uuid
import os
import logging
from typing import Optional, List

from backend.common.mqtt import MQTTClient
from backend.common.topics import TRICORDER_MISSION_COMMANDS, TRICORDER_MISSION_STATE
from .models import Mission, Task
from .persistence import PersistenceManager
from .mqtt_adapter import configure_client, start_loop_if_connected, publish_state


class MissionManager:

    STATE_TOPIC = TRICORDER_MISSION_STATE
    COMMAND_TOPIC = TRICORDER_MISSION_COMMANDS

    def __init__(self, mqtt_host: Optional[str] = "localhost", mqtt_port: int = 1883, client_id: Optional[str] = "mission-manager", state_change_callback=None, persistence_file: Optional[str] = None):
        self._logger = logging.getLogger(__name__)

        # Only create and configure MQTT client if a host is provided.
        if mqtt_host is not None and client_id is not None:
            try:
                self._mqtt = MQTTClient(mqtt_host, mqtt_port, client_id)
                configure_client(self._mqtt, self.COMMAND_TOPIC, self._on_mqtt_message)
                start_loop_if_connected(self._mqtt)
            except Exception:
                self._logger.exception("Failed to initialize MQTT client; continuing without MQTT")
                self._mqtt = None
        else:
            self._mqtt = None

        self._missions = {}
        self._lock = threading.Lock()
        self._running = True
        # optional callback that will be invoked when state is published
        self._state_change_callback = state_change_callback

        # persistence manager (optional)
        default_path = os.path.join(os.path.dirname(__file__), 'missions.json')
        persistence_path = persistence_file if persistence_file is not None else default_path
        self._persistence = PersistenceManager(persistence_path)
        try:
            for m in self._persistence.load():
                with self._lock:
                    self._missions[m.id] = m
        except Exception:
            self._logger.exception("Failed loading persisted missions")
        else:
            # log number of missions loaded for diagnostics
            try:
                self._logger.info("Loaded %d missions from persistence", len(self._missions))
            except Exception:
                pass

        # start ticker after loading persisted state
        self._ticker = threading.Thread(target=self._ticker_loop, daemon=True)
        self._ticker.start()

    def shutdown(self):
        self._running = False
        try:
            if self._mqtt:
                self._mqtt.disconnect()
        except Exception:
            pass

    def start_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                self._logger.info("start_mission: mission %s not found", mission_id)
                return False
            if m.started:
                self._logger.info("start_mission: mission %s already started", mission_id)
                return False
            m.started = True
            m.paused = False
            self._logger.info("start_mission: mission %s started", mission_id)
        self._publish_state(mission_id)
        try:
            ok = self._persistence.save(list(self._missions.values()))
            if ok:
                self._logger.info("start_mission: persisted missions after starting %s", mission_id)
            else:
                self._logger.warning("start_mission: failed to persist missions after starting %s", mission_id)
        except Exception:
            self._logger.exception("Failed saving mission after start")
        return True

    def pause_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m or not m.started or m.paused:
                return False
            m.paused = True
        self._publish_state(mission_id)
        try:
            ok = self._persistence.save(list(self._missions.values()))
            if ok:
                self._logger.info("pause_mission: persisted missions after pausing %s", mission_id)
            else:
                self._logger.warning("pause_mission: failed to persist missions after pausing %s", mission_id)
        except Exception:
            self._logger.exception("Failed saving mission after pause")
        return True

    def resume_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m or not m.started or not m.paused:
                return False
            m.paused = False
            self._logger.info("resume_mission: mission %s resumed", mission_id)
        self._publish_state(mission_id)
        try:
            ok = self._persistence.save(list(self._missions.values()))
            if ok:
                self._logger.info("resume_mission: persisted missions after resuming %s", mission_id)
            else:
                self._logger.warning("resume_mission: failed to persist missions after resuming %s", mission_id)
        except Exception:
            self._logger.exception("Failed saving mission after resume")
        return True

    def stop_mission(self, mission_id: str) -> bool:
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                return False
            m.started = False
            m.paused = False
        self._publish_state(mission_id)
        try:
            ok = self._persistence.save(list(self._missions.values()))
            if ok:
                self._logger.info("stop_mission: persisted missions after stopping %s", mission_id)
            else:
                self._logger.warning("stop_mission: failed to persist missions after stopping %s", mission_id)
        except Exception:
            self._logger.exception("Failed saving mission after stop")
        return True

    def complete_task(self, mission_id: str, task_id: str) -> bool:
        changed = False
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                self._logger.info("complete_task: mission %s not found", mission_id)
                return False
            for t in m.tasks:
                if t.id == task_id:
                    t.completed = True
                    changed = True
                    break

        if changed:
            # publish and persist after releasing lock to avoid deadlock
            self._logger.info("complete_task: task %s marked complete in mission %s", task_id, mission_id)
            self._publish_state(mission_id)
            try:
                self._persistence.save(list(self._missions.values()))
            except Exception:
                self._logger.exception("Failed saving mission after complete_task")
            return True

        return False

    def set_task_completion(self, mission_id: str, task_id: str, completed: bool) -> bool:
        """Set the completed flag for a task to True or False."""
        changed = False
        with self._lock:
            m = self._missions.get(mission_id)
            if not m:
                self._logger.info("set_task_completion: mission %s not found", mission_id)
                return False
            for t in m.tasks:
                if t.id == task_id:
                    if t.completed != bool(completed):
                        t.completed = bool(completed)
                        changed = True
                    break

        if changed:
            self._logger.info("set_task_completion: task %s set to %s in mission %s", task_id, completed, mission_id)
            # publish and persist after releasing lock to avoid deadlock
            self._publish_state(mission_id)
            try:
                ok = self._persistence.save(list(self._missions.values()))
                if ok:
                    self._logger.info("set_task_completion: persisted missions after updating task %s", task_id)
                else:
                    self._logger.warning("set_task_completion: failed to persist missions after updating task %s", task_id)
            except Exception:
                self._logger.exception("Failed saving mission after set_task_completion")
            return True

        return False

    def _publish_state(self, mission_id: Optional[str] = None):
        payload = {}
        with self._lock:
            if mission_id:
                m = self._missions.get(mission_id)
                if not m:
                    return
                payload = {"mission": m.to_dict()}
            else:
                payload = {"missions": [m.to_dict() for m in self._missions.values()]}
        try:
            if self._mqtt:
                publish_state(self._mqtt, self.STATE_TOPIC, payload)
        except Exception:
            self._logger.exception("Failed publishing mission state to MQTT")

        # call local state-change callback if provided
        if self._state_change_callback:
            try:
                self._state_change_callback(payload)
            except Exception:
                self._logger.exception("State change callback raised an exception")

    def _on_mqtt_message(self, topic, payload):
        action = payload.get("action")
        if not action:
            return
        if action == "start":
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
                    # log mission state occasionally for diagnostics
                    try:
                        self._logger.debug("ticker: checking mission %s started=%s paused=%s elapsed=%s", m.id, m.started, m.paused, m.elapsed_seconds)
                    except Exception:
                        pass
                    if m.started and not m.paused:
                        m.elapsed_seconds += 1
                        updated.append(m.id)
            # publish state for each updated mission; persist once per tick
            if updated:
                try:
                    self._logger.info("ticker: updated missions %s", updated)
                except Exception:
                    pass
                for mid in updated:
                    self._publish_state(mid)
                try:
                    ok = self._persistence.save(list(self._missions.values()))
                    if ok:
                        self._logger.debug("ticker: persisted missions after update")
                    else:
                        self._logger.warning("ticker: failed to persist missions after update")
                except Exception:
                    self._logger.exception("Failed saving missions in ticker loop")


    def get_missions(self) -> List[Mission]:
        """Return the stored Mission model objects.

        The frontend expects a list of dicts, so callers that need
        serializable data (e.g. QML) should call `to_dict()` on each
        Mission. Keeping the manager API returning model objects makes
        server-side logic easier to test and reuse.
        """
        with self._lock:
            return list(self._missions.values())