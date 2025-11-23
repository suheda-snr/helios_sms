from PySide6.QtCore import QObject, Signal, Slot
from typing import Any
import logging

from backend.mission.manager import MissionManager
from backend.mission.models import Mission

logger = logging.getLogger(__name__)


class MissionBackend(QObject):
    missionsUpdated = Signal()

    def __init__(self, mqtt_host=None, mqtt_port=1883, client_id=None):
        super().__init__()
        try:
            # Create manager without MQTT by default (simpler, single in-memory source)
            self._manager = MissionManager(mqtt_host, mqtt_port, client_id, state_change_callback=self._on_state_change)
            try:
                logger.debug("MissionBackend: created MissionManager, mqtt_configured=%s", bool(getattr(self._manager, '_mqtt', None)))
            except Exception:
                logger.debug("MissionBackend: created MissionManager")
        except Exception:
            logger.exception("Failed to create MissionManager")
            self._manager = None

    def _on_state_change(self, payload: dict):
        try:
            self.missionsUpdated.emit()
        except Exception:
            pass

    @Slot(result='QVariant')
    def getMissions(self):
        try:
            if self._manager:
                missions = self._manager.get_missions()
                try:
                    logger.debug("MissionBackend.getMissions: returning %d missions", len(missions))
                except Exception:
                    logger.debug("MissionBackend.getMissions: returning missions")
                # Convert model objects to serializable dicts for QML
                return [m.to_dict() for m in missions]
        except Exception:
            logger.exception("Error fetching missions")
        return []

    @Slot(str, str, result=bool)
    def completeTask(self, mission_id: str, task_id: str):
        try:
            if self._manager:
                return self._manager.complete_task(mission_id, task_id)
        except Exception:
            logger.exception("Error completing task")
        return False

    @Slot(str, result=bool)
    def startMission(self, mission_id: str):
        try:
            if self._manager:
                ok = self._manager.start_mission(mission_id)
                # manager logs started at INFO level; keep backend quiet
                return ok
        except Exception:
            logger.exception("Error in startMission")
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
        except Exception:
            logger.exception("Error in markTaskComplete")
        return False

    def shutdown(self):
        try:
            if self._manager:
                self._manager.shutdown()
        except Exception:
            pass
