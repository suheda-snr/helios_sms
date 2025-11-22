from PySide6.QtCore import QObject, Signal, Slot
from typing import Any

from backend.mission.manager import MissionManager
from backend.common.topics import TRICORDER_MISSION_COMMANDS, TRICORDER_MISSION_STATE
from backend.common.utils import qjs_to_py, safe_publish


class MissionBackend(QObject):
    missionsUpdated = Signal()

    def __init__(self, mqtt_host="localhost", mqtt_port=1883, client_id="mission-manager"):
        super().__init__()
        try:
            self._manager = MissionManager(mqtt_host, mqtt_port, client_id, state_change_callback=self._on_state_change)
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
            if self._manager:
                # publish command via manager's mqtt
                safe_publish(self._manager._mqtt, TRICORDER_MISSION_COMMANDS, py_payload)
        except Exception:
            pass

    @Slot(result='QVariant')
    def getMissions(self):
        try:
            if self._manager:
                with self._manager._lock:
                    return [m.__dict__ for m in self._manager._missions.values()]
        except Exception:
            pass
        return []

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
