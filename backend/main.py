import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from pathlib import Path as _Path
import sys as _sys

_repo_root = _Path(__file__).resolve().parents[1]
if str(_repo_root) not in _sys.path:
    _sys.path.insert(0, str(_repo_root))

from backend.alert_manager import AlertManager
from backend.telemetry.suit import TricorderBackend


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        QQuickStyle.setStyle('Basic')
    except Exception:
        pass
    app = QApplication(sys.argv)
    backend = TricorderBackend()
    alert_mgr = AlertManager(backend)
    
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    
    qml_file = Path(__file__).resolve().parents[1] / "frontend" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    if not engine.rootObjects():
        sys.exit(-1)
    # ensure backend cleans up MQTT on application exit
    try:
        app.aboutToQuit.connect(backend.shutdown)
    except Exception:
        pass

    sys.exit(app.exec())
