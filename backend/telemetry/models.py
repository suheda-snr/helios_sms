from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Telemetry:
    o2: Optional[float] = None
    battery: Optional[float] = None
    co2: Optional[float] = None
    leak: Optional[bool] = None
    suit_temp: Optional[float] = None
    external_temp: Optional[float] = None
    timestamp: Optional[int] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return cls(
            o2=d.get("o2"),
            battery=d.get("battery"),
            co2=d.get("co2"),
            leak=d.get("leak"),
            suit_temp=d.get("suit_temp"),
            external_temp=d.get("external_temp"),
            timestamp=d.get("timestamp"),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "o2": self.o2,
            "battery": self.battery,
            "co2": self.co2,
            "leak": self.leak,
            "suit_temp": self.suit_temp,
            "external_temp": self.external_temp,
            "timestamp": self.timestamp,
        }
