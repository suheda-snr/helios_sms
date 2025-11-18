// app/qml/Tricorder.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: win
    visible: true
    title: "Tricorder - MGST"
    width: 480
    height: 800

    property var telemetryData: ({})
    property var missionData: ({})
    signal requestMarkTask(int taskId)

    ColumnLayout {
        anchors.fill: parent
        spacing: 8
        padding: 12

        Rectangle {
            Layout.fillWidth: true
            color: "#0b1220"
            radius: 8
            border.color: "#2b6f9e"
            height: 140

            Column {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 6

                Row {
                    spacing: 10
                    anchors.horizontalCenter: parent.horizontalCenter

                    Column {
                        spacing: 4
                        Text { text: "O2"; color: "white" }
                        ProgressBar {
                            id: o2Bar
                            from: 0; to: 100
                            value: telemetryData.o2 ? telemetryData.o2 : 0
                            width: 200
                            height: 16
                        }
                        Text { text: Math.round((telemetryData.o2?telemetryData.o2:0)*100)/100 + " %"; color: "lightgreen" }
                    }

                    Column {
                        spacing: 4
                        Text { text: "Battery"; color: "white" }
                        ProgressBar {
                            id: battBar
                            from: 0; to: 100
                            value: telemetryData.battery ? telemetryData.battery : 0
                            width: 200
                            height: 16
                        }
                        Text { text: Math.round((telemetryData.battery?telemetryData.battery:0)*100)/100 + " %"; color: "lightyellow" }
                    }
                }

                Row {
                    spacing: 16
                    Text { text: "CO2: " + (telemetryData.co2 ? telemetryData.co2 : "-") + " %"; color: "white" }
                    Text { text: "Suit Temp: " + (telemetryData.suit_temp ? telemetryData.suit_temp : "-") + " °C"; color: "white" }
                    Text { text: "Ext Temp: " + (telemetryData.external_temp ? telemetryData.external_temp : "-") + " °C"; color: "white" }
                }
            }
        }

        // Mission controls
        Rectangle {
            color: "#071022"
            radius: 6
            Layout.fillWidth: true
            height: 120

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                Row {
                    spacing: 8
                    Text { text: missionData.name ? missionData.name : "No Active Mission"; color: "white"; font.pixelSize: 16 }
                    Text { text: missionData.status ? "(" + missionData.status + ")" : ""; color: "lightgrey" }
                }

                Row {
                    spacing: 8
                    Button { text: "Start"; onClicked: backend.startMission() }
                    Button { text: "Pause"; onClicked: backend.pauseMission() }
                    Button { text: "Stop"; onClicked: backend.stopMission() }
                    Spacer {}
                    Text { text: "Elapsed: " + (missionData.elapsed ? missionData.elapsed + "s" : "0s"); color: "white" }
                    Text { text: "Max: " + (missionData.max_duration ? missionData.max_duration + "s" : "-"); color: "white" }
                }
            }
        }

        // Tasks
        Rectangle {
            color: "#081926"
            radius: 6
            Layout.fillWidth: true
            Layout.fillHeight: true
            height: 420
            Column {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                Text { text: "Tasks"; color: "white"; font.pixelSize: 14 }

                ListModel { id: taskModel }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: taskModel
                    delegate: Rectangle {
                        width: parent.width
                        height: 56
                        color: index % 2 == 0 ? "#071e2a" : "#062630"
                        Row {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8
                            CheckBox {
                                checked: done
                                onCheckedChanged: {
                                    if (checked) backend.markTaskComplete(id)
                                }
                            }
                            Column {
                                Text { text: title; color: done ? "lightgray" : "white" }
                                Text { text: "Projected: " + proj_duration + "s"; color: "lightgray"; font.pixelSize: 12 }
                            }
                            Spacer {}
                        }
                    }
                }
            }
        }

        // Warnings area
        Rectangle {
            color: "#220000"
            radius: 6
            Layout.fillWidth: true
            height: 56
            Text {
                id: warningText
                anchors.centerIn: parent
                text: ""
                color: "yellow"
            }
        }
    }

    Connections {
        target: backend
        onTelemetryUpdated: {
            telemetryData = telemetry
        }
        onMissionUpdated: {
            missionData = mission
            // populate taskModel
            taskModel.clear()
            if (mission.tasks) {
                for (var i = 0; i < mission.tasks.length; ++i) {
                    taskModel.append(mission.tasks[i])
                }
            }
        }
        onWarningIssued: {
            // show warning for a short time
            warningText.text = warning
            // clear after 4s
            Qt.callLater(function(){ warningText.text = "" }, 4000)
        }
    }
}
