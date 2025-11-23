import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: taskItem
    property var taskData
    property string missionId
    
    width: parent.width
    height: 70
    radius: 4
    color: taskData.completed ? Qt.rgba(0.04, 0.15, 0.08, 0.8) : Qt.rgba(0.08, 0.06, 0.04, 0.8)
    border.width: 1
    border.color: taskData.completed ? "#228844" : "#4a3a2a"
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12
        
        // Task completion indicator
        Rectangle {
            width: 16
            height: 16
            radius: 8
            color: taskData.completed ? "#00ff88" : "transparent"
            border.width: 2
            border.color: taskData.completed ? "#00ff88" : "#666666"
            
            Text {
                text: "✓"
                anchors.centerIn: parent
                color: "#ffffff"
                font.pixelSize: 10
                font.bold: true
                visible: taskData.completed
            }
            
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    // Toggle task completion without triggering mission card refresh
                    var ok = missionBackend.markTaskComplete(missionId, taskData.id, !taskData.completed)
                    // Prevent event propagation to avoid collapsing the mission card
                    mouse.accepted = true
                }
                cursorShape: Qt.PointingHandCursor
            }
        }
        
        // Task details
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            
            Text {
                text: taskData.title || "Unnamed Task"
                color: taskData.completed ? "#aaffaa" : "#dddddd"
                font.pixelSize: 13
                font.bold: true
                font.family: "Arial"
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            
            Text {
                text: taskData.description || "No task description"
                color: taskData.completed ? "#88cc88" : "#aaaaaa"
                font.pixelSize: 11
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }
        
        // Duration indicator
        Rectangle {
            width: 60
            height: 24
            radius: 2
            color: Qt.rgba(0.02, 0.08, 0.12, 0.6)
            border.color: "#2a4a6b"
            
            Text {
                text: `${Math.floor(taskData.projected_seconds / 60)}:${String(taskData.projected_seconds % 60).padStart(2, '0')}`
                anchors.centerIn: parent
                color: "#88ccdd"
                font.pixelSize: 10
                font.family: "monospace"
            }
        }
    }
}