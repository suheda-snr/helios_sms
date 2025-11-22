import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from telemetry.suit import TricorderBackend


class AlertManager:
    def __init__(self, backend):
        self.backend = backend
        self.sound = QSoundEffect()
        self._looping = False
        
        sound_path = backend.getAlertSoundPath()
        if sound_path:
            self.sound.setSource(QUrl.fromLocalFile(sound_path))
            self.sound.setVolume(0.9)
        
        backend.warningRaised.connect(self._update)
        backend.activeWarningsUpdated.connect(self._update)
    
    def _update(self, _=None):
        has_unacked = any(not w.get('acknowledged') 
                         for w in self.backend.getActiveWarnings())
        
        if has_unacked and not self._looping:
            self.sound.setLoopCount(QSoundEffect.Infinite)
            self.sound.play()
            self._looping = True
        elif not has_unacked and self._looping:
            self.sound.stop()
            self._looping = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    backend = TricorderBackend()
    alert_mgr = AlertManager(backend)
    
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    
    qml_file = Path(__file__).resolve().parents[1] / "frontend" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    if not engine.rootObjects():
        sys.exit(-1)
    
    sys.exit(app.exec())
