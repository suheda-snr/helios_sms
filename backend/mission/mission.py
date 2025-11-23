from PySide6.QtCore import QObject, Signal, Slot
from typing import Any

from backend.mission.manager import MissionManager
from backend.common.topics import TRICORDER_MISSION_COMMANDS, TRICORDER_MISSION_STATE
from backend.common.utils import qjs_to_py, safe_publish
from backend.mission.models import Mission


class MissionBackend(QObject):
    missionsUpdated = Signal()

    def __init__(self, mqtt_host=None, mqtt_port=1883, client_id=None):
        super().__init__()
        try:
            # Create manager without MQTT by default (simpler, single in-memory source)
            self._manager = MissionManager(mqtt_host, mqtt_port, client_id, state_change_callback=self._on_state_change)
            try:
                print(f"MissionBackend: created MissionManager, mqtt_configured={bool(getattr(self._manager, '_mqtt', None))}")
            except Exception:
                print("MissionBackend: created MissionManager")
        except Exception:
            self._manager = None

    def _on_state_change(self, payload: dict):
        try:
            self.missionsUpdated.emit()
        except Exception:
            pass

    @Slot('QVariant')
    def publishMissionCommand(self, payload: Any):
        try:
            py_payload = qjs_to_py(payload)
        except Exception:
            py_payload = payload
        try:
            if self._manager and getattr(self._manager, '_mqtt', None):
                # publish command via manager's mqtt
                safe_publish(self._manager._mqtt, TRICORDER_MISSION_COMMANDS, py_payload)
                return True
        except Exception:
            pass
        return False

    @Slot(result='QVariant')
    def getMissions(self):
        try:
            if self._manager:
                missions = self._manager.get_missions()
                try:
                    print(f"MissionBackend.getMissions: returning {len(missions)} missions")
                except Exception:
                    print("MissionBackend.getMissions: returning missions")
                return missions
        except Exception as e:
            print(f"Error fetching missions: {e}")
        return []

    @Slot(str, str, result=bool)
    def completeTask(self, mission_id: str, task_id: str):
        try:
            if self._manager:
                return self._manager.complete_task(mission_id, task_id)
        except Exception as e:
            print(f"Error completing task: {e}")
        return False

    @Slot(str, result=bool)
    def startMission(self, mission_id: str):
        try:
            print(f"MissionBackend.startMission called with mission_id={mission_id}")
            if self._manager:
                ok = self._manager.start_mission(mission_id)
                print(f"MissionBackend.startMission result={ok} for mission_id={mission_id}")
                return ok
        except Exception as e:
            print(f"Error in startMission: {e}")
        return False

    @Slot(str, result=bool)
    def pauseMission(self, mission_id: str):
        try:
            if self._manager:
                return self._manager.pause_mission(mission_id)
        except Exception:
            pass
        return False

    @Slot(str, result=bool)
    def resumeMission(self, mission_id: str):
        try:
            if self._manager:
                return self._manager.resume_mission(mission_id)
        except Exception:
            pass
        return False

    @Slot(str, result=bool)
    def stopMission(self, mission_id: str):
        try:
            if self._manager:
                return self._manager.stop_mission(mission_id)
        except Exception:
            pass
        return False

    @Slot(str, str, bool, result=bool)
    def markTaskComplete(self, mission_id: str, task_id: str, completed: bool):
        try:
            if self._manager:
                return self._manager.set_task_completion(mission_id, task_id, bool(completed))
        except Exception as e:
            print(f"Error in markTaskComplete: {e}")
        return False

    @Slot()
    def requestMissionState(self):
        try:
            if self._manager:
                self._manager._publish_state()
        except Exception:
            pass

    def shutdown(self):
        try:
            if self._manager:
                self._manager.shutdown()
        except Exception:
            pass
