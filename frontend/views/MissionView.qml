import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: missionView

    property var missions: []

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        // Header
        Rectangle {
            width: parent.width
            height: 56
            color: "#06282f"
            radius: 8

            Text {
                text: "Mission Overview"
                anchors.centerIn: parent
                color: "#bfeeee"
                font.bold: true
                font.pixelSize: 18
            }
        }

        // Mission List
        ListView {
            id: missionList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: missions

            delegate: Rectangle {
                width: parent.width
                height: 150 + ((modelData.tasks ? modelData.tasks.length : 0) * 100)
                color: "#08303a"
                radius: 8
                border.color: "#0f393f"
                anchors.margins: 8

                // expose mission id to nested Repeaters
                property string missionId: modelData.id

                ColumnLayout {
                    spacing: 4

                    // Mission Name
                    Label {
                        text: "Mission: " + (modelData.name || "Unnamed Mission")
                        color: "#bfeeee"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    // Mission Description
                    Label {
                        text: "Description: " + (modelData.description || "No description provided")
                        color: "#bfeeee"
                        font.pixelSize: 14
                    }

                    // Mission Durations
                    Label {
                        text: "Projected Duration: " + modelData.max_duration_seconds + " seconds"
                        color: "#ffcc66"
                        font.pixelSize: 14
                    }

                    Label {
                        text: "Elapsed Duration: " + modelData.elapsed_seconds + " seconds"
                        color: "#66ff66"
                        font.pixelSize: 14
                    }

                    RowLayout {
                        spacing: 10

                        Button {
                            text: "Start"
                            enabled: !modelData.started
                            onClicked: {
                                var ok = missionBackend.startMission(modelData.id)
                                if (ok) {
                                    refreshTimer.start()
                                }
                            }
                        }

                        Button {
                            text: modelData.paused ? "Resume" : "Pause"
                            enabled: modelData.started
                            onClicked: {
                                if (modelData.paused) {
                                    var ok = missionBackend.resumeMission(modelData.id)
                                    if (ok) refreshTimer.start()
                                } else {
                                    var ok = missionBackend.pauseMission(modelData.id)
                                    if (ok) refreshTimer.start()
                                }
                            }
                        }

                        Button {
                            text: "Stop"
                            enabled: modelData.started
                            onClicked: {
                                var ok = missionBackend.stopMission(modelData.id)
                                if (ok) {
                                    refreshTimer.start()
                                }
                            }
                        }
                    }

                    // Task List
                    Repeater {
                        id: tasksRepeater
                        model: modelData.tasks

                        Rectangle {
                            width: parent.width
                            height: 100
                            color: "#0f393f"
                            radius: 5
                            anchors.margins: 4

                            ColumnLayout {
                                spacing: 2

                                Label {
                                    text: "Task: " + (modelData.title || "Unnamed Task")
                                    color: "#bfeeee"
                                    font.pixelSize: 14
                                    font.bold: true
                                }

                                Label {
                                    text: "Description: " + (modelData.description || "No description provided")
                                    color: "#bfeeee"
                                    font.pixelSize: 12
                                }

                                Label {
                                    text: "Projected Duration: " + modelData.projected_seconds + " seconds"
                                    color: "#ffcc66"
                                    font.pixelSize: 12
                                }

                                RowLayout {
                                    spacing: 10

                                    Label {
                                        text: "Completed: "
                                        color: "#bfeeee"
                                        font.pixelSize: 12
                                    }

                                    CheckBox {
                                        checked: modelData.completed
                                        onCheckedChanged: {
                                            // pass (missionId, taskId, completed) to backend
                                            var ok = missionBackend.markTaskComplete(missionId, modelData.id, checked)
                                            if (ok) {
                                                // schedule a refresh after the model update completes
                                                refreshTimer.start()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Refresh Button
        Button {
            text: "Refresh Missions"
            Layout.alignment: Qt.AlignHCenter
            onClicked: {
                missionView.missions = missionBackend.getMissions()
            }
        }
    }

    Timer {
        id: refreshTimer
        interval: 0
        repeat: false
        onTriggered: {
            missionView.missions = missionBackend.getMissions()
        }
    }

    // Listen for backend updates (emitted every second by the mission manager ticker)
    Connections {
        target: missionBackend
        onMissionsUpdated: {
            // update the UI model when the backend signals a state change
            missionView.missions = missionBackend.getMissions()
        }
    }

    Component.onCompleted: {
        console.log("Missions loaded in QML:", missions)
        missions = missionBackend.getMissions()
    }
}