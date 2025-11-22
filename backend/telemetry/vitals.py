from typing import Dict, Tuple


def detect_warnings(telemetry: dict, thresholds: dict) -> Dict[str, Tuple[str, str]]:
    """Return a mapping of warning_id -> (message, severity) for given telemetry.

    This encapsulates the business rules for determining active warnings so
    the UI/backend code can remain small and focused on signal handling.
    """
    current = {}

    o2 = telemetry.get('o2')
    battery = telemetry.get('battery')
    co2 = telemetry.get('co2')
    leak = telemetry.get('leak')
    suit_temp = telemetry.get('suit_temp')

    if o2 is not None and o2 < thresholds.get('o2_low', 19.0):
        current['low_o2'] = (f"LOW O2 ({o2}%)", 'critical')

    if battery is not None and battery < thresholds.get('battery_low', 15.0):
        current['low_batt'] = (f"LOW BATTERY ({battery}%)", 'critical')

    if co2 is not None and co2 > thresholds.get('co2_high', 1.0):
        current['high_co2'] = (f"HIGH CO2 ({co2}%)", 'warning')

    if leak:
        current['suit_leak'] = ("SUIT LEAK DETECTED", 'critical')

    if suit_temp is not None:
        if suit_temp < thresholds.get('suit_temp_low', -20.0):
            current['temp_low'] = (f"SUIT TEMP LOW ({suit_temp}C)", 'warning')
        if suit_temp > thresholds.get('suit_temp_high', 45.0):
            current['temp_high'] = (f"SUIT TEMP HIGH ({suit_temp}C)", 'warning')

    # Compound condition: atmosphere loss when both leak and low O2
    if 'suit_leak' in current and 'low_o2' in current:
        current['atm_loss'] = ("ATMOSPHERE LOSS - LEAK", 'critical')
        current.pop('low_o2', None)
        current.pop('suit_leak', None)

    return current
