import json
import threading
from typing import Optional, Callable, Dict, Any
import paho.mqtt.client as mqtt


class MQTTClient:
    DEFAULT_TOPIC = "tricorder/telemetry"
    
    def __init__(self, host="localhost", port=1883, client_id="mqtt-client"):
        self.host = host
        self.port = port
        self._client = mqtt.Client(client_id=client_id)
        self._lock = threading.Lock()
        self._connected = False
        self.on_message_callback = None
        
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def connect(self):
        try:
            self._client.connect(self.host, self.port, 60)
            return True
        except Exception as e:
            print(f"MQTT connect error: {e}")
            return False

    def disconnect(self):
        with self._lock:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def loop_start(self):
        self._client.loop_start()

    def is_connected(self):
        return self._connected

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"Connected to MQTT at {self.host}:{self.port}")
            client.subscribe(self.DEFAULT_TOPIC)
        else:
            print(f"Connection failed: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            print(f"Disconnected unexpectedly: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if self.on_message_callback:
                self.on_message_callback(msg.topic, payload)
        except Exception as e:
            print(f"Message error: {e}")

    def publish(self, topic, payload):
        if not self._connected:
            return False
        try:
            with self._lock:
                result = self._client.publish(topic, json.dumps(payload))
                return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"Publish error: {e}")
            return False
