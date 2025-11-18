import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from telemetry.suit import TricorderBackend  # backend object for vitals

if __name__ == "__main__":
    app = QApplication(sys.argv)

    backend = TricorderBackend()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load("frontend/main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
