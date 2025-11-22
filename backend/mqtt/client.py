import json
import threading
import time
import logging
from typing import Any
import paho.mqtt.client as mqtt
try:
    from backend.common.topics import TRICORDER_TELEMETRY
except Exception:
    TRICORDER_TELEMETRY = "tricorder/telemetry"


class MQTTClient:
    DEFAULT_TOPIC = TRICORDER_TELEMETRY
    
    def __init__(self, host="localhost", port=1883, client_id="mqtt-client"):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._client = mqtt.Client(client_id=client_id)
        self._lock = threading.Lock()
        self._connected = False
        self._stop_reconnect = False
        self.on_message_callback = None
        self._reconnect_thread = None
        self._logger = logging.getLogger(__name__)
        
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def connect(self):
        try:
            self._logger.info("MQTT connecting to %s:%s as client_id=%s", self.host, self.port, getattr(self, 'client_id', '<unknown>'))
            self._client.connect(self.host, self.port, 60)
            # do not start loop here; callers may manage loop lifecycle
            self._stop_reconnect = False
            return True
        except Exception as e:
            self._logger.exception("MQTT connect error")
            return False

    def disconnect(self):
        # signal reconnect attempts to stop and disconnect cleanly
        self._stop_reconnect = True
        with self._lock:
            try:
                self._client.loop_stop()
            except Exception:
                pass
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._connected = False

    def loop_start(self):
        self._client.loop_start()

    def is_connected(self):
        return self._connected

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            self._logger.info("Connected to MQTT at %s:%s (client_id=%s)", self.host, self.port, getattr(self, 'client_id', '<unknown>'))
            client.subscribe(self.DEFAULT_TOPIC)
        else:
            self._logger.warning("Connection failed: %s (client_id=%s)", rc, getattr(self, 'client_id', '<unknown>'))

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            self._logger.warning("Disconnected unexpectedly: %s (client_id=%s)", rc, getattr(self, 'client_id', '<unknown>'))
            # start reconnect attempts in background
            if not self._stop_reconnect:
                self._start_reconnect_loop()

    def _start_reconnect_loop(self):
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return

        def _reconnect_loop():
            backoff = 1.0
            while not self._stop_reconnect:
                try:
                    self._logger.info("Attempting MQTT reconnect...")
                    with self._lock:
                        self._client.reconnect()
                    self._logger.info("MQTT reconnect succeeded")
                    return
                except Exception as e:
                    self._logger.debug("Reconnect failed: %s", e)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

        self._reconnect_thread = threading.Thread(target=_reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if self.on_message_callback:
                self.on_message_callback(msg.topic, payload)
        except Exception as e:
            self._logger.exception("Message error")

    def publish(self, topic, payload):
        if not self._connected:
            self._logger.debug("Publish skipped, not connected: %s", topic)
            return False
        try:
            with self._lock:
                result = self._client.publish(topic, json.dumps(payload))
                ok = result.rc == mqtt.MQTT_ERR_SUCCESS
                if not ok:
                    self._logger.warning("Publish returned error code: %s", result.rc)
                return ok
        except Exception:
            self._logger.exception("Publish error")
            return False
