import sys
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtCore import QUrl

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    # Create QQuickView
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile("main.qml"))

    # Make the root object resize with the view
    view.setResizeMode(QQuickView.SizeRootObjectToView)

    # Show the window
    view.show()

    sys.exit(app.exec())
