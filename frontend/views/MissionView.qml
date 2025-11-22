import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: missionView
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.03,0.06,0.07,1)

        // Header
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 56
            color: "transparent"
            border.color: "#08303a"

            Text {
                text: "MISSIONS"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 12
                color: "#bfeeee"
                font.bold: true
                font.pixelSize: 14
            }
        }

        Rectangle {
            anchors.top: parent.top
            anchors.topMargin: 72
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 12

            RowLayout {
                spacing: 8
                Button {
                    text: "Create Mission"
                    onClicked: {
                        if (mission && mission.publishMissionCommand) {
                            mission.publishMissionCommand({action: "create_mission", name: "New Mission"})
                        }
                    }
                }

                Button {
                    text: "Refresh"
                    onClicked: {
                        if (mission && mission.requestMissionState) mission.requestMissionState()
                    }
                }
            }

            // Missions list
            Flickable {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 48
                anchors.bottom: parent.bottom
                contentHeight: columnContent.height
                clip: true
                Column {
                    id: columnContent
                    width: parent.width
                    spacing: 8

                    // Placeholder: backend.getMissions() expected
                    Repeater {
                        model: mission && mission.getMissions ? mission.getMissions() : []
                        delegate: MissionItem {
                            mission: modelData
                            onStartRequested: {
                                if (mission && mission.publishMissionCommand) mission.publishMissionCommand({action: "start", mission_id: mission.id})
                            }
                            onStopRequested: {
                                if (mission && mission.publishMissionCommand) mission.publishMissionCommand({action: "stop", mission_id: mission.id})
                            }
                        }
                    }
                }
            }
        }

        Connections {
            target: mission
            // hook for when Python updates mission list/state
            function onMissionsUpdated() {
                // force UI to update — Repeater reads mission.getMissions()
            }
        }
    }
}
