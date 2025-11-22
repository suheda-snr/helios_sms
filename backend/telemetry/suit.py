from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path
from .helpers import _make_beep, logger

try:
    from backend.mqtt import MQTTClient
except ImportError:
    from mqtt import MQTTClient

from .producer import WarningEngine





class TricorderBackend(QObject):

    telemetryUpdated = Signal(dict)
    warningIssued = Signal(str)
    warningRaised = Signal(dict)
    warningCleared = Signal(str)
    activeWarningsUpdated = Signal()

    def __init__(self, broker_host="localhost", broker_port=1883, client_id="tricorder-app"):
        super().__init__()

        # Create alert sound
        backend_dir = Path(__file__).resolve().parents[1]
        assets_dir = backend_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        self._alert_sound = assets_dir / "warning.wav"
        if not self._alert_sound.exists():
            try:
                _make_beep(self._alert_sound)
            except Exception:
                # _make_beep already logged; continue without crashing the UI
                pass

        # Warning engine
        self.engine = WarningEngine()
        # use explicit methods instead of lambdas for clarity
        def _on_raise(info: dict):
            try:
                # Emit a short string for simple UI handlers
                self.warningIssued.emit(info.get('message', ''))
            except Exception:
                logger.exception("Error emitting warningIssued")
            try:
                # Emit structured warning for other consumers
                self.warningRaised.emit(info)
            except Exception:
                logger.exception("Error emitting warningRaised")

        def _on_clear(wid: str):
            try:
                self.warningCleared.emit(wid)
            except Exception:
                logger.exception("Error emitting warningCleared")

        def _on_update():
            try:
                self.activeWarningsUpdated.emit()
            except Exception:
                logger.exception("Error emitting activeWarningsUpdated")

        self.engine.on_raise = _on_raise
        self.engine.on_clear = _on_clear
        self.engine.on_update = _on_update

        # MQTT connection
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        if self.mqtt.connect():
            self.mqtt.loop_start()

    def _on_message(self, topic, payload):
        logger.debug("Telemetry: %s", payload)
        try:
            self.telemetryUpdated.emit(payload)
        except Exception:
            logger.exception("Error emitting telemetryUpdated")
        try:
            self.engine.process(payload)
        except Exception:
            logger.exception("Error processing telemetry payload")

    @Slot(str)
    def acknowledgeWarning(self, wid):
        self.engine.acknowledge(wid)

    @Slot(result='QVariant')
    def getActiveWarnings(self):
        return self.engine.get_active_warnings()

    @Slot(result=str)
    def getAlertSoundPath(self):
        return str(self._alert_sound)

    def shutdown(self):
        try:
            if getattr(self, 'mqtt', None):
                self.mqtt.disconnect()
        except Exception:
            logger.exception("Error during backend shutdown")
