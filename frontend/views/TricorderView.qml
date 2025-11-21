import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: tricorderView
    property var telemetryData
    signal warningIssued(string warningMsg)
    property var activeWarnings: []

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.02,0.07,0.09,1)

        // subtle top header
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 56
            color: "transparent"
            border.color: "#08303a"
            gradient: Gradient {
                GradientStop { position: 0; color: "#06282f" }
                GradientStop { position: 1; color: "#052024" }
            }

            Text {
                text: "TRICORDER — SUIT HUD"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 12
                color: "#bfeeee"
                font.bold: true
                font.pixelSize: 14
            }
        }

        // Center vitals
        RowLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 84
            spacing: 40

            VitalsDial {
                label: "Oxygen (O2)"
                value: Number(telemetryData.o2 ? telemetryData.o2 : 0)
                maximum: 100
            }

            ColumnLayout {
                spacing: 18
                Layout.alignment: Qt.AlignVCenter

                VitalsDial {
                    label: "Battery"
                    value: Number(telemetryData.battery ? telemetryData.battery : 0)
                    maximum: 100
                }

                // CO2 small readout and temperatures
                RowLayout {
                    spacing: 18

                    Rectangle {
                        width: 200; height: 64; radius: 8
                        color: Qt.rgba(0.03,0.08,0.09,0.6)
                        border.color: "#0f393f"
                        Column {
                            anchors.fill: parent
                            anchors.margins: 8
                            Text { text: "CO2"; color: "lightgray"; font.pixelSize: 12 }
                            Text { text: telemetryData.co2 ? telemetryData.co2.toFixed(2) + " %" : "-"; color: "#ffcc66"; font.pixelSize: 18; font.bold: true }
                        }
                    }

                    TempDisplay {
                        suitTemp: telemetryData.suit_temp ? telemetryData.suit_temp : "-"
                        externalTemp: telemetryData.external_temp ? telemetryData.external_temp : "-"
                    }
                }
            }
        }

        // Warning overlay anchored under header
        WarningDisplay {
            id: warningDisplay
            anchors.top: parent.top
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            warningText: ""
        }

        // Active warnings panel (right side)
        Rectangle {
            id: warningsPanel
            width: 220
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 72
            height: parent.height - 120
            radius: 8
            color: Qt.rgba(0.04,0.08,0.09,0.7)
            border.color: "#2a6b6f"

            Column {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Text { text: "Active Warnings"; color: "#ffdcdc"; font.pixelSize: 12; font.bold: true }

                Repeater {
                    model: activeWarnings
                    delegate: WarningItem {
                        warning: modelData
                        onAcknowledge: {
                            backend.acknowledgeWarning(modelData.id)
                        }
                    }
                }
            }
        }

        Connections {
            target: backend
            function onWarningIssued(msg) {
                warningDisplay.warningText = msg
            }
        }

        Connections {
            target: backend
            function onActiveWarningsUpdated() {
                activeWarnings = backend.getActiveWarnings()
            }
        }

        Component.onCompleted: {
            activeWarnings = backend.getActiveWarnings()
        }
    }
}
