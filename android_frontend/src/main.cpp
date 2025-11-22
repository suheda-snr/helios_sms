#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QDir>
#include <QFile>
#include <QCoreApplication>
#include <QDebug>
#include "tricorderbackend.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);

    TricorderBackend backend;

    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty("backend", &backend);

    // Locate the repository's `frontend/main.qml` by walking up parent directories
    QString qmlPath;
    {
        QString exeDir = QCoreApplication::applicationDirPath();
        QDir dir(exeDir);
        // walk up a few levels to find the frontend folder
        for (int i = 0; i < 8; ++i) {
            QString candidate = dir.filePath("frontend/main.qml");
            if (QFile::exists(candidate)) {
                qmlPath = QDir::toNativeSeparators(candidate);
                break;
            }
            if (!dir.cdUp()) break;
        }
    }

    if (qmlPath.isEmpty()) {
        qWarning() << "Could not locate frontend/main.qml relative to executable; expected to find the QML in a parent folder.";
        return -1;
    }

    engine.load(QUrl::fromLocalFile(qmlPath));
    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
