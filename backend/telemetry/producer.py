from typing import Optional, Dict, Any, Callable
import time


class WarningEngine:
    """Processes telemetry and maintains active warnings.

    This is backend-agnostic logic: it keeps thresholds, raises/clears
    warnings and calls optional callbacks when events occur.
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        # default thresholds
        self.thresholds = thresholds or {
            "o2_low": 19.0,
            "battery_low": 15.0,
            "co2_high": 1.0,
            "suit_temp_low": -20.0,
            "suit_temp_high": 45.0,
        }

        # id -> info dict
        self.active_warnings: Dict[str, Dict[str, Any]] = {}

        # optional callbacks
        self.on_raise: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_clear: Optional[Callable[[str], None]] = None
        self.on_update: Optional[Callable[[], None]] = None

        # file logging removed per project settings (no warnings files)

    def _raise_warning(self, wid: str, message: str, severity: str = "critical", cause: Optional[str] = None):
        now = time.time()
        if wid in self.active_warnings:
            self.active_warnings[wid]['last_seen'] = now
            return

        info = {
            'id': wid,
            'message': message,
            'severity': severity,
            'cause': cause,
            'timestamp': now,
            'acknowledged': False,
        }
        self.active_warnings[wid] = info
        # callbacks
        try:
            if self.on_raise:
                self.on_raise(info)
        except Exception:
            pass
        try:
            if self.on_update:
                self.on_update()
        except Exception:
            pass
        # no file logging

    def _clear_warning(self, wid: str):
        if wid in self.active_warnings:
            # no file logging
            del self.active_warnings[wid]
            try:
                if self.on_clear:
                    self.on_clear(wid)
            except Exception:
                pass
            try:
                if self.on_update:
                    self.on_update()
            except Exception:
                pass

    def acknowledge(self, wid: str):
        if wid in self.active_warnings:
            self.active_warnings[wid]['acknowledged'] = True
            # no file logging
            if self.on_update:
                try:
                    self.on_update()
                except Exception:
                    pass

    def get_active_warnings(self):
        return list(self.active_warnings.values())

    def process(self, telemetry: Dict[str, Any]):
        # Determine current condition-based warnings
        current = {}

        o2 = telemetry.get('o2')
        battery = telemetry.get('battery')
        co2 = telemetry.get('co2')
        leak = telemetry.get('leak')
        suit_temp = telemetry.get('suit_temp')

        # LOW O2
        if o2 is not None and o2 < self.thresholds['o2_low']:
            current['low_o2'] = (f"LOW O2 ({o2}%)", 'critical')

        # LOW BATTERY
        if battery is not None and battery < self.thresholds['battery_low']:
            current['low_batt'] = (f"LOW BATTERY ({battery}%)", 'critical')

        # HIGH CO2
        if co2 is not None and co2 > self.thresholds['co2_high']:
            current['high_co2'] = (f"HIGH CO2 ({co2}%)", 'warning')

        # SUIT LEAK
        if leak:
            current['suit_leak'] = ("SUIT LEAK DETECTED", 'critical')

        # Temp extremes
        if suit_temp is not None:
            if suit_temp < self.thresholds['suit_temp_low']:
                current['temp_low'] = (f"SUIT TEMP LOW ({suit_temp}C)", 'warning')
            if suit_temp > self.thresholds['suit_temp_high']:
                current['temp_high'] = (f"SUIT TEMP HIGH ({suit_temp}C)", 'warning')

        # Root-cause example: if leak and low o2 => ATM LOSS: LEAK
        if 'suit_leak' in current and 'low_o2' in current:
            current['atm_loss'] = ("ATMOSPHERE LOSS - LEAK", 'critical')
            current.pop('low_o2', None)
            current.pop('suit_leak', None)

        # Raise new ones
        for key, (msg, sev) in current.items():
            self._raise_warning(key, msg, severity=sev, cause=None)

        # Clear warnings that are no longer present
        to_clear = [wid for wid in list(self.active_warnings.keys()) if wid not in current]
        for wid in to_clear:
            self._clear_warning(wid)
