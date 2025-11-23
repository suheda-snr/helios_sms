from typing import Any


def qjs_to_py(value: Any):
    try:
        if hasattr(value, 'toVariant'):
            return value.toVariant()
    except Exception:
        pass
    return value


def safe_publish(mqtt_client, topic: str, payload: Any) -> bool:
    try:
        py_payload = qjs_to_py(payload)
        mqtt_client.publish(topic, py_payload)
        return True
    except Exception:
        return False
