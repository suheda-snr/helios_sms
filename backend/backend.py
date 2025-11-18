# app/backend.py
# PySide6 QObject that subscribes to MQTT topics and exposes signals/methods to QML.

import json
import os
import threading

from PySide6.QtCore import QObject, Signal, Slot, QTimer
import paho.mqtt.client as mqtt

TELEMETRY_TOPIC = "tricorder/telemetry"
MISSION_TOPIC = "tricorder/mission"
CONTROL_TOPIC = "tricorder/control"

class TricorderBackend(QObject):
    telemetryUpdated = Signal(dict)
    missionUpdated = Signal(dict)
    warningIssued = Signal(str)

    def __init__(self, broker_host="localhost", broker_port=1883, client_id="tricorder-app"):
        super().__init__()
        self.broker = broker_host
        self.port = broker_port
        self.client = mqtt.Client(client_id=client_id)
        # set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client_lock = threading.Lock()
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
        except Exception as e:
            print("MQTT connect failed:", e)
        # run MQTT network loop in background thread
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        print("Tricorder app connected to broker (rc=%s)" % rc)
        client.subscribe(TELEMETRY_TOPIC)
        client.subscribe(MISSION_TOPIC)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as e:
            print("Bad payload:", e)
            return
        if msg.topic == TELEMETRY_TOPIC:
            # emit telemetry
            self.telemetryUpdated.emit(payload)
            # check for simple warnings
            if payload.get("o2", 100) < 19:
                self.warningIssued.emit("LOW O2")
            if payload.get("battery", 100) < 15:
                self.warningIssued.emit("LOW BATTERY")
            if payload.get("leak"):
                self.warningIssued.emit("SUIT LEAK")
        elif msg.topic == MISSION_TOPIC:
            self.missionUpdated.emit(payload)
            # check for mission emergencies too
            if payload.get("emergency"):
                self.warningIssued.emit(payload.get("emergency"))

    @Slot()
    def startMission(self):
        msg = {"action": "start"}
        self._publish_control(msg)

    @Slot()
    def pauseMission(self):
        msg = {"action": "pause"}
        self._publish_control(msg)

    @Slot()
    def stopMission(self):
        msg = {"action": "stop"}
        self._publish_control(msg)

    @Slot(int)
    def markTaskComplete(self, task_id):
        msg = {"action": "mark_task", "task_id": int(task_id)}
        self._publish_control(msg)

    def _publish_control(self, msg):
        with self.client_lock:
            try:
                self.client.publish(CONTROL_TOPIC, json.dumps(msg))
            except Exception as e:
                print("Failed to publish control:", e)
