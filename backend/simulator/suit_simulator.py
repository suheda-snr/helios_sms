import threading
import time
import random
from typing import Optional

import sys
import os

try:
    from backend.mqtt import MQTTClient
except Exception:
    # fallback for running this file directly as a script from the repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from mqtt import MQTTClient

TELEMETRY_TOPIC = "tricorder/telemetry"


class SuitSimulator:
    #Simulator that publishes periodic telemetry over MQTT.

    def __init__(self, mqtt_client: Optional[MQTTClient] = None, *,
                 broker_host: str = "localhost", broker_port: int = 1883,
                 client_id: str = "tricorder-sim"):
        # allow injecting an existing client
        if mqtt_client is not None:
            self.mqtt = mqtt_client
        else:
            self.mqtt = MQTTClient(broker_host, broker_port, client_id)
            # connect automatically for the simple run case
            try:
                self.mqtt.connect()
                self.mqtt.loop_start()
            except Exception:
                pass

        # Initial vitals
        self.o2 = 98.0
        self.co2 = 0.04
        self.suit_temp = 20.0
        self.external_temp = -40.0
        self.battery = 95.0
        self.leak = False

        self.telemetry_interval = 1.0
        self.running = False
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._telemetry_loop, daemon=True)

    def start(self):
        if not self.running:
            self.running = True
            if not self.thread.is_alive():
                self.thread = threading.Thread(target=self._telemetry_loop, daemon=True)
                self.thread.start()

    def stop(self, timeout: float = 2.0):
        self.running = False
        try:
            if self.thread.is_alive():
                self.thread.join(timeout)
        except Exception:
            pass

    def _telemetry_loop(self):
        while self.running:
            self._simulate_tick()
            payload = {
                "o2": round(self.o2, 2),
                "co2": round(self.co2, 3),
                "suit_temp": round(self.suit_temp, 2),
                "external_temp": round(self.external_temp, 2),
                "battery": round(self.battery, 2),
                "leak": self.leak,
                "timestamp": int(time.time())
            }
            try:
                self.mqtt.publish(TELEMETRY_TOPIC, payload)
            except Exception:
                # publishing should not crash simulator loop
                pass
            time.sleep(self.telemetry_interval)

    def _simulate_tick(self):
        if not self.leak:
            self.o2 += random.uniform(-0.2, 0.2)
            self.co2 += random.uniform(-0.05, 0.05)
        else:
            self.o2 -= random.uniform(0.1, 0.8)
            self.co2 += random.uniform(0.01, 0.1)

        self.battery -= random.uniform(0.01, 0.05)
        if random.random() < 0.001:
            self.battery -= random.uniform(5, 20)

        self.suit_temp += random.uniform(-0.02, 0.02)
        self.external_temp += random.uniform(-0.1, 0.1)

        if self.battery < 20 and random.random() < 0.02:
            self.leak = True

        # clamp values
        self.o2 = max(0.0, min(100.0, self.o2))
        self.co2 = max(0.0, self.co2)
        self.battery = max(0.0, self.battery)


if __name__ == "__main__":
    sim = SuitSimulator()
    sim.start()
    print("Suit simulator running... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
        print("Simulator stopped.")
