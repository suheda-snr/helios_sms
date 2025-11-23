import json
import os
import logging
from typing import List, Dict, Any, Optional

from .models import Mission, Task

logger = logging.getLogger(__name__)


class PersistenceManager:
    def __init__(self, persistence_file: Optional[str]):
        self.path = persistence_file

    def save(self, missions: List[Mission]):
        if not self.path:
            logger.debug("PersistenceManager.save: no path configured, skipping save")
            return False
        try:
            data = [m.to_dict() for m in missions]
            d = os.path.dirname(self.path)
            if d and not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved %d missions to %s", len(missions), self.path)
            return True
        except Exception:
            logger.exception("Failed saving missions to file: %s", self.path)
            return False

    def load(self) -> List[Mission]:
        result: List[Mission] = []
        if not self.path or not os.path.exists(self.path):
            return result
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            # If raw is a list of task dicts (legacy), wrap into one mission
            if isinstance(raw, list) and raw and all(isinstance(i, dict) for i in raw):
                first = raw[0]
                if 'title' in first and 'name' not in first and 'tasks' not in first:
                    m = Mission(id=str(os.urandom(16).hex()), name="Imported Mission")
                    for t in raw:
                        try:
                            m.tasks.append(Task.from_dict(t))
                        except Exception:
                            logger.exception("Skipping invalid task entry during load")
                    result.append(m)
                    return result
                # Otherwise decode as list of missions
                for item in raw:
                    try:
                        result.append(Mission.from_dict(item))
                    except Exception:
                        logger.exception("Skipping invalid mission entry during load")
        except Exception:
            logger.exception("Failed loading missions from file: %s", self.path)
        return result
