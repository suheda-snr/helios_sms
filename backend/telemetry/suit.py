from PySide6.QtCore import QObject, Signal
from mqtt.client import MQTTClient

TELEMETRY_TOPIC = "tricorder/telemetry"

class TricorderBackend(QObject):
    telemetryUpdated = Signal(dict)
    warningIssued = Signal(str)

    def __init__(self, broker_host="localhost", broker_port=1883, client_id="tricorder-app"):
        super().__init__()

        # MQTT setup
        self.mqtt = MQTTClient(broker_host, broker_port, client_id)
        self.mqtt.on_message_callback = self._on_message
        self.mqtt.connect()
        self.mqtt.loop_start()

    def _on_message(self, topic, payload):
        if topic == TELEMETRY_TOPIC:
            self.telemetryUpdated.emit(payload)
            self._check_warnings(payload)

    def _check_warnings(self, telemetry):
        if telemetry.get("o2", 100) < 19:
            self.warningIssued.emit("LOW O2")
        if telemetry.get("battery", 100) < 15:
            self.warningIssued.emit("LOW BATTERY")
        if telemetry.get("leak"):
            self.warningIssued.emit("SUIT LEAK DETECTED")
