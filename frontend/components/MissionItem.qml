import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: parent ? parent.width : 400
    height: 84
    radius: 8
    color: Qt.rgba(0.06,0.12,0.13,0.8)
    border.color: "#1f6b6f"

    property var mission: ({ id: "", name: "", tasks: [], started: false, paused: false, elapsed_seconds: 0 })

    signal startRequested()
    signal stopRequested()

    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Text { text: mission.name; color: "#dff7f7"; font.bold: true }
            Text { text: "Elapsed: " + mission.elapsed_seconds + "s"; color: "#cfe"; font.pixelSize: 12 }
            RowLayout {
                spacing: 8
                Repeater {
                    model: mission.tasks ? mission.tasks.slice(0,3) : []
                    delegate: Rectangle {
                        width: 8; height: 8; radius: 4
                        color: modelData.completed ? "#66ff66" : "#ffcc66"
                    }
                }
            }
        }

        ColumnLayout {
            spacing: 6
            Button { text: mission.started ? "Stop" : "Start"; onClicked: mission.started ? root.stopRequested() : root.startRequested() }
        }
    }
}
