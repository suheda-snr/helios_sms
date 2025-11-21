from PySide6.QtCore import QObject, Signal, Slot
import time
import uuid

class MissionManager(QObject):
    """Simple in-memory mission manager exposed to QML.

    Mission dict structure:
      id: str
      name: str
      duration: int (seconds planned)
      max_duration: int (seconds) or null
      tasks: [ { id, name, description, projected_duration, completed } ]
      state: 'stopped'|'running'|'paused'
      start_time: timestamp or None
      paused_at: timestamp when paused or None
      elapsed: seconds of elapsed runtime (computed)
      created_at: timestamp
    """

    missionsChanged = Signal()
    missionUpdated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._missions = {}

    def _now(self):
        return time.time()

    def _make_id(self):
        return str(uuid.uuid4())

    @Slot(result='QVariant')
    def listMissions(self):
        return list(self._missions.values())

    @Slot(str, int, int, result='QString')
    def createMission(self, name, duration, max_duration=0):
        mid = self._make_id()
        mission = {
            'id': mid,
            'name': name,
            'duration': int(duration),
            'max_duration': int(max_duration) if max_duration else None,
            'tasks': [],
            'state': 'stopped',
            'start_time': None,
            'paused_at': None,
            'elapsed': 0,
            'created_at': self._now(),
        }
        self._missions[mid] = mission
        self.missionsChanged.emit()
        return mid

    @Slot(str, result='QVariant')
    def getMission(self, mid):
        m = self._missions.get(mid)
        if not m:
            return None
        # compute current elapsed
        elapsed = m.get('elapsed', 0)
        if m.get('state') == 'running' and m.get('start_time'):
            elapsed += int(self._now() - m['start_time'])
        return {**m, 'elapsed': elapsed}

    @Slot(str, str, str, int, result='QString')
    def addTask(self, mid, name, description, projected_duration=0):
        m = self._missions.get(mid)
        if not m:
            return ''
        tid = self._make_id()
        task = {
            'id': tid,
            'name': name,
            'description': description,
            'projected_duration': int(projected_duration),
            'completed': False,
        }
        m['tasks'].append(task)
        self.missionUpdated.emit(m)
        return tid

    @Slot(str, result=bool)
    def startMission(self, mid):
        m = self._missions.get(mid)
        if not m:
            return False
        if m['state'] == 'running':
            return True
        # if paused, don't reset elapsed; else ensure elapsed set
        if m['state'] == 'paused' and m.get('paused_at'):
            # resume
            m['start_time'] = self._now() - m.get('elapsed', 0)
        else:
            m['start_time'] = self._now()
            m['elapsed'] = 0
        m['state'] = 'running'
        m['paused_at'] = None
        self.missionUpdated.emit(m)
        return True

    @Slot(str, result=bool)
    def pauseMission(self, mid):
        m = self._missions.get(mid)
        if not m or m['state'] != 'running':
            return False
        # capture elapsed
        if m.get('start_time'):
            m['elapsed'] = int(self._now() - m['start_time'])
        m['state'] = 'paused'
        m['paused_at'] = self._now()
        m['start_time'] = None
        self.missionUpdated.emit(m)
        return True

    @Slot(str, result=bool)
    def stopMission(self, mid):
        m = self._missions.get(mid)
        if not m:
            return False
        # finalize elapsed
        if m.get('state') == 'running' and m.get('start_time'):
            m['elapsed'] = int(self._now() - m['start_time'])
        m['state'] = 'stopped'
        m['start_time'] = None
        m['paused_at'] = None
        self.missionUpdated.emit(m)
        return True

    @Slot(str, str, bool, result=bool)
    def setTaskCompleted(self, mid, tid, completed):
        m = self._missions.get(mid)
        if not m:
            return False
        for t in m['tasks']:
            if t['id'] == tid:
                t['completed'] = bool(completed)
                self.missionUpdated.emit(m)
                return True
        return False

    @Slot(result='QVariant')
    def getAllWithProgress(self):
        # return missions with computed elapsed
        out = []
        for m in self._missions.values():
            elapsed = m.get('elapsed', 0)
            if m.get('state') == 'running' and m.get('start_time'):
                elapsed += int(self._now() - m['start_time'])
            out.append({**m, 'elapsed': elapsed})
        return out
