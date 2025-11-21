import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import Qt

from telemetry.suit import TricorderBackend  # backend object for vitals

if __name__ == "__main__":
    app = QApplication(sys.argv)

    backend = TricorderBackend()
    # Debug: report mission manager status for troubleshooting
    try:
        mm = getattr(backend, 'missionManager', None)
        if mm:
            try:
                missions = mm.getAllWithProgress()
            except Exception:
                try:
                    missions = mm.listMissions()
                except Exception:
                    missions = None
            print("MissionManager present. Missions:", missions)
        else:
            print("MissionManager not available on backend")
    except Exception as e:
        print("Error checking missionManager:", e)

    # Setup a short QSoundEffect to play alert sounds when backend raises warnings.
    alert_sound = QSoundEffect()
    try:
        sound_path = backend.getAlertSoundPath()
        if sound_path:
            alert_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
    except Exception:
        pass
    alert_sound.setVolume(0.9)

    # Connect backend signal to play the alert
    # Track whether alert is currently looping
    _alert_looping = {'value': False}

    def _ensure_sound_source():
        try:
            sp = backend.getAlertSoundPath()
            if sp:
                alert_sound.setSource(QUrl.fromLocalFile(str(sp)))
        except Exception:
            pass

    def _update_alert_loop():
        """Enable looping if any active warning is unacknowledged; stop otherwise."""
        try:
            active = backend.getActiveWarnings()
            any_unacked = any((not w.get('acknowledged')) for w in active)
            _ensure_sound_source()
            if any_unacked:
                # start looping
                try:
                    alert_sound.setLoopCount(QSoundEffect.Infinite)
                except Exception:
                    try:
                        alert_sound.setLoopCount(-1)
                    except Exception:
                        pass
                try:
                    alert_sound.play()
                except Exception:
                    pass
                _alert_looping['value'] = True
            else:
                # stop looping
                if _alert_looping['value']:
                    try:
                        alert_sound.stop()
                    except Exception:
                        pass
                    _alert_looping['value'] = False
        except Exception:
            pass

    def _on_warning_raised(info):
        # On any new warning, recompute loop state (will loop if any unacked warnings exist)
        _update_alert_loop()

    try:
        backend.warningRaised.connect(_on_warning_raised)
    except Exception:
        pass

    # When active warnings change, stop looping sound if no critical unacknowledged remain
    def _on_active_warnings_updated():
        try:
            active = backend.getActiveWarnings()
            critical_unacked = any((w.get('severity') == 'critical' and not w.get('acknowledged')) for w in active)
            if not critical_unacked and _alert_looping['value']:
                try:
                    alert_sound.stop()
                except Exception:
                    pass
                _alert_looping['value'] = False
        except Exception:
            pass

    try:
        backend.activeWarningsUpdated.connect(_on_active_warnings_updated)
    except Exception:
        pass

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    # Expose mission manager as a separate context property so QML can use it directly
    try:
        if getattr(backend, 'missionManager', None):
            engine.rootContext().setContextProperty("missionManager", backend.missionManager)
    except Exception:
        pass

    # Resolve QML path relative to the repository root (two levels up from this file)
    qml_file = Path(__file__).resolve().parents[1] / "frontend" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
