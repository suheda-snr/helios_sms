import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: detail
    color: "transparent"
    radius: 6
    Column {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        Text { id: nameLabel; text: mission ? mission.name : "(no mission)"; color: "#dfe" }
        Text { id: elapsedLabel; text: mission ? "Elapsed: " + Math.floor((mission.elapsed||0)) + "s" : ""; color: "#cfe" }

        RowLayout {
            spacing: 8
            Button { text: "Start"; enabled: mission && mission.state !== 'running'; onClicked: missionManager.startMission(mission.id) }
            Button { text: "Pause"; enabled: mission && mission.state === 'running'; onClicked: missionManager.pauseMission(mission.id) }
            Button { text: "Stop"; enabled: mission && mission.state !== 'stopped'; onClicked: missionManager.stopMission(mission.id) }
        }

        Text { text: "Tasks"; font.pixelSize: 12; color: "#bfe" }
        Flickable {
            id: tasksFlick
            contentHeight: tasksModel ? tasksModel.length * 32 : 0
            clip: true
            Layout.fillWidth: true
            Layout.preferredHeight: 120

            Column {
                id: tasksColumn
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 6
                Repeater {
                    model: tasksModel
                    delegate: TaskItem {
                        task: modelData
                        onTaskToggled: function(checked) {
                            missionManager.setTaskCompleted(mission.id, modelData.id, checked)
                        }
                    }
                }
            }
        }
    }

    property var mission: null
    property var tasksModel: []
    // missionManager must be provided from the root context
}
