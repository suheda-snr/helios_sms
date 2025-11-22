import json
import threading
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host="localhost", port=1883, client_id="mqtt-client"):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id, userdata=self)
        self.client_lock = threading.Lock()
        self.on_message_callback = None

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def connect(self):
        try:
            self.client.connect(self.host, self.port, 60)
        except Exception as e:
            print("MQTT connect error:", e)

    def loop_start(self):
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker, rc=", rc)
        # Subscribe to telemetry and commands so backend and frontends can communicate
        client.subscribe("tricorder/telemetry")
        client.subscribe("tricorder/commands")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except:
            print("MQTT decode error for topic:", msg.topic)
            return

        if self.on_message_callback:
            self.on_message_callback(msg.topic, payload)

    def publish(self, topic, payload):
        with self.client_lock:
            self.client.publish(topic, json.dumps(payload))
