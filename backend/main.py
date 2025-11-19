import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from telemetry.suit import TricorderBackend  # backend object for vitals

if __name__ == "__main__":
    app = QApplication(sys.argv)

    backend = TricorderBackend()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)

    # Resolve QML path relative to the repository root (two levels up from this file)
    qml_file = Path(__file__).resolve().parents[1] / "frontend" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
