import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    property var warning: ({})
    signal acknowledge(string id)

    width: parent ? parent.width : 200
    height: 56
    radius: 6
    color: warning && !warning.acknowledged && warning.severity === 'critical' ? Qt.rgba(0.35,0.05,0.05,0.95) : Qt.rgba(0.06,0.02,0.02,0.6)
    border.color: warning && (warning.severity === 'critical' ? '#ff4444' : '#ffcc66')

    RowLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 8

        ColumnLayout {
            Layout.fillWidth: true
            Text {
                text: warning && warning.message ? warning.message : ""
                color: '#ffecec'
                font.pixelSize: 12
                elide: Text.ElideRight
            }
            Text {
                text: warning && warning.severity ? warning.severity.toUpperCase() : ''
                color: '#ffcccc'
                font.pixelSize: 10
            }
        }

        Button {
            id: ackBtn
            text: warning && warning.acknowledged ? '\u2713 ACK' : (warning && warning.severity === 'critical' ? 'CLICK TO SILENCE' : 'Acknowledge')
            enabled: !(warning && warning.acknowledged)
            font.pixelSize: 12
            implicitWidth: 110
            implicitHeight: 34
            contentItem: Text {
                text: control.text
                color: control.enabled ? "#ffffff" : "#eeeeee"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.bold: true
            }
            background: Rectangle {
                id: bgRect
                radius: 8
                color: warning && warning.acknowledged ? "#2e7d32" : (warning && warning.severity === 'critical' ? "#d32f2f" : "#ff9800")
                border.color: Qt.darker(color, 1.25)
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.lighter(bgRect.color, 1.05) }
                    GradientStop { position: 1; color: bgRect.color }
                }
                // Glow for critical unacked
                Rectangle {
                    id: glowRect
                    anchors.centerIn: parent
                    width: parent.width + (warning && warning.severity === 'critical' && !(warning && warning.acknowledged) ? 14 : 0)
                    height: parent.height + (warning && warning.severity === 'critical' && !(warning && warning.acknowledged) ? 14 : 0)
                    radius: parent.radius + 6
                    color: warning && warning.severity === 'critical' && !(warning && warning.acknowledged) ? Qt.rgba(1,0.15,0.15,0.18) : Qt.rgba(0,0,0,0)
                    z: -1
                    Behavior on color { ColorAnimation { duration: 350 } }
                    Behavior on width { NumberAnimation { duration: 350 } }
                    Behavior on height { NumberAnimation { duration: 350 } }
                }
            }
            // pulse animation on the button when critical and unacknowledged
            SequentialAnimation on scale {
                running: warning && warning.severity === 'critical' && !(warning && warning.acknowledged)
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.05; duration: 500; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 1.05; to: 1.0; duration: 500; easing.type: Easing.InOutQuad }
            }
            onClicked: {
                if (warning && warning.id) {
                    root.acknowledge(warning.id)
                    // immediate local feedback while backend processes
                    warning.acknowledged = true
                }
            }
        }
    }

    // subtle pulse for critical unacknowledged warnings
    SequentialAnimation on opacity {
        loops: warning && warning.severity === 'critical' && !(warning && warning.acknowledged) ? Animation.Infinite : 1
        NumberAnimation { from: 1.0; to: 0.85; duration: 600; easing.type: Easing.InOutQuad }
        NumberAnimation { from: 0.85; to: 1.0; duration: 600; easing.type: Easing.InOutQuad }
    }
}