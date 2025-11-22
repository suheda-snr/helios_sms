#pragma once

#include <QObject>
#include <QVariant>
#include <QMap>
#include <QString>
#include <QtMqtt/QMqttClient>
#include <QtMqtt/QMqttTopicName>

class TricorderBackend : public QObject {
    Q_OBJECT
public:
    explicit TricorderBackend(QObject* parent = nullptr);
    ~TricorderBackend() override = default;

    Q_SIGNAL void telemetryUpdated(const QVariant &payload);
    Q_SIGNAL void warningIssued(const QString &msg);
    Q_SIGNAL void warningRaised(const QVariant &warningDict);
    Q_SIGNAL void warningCleared(const QString &id);
    Q_SIGNAL void activeWarningsUpdated();

    Q_INVOKABLE void acknowledgeWarning(const QString &id);
    Q_INVOKABLE QVariantList getActiveWarnings();
    Q_INVOKABLE void setBroker(const QString &host, int port = 1883);

private:
    void connectMqtt();
    void handleTelemetry(const QByteArray &payload);
    void checkWarnings(const QVariantMap &telemetry);

    QMqttClient* m_client = nullptr;
    QMap<QString, QVariantMap> m_activeWarnings;
    QVariantMap m_thresholds;
};
