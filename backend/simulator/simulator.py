from PySide6.QtCore import QObject, Signal, Slot
from typing import Optional

from backend.simulator.suit_simulator import SuitSimulator


class SimulatorBackend(QObject):

    runningChanged = Signal(bool)

    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883, client_id: str = "tricorder-sim"):
        super().__init__()
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._client_id = client_id
        self._sim: Optional[SuitSimulator] = None
        self._running = False

    @Slot()
    def start(self):
        if self._running:
            return
        try:
            self._sim = SuitSimulator(broker_host=self._broker_host, broker_port=self._broker_port, client_id=self._client_id)
            self._sim.start()
            self._running = True
            self.runningChanged.emit(True)
        except Exception:
            self._sim = None

    @Slot()
    def stop(self):
        if not self._running or not self._sim:
            return
        try:
            self._sim.stop()
        except Exception:
            pass
        self._sim = None
        self._running = False
        self.runningChanged.emit(False)

    @Slot(str)
    def setClientId(self, client_id: str):
        # only allow changing client id when simulator is not running
        if self._running:
            return
        self._client_id = client_id

    @Slot(result=bool)
    def isRunning(self) -> bool:
        return self._running

    def shutdown(self):
        try:
            self.stop()
        except Exception:
            pass
