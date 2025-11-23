#pragma once

#include <QObject>
#include <QVariant>
#include <QVariantMap>
#include <QMap>
#include <QString>
#include <QTimer>
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
    Q_SIGNAL void missionsUpdated();
    Q_SIGNAL void missionProgress(const QVariant &mission);

    Q_INVOKABLE void acknowledgeWarning(const QString &id);
    Q_INVOKABLE QVariantList getActiveWarnings();
    Q_INVOKABLE void setBroker(const QString &host, int port = 1883);
    // Missions API (implemented to match Python backend expectations)
    Q_INVOKABLE QVariant createMission(const QString &name, const QVariant &durationSeconds, const QVariant &tasks, const QString &description = QString());
    Q_INVOKABLE void startMission(const QString &mid);
    Q_INVOKABLE void pauseMission(const QString &mid);
    Q_INVOKABLE void stopMission(const QString &mid);
    Q_INVOKABLE QVariantList getMissions();

private:
    void connectMqtt();
    void handleTelemetry(const QByteArray &payload);
    void checkWarnings(const QVariantMap &telemetry);

    // missions storage
    QMap<QString, QVariantMap> m_missions;
    QTimer* m_missionTimer = nullptr;
    void loadMissions();
    void saveMissions();

    QMqttClient* m_client = nullptr;
    QMap<QString, QVariantMap> m_activeWarnings;
    QVariantMap m_thresholds;
};
