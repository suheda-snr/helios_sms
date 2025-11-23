import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: tricorderView
    property var currentMissionProgress: null
    property var telemetryData
    signal warningIssued(string warningMsg)
    property var activeWarnings: []

    Theme { id: theme }

    Rectangle {
        anchors.fill: parent
        color: theme.bg

        // subtle top header
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 56
            color: "transparent"
            border.color: theme.panelAlt
            gradient: Gradient {
                GradientStop { position: 0; color: theme.panel }
                GradientStop { position: 1; color: theme.panelAlt }
            }

            Text {
                text: "TRICORDER — SUIT HUD"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 12
                color: theme.textPrimary
                font.bold: true
                font.pixelSize: 14
            }
            // Mission HUD: remaining time + risk indicator
            Text {
                id: missionHud
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 12
                font.pixelSize: 13
                text: {
                    var m = tricorderView.currentMissionProgress
                    if (!m) return ""
                    var dur = m.duration
                    var elapsed = m.elapsed ? m.elapsed : 0
                    if (dur === null || dur === undefined) return m.name ? (m.name + " — running") : "Mission running"
                    var rem = Math.max(0, dur - elapsed)
                    var mm = Math.floor(rem / 60)
                    var ss = rem % 60
                    function pad(n){ return n<10?('0'+n):n }
                    var name = m.name ? (m.name + " — ") : ""
                    return name + mm + ":" + pad(ss)
                }
                // color: if estimated suit capacity seems less than remaining, show danger
                color: {
                    var m = tricorderView.currentMissionProgress
                    if (!m) return theme.textMuted
                    var dur = m.duration
                    var elapsed = m.elapsed ? m.elapsed : 0
                    if (dur === null || dur === undefined) return theme.textMuted
                    var rem = Math.max(0, dur - elapsed)
                    var capBattery = telemetryData && telemetryData.battery ? telemetryData.battery * 60 : 0
                    var capO2 = telemetryData && telemetryData.o2 ? telemetryData.o2 * 60 : 0
                    var risk = (capBattery && rem > capBattery) || (capO2 && rem > capO2)
                    return risk ? theme.danger : theme.textMuted
                }
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
                        color: theme.panel
                        border.color: theme.panelAlt
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
        color: theme.panel
        border.color: theme.panelAlt

            Column {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Text { text: "Active Warnings"; color: theme.warning; font.pixelSize: 12; font.bold: true }

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

        Connections {
            target: backend
            function onMissionProgress(m) {
                tricorderView.currentMissionProgress = m
            }
        }

        // Mission button and dialog
        Button {
            id: missionBtn
            text: "Missions"
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 12
            background: Rectangle { color: theme.accent; radius: 6 }
            contentItem: Text { text: missionBtn.text; color: theme.panel; font.bold: true }
            onClicked: missionDialog.visible = true
        }

        MissionView {
            id: missionDialog
            visible: false
        }

        Component.onCompleted: {
            activeWarnings = backend.getActiveWarnings()
        }
    }
}