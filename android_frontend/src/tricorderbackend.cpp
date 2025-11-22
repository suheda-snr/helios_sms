#include "tricorderbackend.h"
#include <QtMqtt/QMqttClient>
#include <QtMqtt/QMqttSubscription>
#include <QtMqtt/QMqttTopicName>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QTimer>
#include <QDebug>

TricorderBackend::TricorderBackend(QObject* parent)
    : QObject(parent)
{
    m_thresholds["o2_low"] = 19.0;
    m_thresholds["battery_low"] = 15.0;
    m_thresholds["co2_high"] = 1.0;

    connectMqtt();
}

void TricorderBackend::connectMqtt()
{
    m_client = new QMqttClient(this);

    // Pick broker from environment variables if provided (useful for device testing)
    QByteArray envHost = qgetenv("TRICORDER_MQTT_HOST");
    QByteArray envPort = qgetenv("TRICORDER_MQTT_PORT");
    if (!envHost.isEmpty()) {
        m_client->setHostname(QString::fromUtf8(envHost));
    } else {
        m_client->setHostname("localhost");
    }
    bool ok = false;
    int port = 1883;
    if (!envPort.isEmpty()) {
        port = envPort.toInt(&ok);
        if (!ok) port = 1883;
    }
    m_client->setPort(port);

    connect(m_client, &QMqttClient::connected, this, [this]() {
        qDebug() << "MQTT connected";
        auto sub = m_client->subscribe(QMqttTopicFilter(QStringLiteral("tricorder/telemetry")));
        Q_UNUSED(sub);
    });

    connect(m_client, &QMqttClient::messageReceived, this, [this](const QByteArray &message, const QMqttTopicName &topic){
        Q_UNUSED(topic);
        handleTelemetry(message);
    });

    m_client->connectToHost();
}

void TricorderBackend::handleTelemetry(const QByteArray &payload)
{
    QJsonParseError err;
    QJsonDocument doc = QJsonDocument::fromJson(payload, &err);
    if (err.error != QJsonParseError::NoError) {
        qWarning() << "MQTT payload JSON parse error:" << err.errorString();
        return;
    }

    QVariantMap map = doc.object().toVariantMap();
    emit telemetryUpdated(QVariant::fromValue(map));
    checkWarnings(map);
}

void TricorderBackend::checkWarnings(const QVariantMap &telemetry)
{
    // simple mirroring of Python logic: thresholds + active map
    QVariant o2v = telemetry.value("o2");
    QVariant battv = telemetry.value("battery");
    QVariant co2v = telemetry.value("co2");
    QVariant leakv = telemetry.value("leak");

    QMap<QString, QPair<QString, QString>> current; // id -> (msg, severity)

    double o2 = o2v.isNull() ? std::numeric_limits<double>::infinity() : o2v.toDouble();
    double batt = battv.isNull() ? std::numeric_limits<double>::infinity() : battv.toDouble();
    double co2 = co2v.isNull() ? 0.0 : co2v.toDouble();
    bool leak = leakv.toBool();

    if (o2 < m_thresholds["o2_low"].toDouble()) current["low_o2"] = qMakePair(QString("LOW O2 (%1%)").arg(o2), QString("critical"));
    if (batt < m_thresholds["battery_low"].toDouble()) current["low_batt"] = qMakePair(QString("LOW BATTERY (%1%)").arg(batt), QString("critical"));
    if (co2 > m_thresholds["co2_high"].toDouble()) current["high_co2"] = qMakePair(QString("HIGH CO2 (%1%)").arg(co2), QString("warning"));
    if (leak) current["suit_leak"] = qMakePair(QString("SUIT LEAK DETECTED"), QString("critical"));

    if (current.contains("suit_leak") && current.contains("low_o2")) {
        current["atm_loss"] = qMakePair(QString("ATMOSPHERE LOSS - LEAK"), QString("critical"));
        current.remove("suit_leak");
        current.remove("low_o2");
    }

    // Raise new warnings
    for (auto it = current.constBegin(); it != current.constEnd(); ++it) {
        QString id = it.key();
        if (!m_activeWarnings.contains(id)) {
            QVariantMap info;
            info["id"] = id;
            info["message"] = it.value().first;
            info["severity"] = it.value().second;
            info["timestamp"] = QDateTime::currentSecsSinceEpoch();
            info["acknowledged"] = false;
            m_activeWarnings[id] = info;
            emit warningRaised(QVariant::fromValue(info));
            emit warningIssued(info["message"].toString());
            emit activeWarningsUpdated();
        }
    }

    // Clear missing warnings
    QList<QString> toClear;
    for (auto it = m_activeWarnings.begin(); it != m_activeWarnings.end(); ++it) {
        if (!current.contains(it.key())) toClear.append(it.key());
    }
    for (const QString &id : toClear) {
        m_activeWarnings.remove(id);
        emit warningCleared(id);
        emit activeWarningsUpdated();
    }
}

void TricorderBackend::acknowledgeWarning(const QString &id)
{
    if (m_activeWarnings.contains(id)) {
        m_activeWarnings[id]["acknowledged"] = true;
        emit activeWarningsUpdated();
        // also publish ack back to commands topic so remote backend can log/store it
        if (m_client && m_client->state() == QMqttClient::Connected) {
            QJsonObject obj;
            obj["type"] = "ack";
            obj["id"] = id;
            QJsonDocument doc(obj);
            m_client->publish(QMqttTopicName(QStringLiteral("tricorder/commands")), doc.toJson());
        }
    }
}

QVariantList TricorderBackend::getActiveWarnings()
{
    QVariantList list;
    for (auto it = m_activeWarnings.begin(); it != m_activeWarnings.end(); ++it) list.append(it.value());
    return list;

}

void TricorderBackend::setBroker(const QString &host, int port)
{
    if (!m_client) return;
    // If connected, disconnect first
    if (m_client->state() == QMqttClient::Connected) {
        m_client->disconnectFromHost();
    }
    m_client->setHostname(host);
    m_client->setPort(port);
    m_client->connectToHost();
}
