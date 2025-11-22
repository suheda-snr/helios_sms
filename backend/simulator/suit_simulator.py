import threading
import time
import random
import sys
import os
import socket

try:
    from backend.mqtt import MQTTClient
except ImportError:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from mqtt import MQTTClient


class SuitSimulator:
    # Sensor limits
    LOW_BATTERY_THRESHOLD = 20.0
    LEAK_PROBABILITY = 0.02
    BATTERY_SPIKE_CHANCE = 0.001
    
    def __init__(self, mqtt_client=None, broker_host="localhost", 
                 broker_port=1883, client_id="tricorder-sim", interval=1.0):
        self.mqtt = mqtt_client or MQTTClient(broker_host, broker_port, client_id)
        if not mqtt_client and self.mqtt.connect():
            self.mqtt.loop_start()
        
        self.o2, self.co2 = 98.0, 0.04
        self.suit_temp, self.external_temp = 20.0, -40.0
        self.battery, self.leak = 95.0, False
        self.telemetry_interval = interval
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self, timeout=0.5):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout)

    def _run(self):
        while self._running:
            self._update_sensors()
            self.mqtt.publish("tricorder/telemetry", {
                "o2": round(self.o2, 2),
                "co2": round(self.co2, 3),
                "suit_temp": round(self.suit_temp, 2),
                "external_temp": round(self.external_temp, 2),
                "battery": round(self.battery, 2),
                "leak": self.leak,
                "timestamp": int(time.time())
            })
            time.sleep(self.telemetry_interval)

    def _update_sensors(self):
        if not self.leak:
            self.o2 -= random.uniform(0.01, 0.05)
            self.co2 += random.uniform(-0.01, 0.05)
        else:
            self.o2 -= random.uniform(0.3, 1.0)
            self.co2 += random.uniform(0.05, 0.15)

        self.battery -= random.uniform(0.01, 0.05)
        if random.random() < self.BATTERY_SPIKE_CHANCE:
            self.battery -= random.uniform(5, 20)

        self.suit_temp += random.uniform(-0.02, 0.02)
        self.external_temp += random.uniform(-0.1, 0.1)

        if self.battery < self.LOW_BATTERY_THRESHOLD and random.random() < self.LEAK_PROBABILITY:
            self.leak = True

        self.o2 = max(0, min(100, self.o2))
        self.co2 = max(0, self.co2)
        self.battery = max(0, self.battery)


if __name__ == "__main__":
    def _acquire_lock(port=50000):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('127.0.0.1', port))
            s.listen(1)
            return s
        except OSError:
            return None

    lock = _acquire_lock()
    if not lock:
        print("Simulator is already running in another terminal. Only one instance allowed.")
        sys.exit(1)

    sim = SuitSimulator()
    sim.start()
    print("Simulator running... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        sim._running = False
        print("Stopped.")
    finally:
        try:
            lock.close()
        except Exception:
            pass
