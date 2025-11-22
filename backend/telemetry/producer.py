import time


class WarningEngine:
    THRESHOLDS = {
        "o2_low": 19.0,
        "battery_low": 15.0,
        "co2_high": 1.0,
        "suit_temp_low": -20.0,
        "suit_temp_high": 45.0,
    }

    def __init__(self, thresholds=None):
        self.thresholds = {**self.THRESHOLDS, **(thresholds or {})}
        self.active_warnings = {}
        self.on_raise = None
        self.on_clear = None
        self.on_update = None

    def _raise_warning(self, wid, message, severity="critical"):
        if wid in self.active_warnings:
            self.active_warnings[wid]['last_seen'] = time.time()
            return

        warning = {
            'id': wid,
            'message': message,
            'severity': severity,
            'timestamp': time.time(),
            'acknowledged': False,
        }
        self.active_warnings[wid] = warning
        if self.on_raise:
            try:
                self.on_raise(warning)
            except Exception as e:
                print(f"Error in on_raise callback: {e}")
        if self.on_update:
            try:
                self.on_update()
            except Exception as e:
                print(f"Error in on_update callback: {e}")

    def _clear_warning(self, wid):
        if wid in self.active_warnings:
            del self.active_warnings[wid]
            if self.on_clear:
                try:
                    self.on_clear(wid)
                except Exception as e:
                    print(f"Error in on_clear callback: {e}")
            if self.on_update:
                try:
                    self.on_update()
                except Exception as e:
                    print(f"Error in on_update callback: {e}")

    def acknowledge(self, wid):
        if wid in self.active_warnings:
            self.active_warnings[wid]['acknowledged'] = True
            if self.on_update:
                try:
                    self.on_update()
                except Exception as e:
                    print(f"Error in on_update callback: {e}")

    def get_active_warnings(self):
        return list(self.active_warnings.values())

    def process(self, data):
        warnings = {}
        o2 = data.get('o2')
        battery = data.get('battery')
        co2 = data.get('co2')
        leak = data.get('leak')
        temp = data.get('suit_temp')
        
        if o2 is not None and o2 < self.thresholds['o2_low']:
            warnings['low_o2'] = (f"LOW O2 ({o2}%)", 'critical')
        if battery is not None and battery < self.thresholds['battery_low']:
            warnings['low_batt'] = (f"LOW BATTERY ({battery}%)", 'critical')
        if co2 is not None and co2 > self.thresholds['co2_high']:
            warnings['high_co2'] = (f"HIGH CO2 ({co2}%)", 'warning')
        if leak:
            warnings['suit_leak'] = ("SUIT LEAK DETECTED", 'critical')
        if temp is not None:
            if temp < self.thresholds['suit_temp_low']:
                warnings['temp_low'] = (f"TEMP LOW ({temp}°C)", 'warning')
            elif temp > self.thresholds['suit_temp_high']:
                warnings['temp_high'] = (f"TEMP HIGH ({temp}°C)", 'warning')
        
        # Consolidate leak + low O2
        if 'suit_leak' in warnings and 'low_o2' in warnings:
            warnings['atm_loss'] = ("ATMOSPHERE LOSS", 'critical')
            del warnings['low_o2']
            del warnings['suit_leak']
        
        for wid, (msg, sev) in warnings.items():
            self._raise_warning(wid, msg, sev)
        
        for wid in list(self.active_warnings.keys()):
            if wid not in warnings:
                self._clear_warning(wid)
