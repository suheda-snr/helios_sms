import logging
from typing import Callable

logger = logging.getLogger(__name__)


def configure_client(mqtt_client, command_topic: str, on_message_callback: Callable):
    try:
        mqtt_client.DEFAULT_TOPIC = command_topic
        mqtt_client.on_message_callback = on_message_callback
    except Exception:
        logger.exception("Failed to configure MQTT client callbacks")


def start_loop_if_connected(mqtt_client):
    try:
        if mqtt_client.connect():
            try:
                mqtt_client.loop_start()
            except Exception:
                logger.exception("Failed to start MQTT loop")
    except Exception:
        logger.exception("MQTT client failed to connect")


def publish_state(mqtt_client, topic: str, payload: dict):
    try:
        mqtt_client.publish(topic, payload)
    except Exception:
        logger.exception("Failed publishing mission state to MQTT")
