import logging
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtMultimedia import QSoundEffect
try:
    import winsound
except Exception:
    winsound = None


class AlertManager:
    def __init__(self, backend):
        self.backend = backend
        self.sound = QSoundEffect()
        self._looping = False
        self._beep_timer = QTimer()
        self._beep_timer.setInterval(800)
        self._beep_timer.timeout.connect(self._play_once)

        sound_path = backend.getAlertSoundPath()
        if sound_path:
            self.sound.setSource(QUrl.fromLocalFile(sound_path))
            self.sound.setVolume(0.9)
            self._sound_path = sound_path
        
        backend.warningRaised.connect(self._update)
        backend.activeWarningsUpdated.connect(self._update)
    
    def _update(self, _=None):
        has_unacked = any(not w.get('acknowledged') 
                         for w in self.backend.getActiveWarnings())
        logging.debug("AlertManager._update called; has_unacked=%s", has_unacked)
        
        if has_unacked and not self._looping:
            # Start repeating short beeps
            self._play_once()
            self._beep_timer.start()
            self._looping = True
        elif not has_unacked and self._looping:
            self._beep_timer.stop()
            try:
                self.sound.stop()
            except Exception:
                logging.exception("QSoundEffect stop failed")
            try:
                if winsound is not None:
                    winsound.PlaySound(None, winsound.SND_ASYNC)
            except Exception:
                logging.exception("winsound stop failed")
            self._looping = False

    def _play_once(self):
        try:
            self.sound.play()
        except Exception:
            logging.exception("QSoundEffect play failed; attempting winsound fallback")
            if winsound is not None and getattr(self, '_sound_path', None):
                try:
                    winsound.PlaySound(self._sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                except Exception:
                    logging.exception("winsound PlaySound failed")
