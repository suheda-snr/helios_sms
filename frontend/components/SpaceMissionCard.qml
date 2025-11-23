import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: missionCard
    property var missionData
    property bool isSelected: false
    property bool isExpanded: false
    property bool initialExpanded: false
    
    signal missionSelected()
    signal startMission()
    signal pauseMission()
    signal resumeMission()
    signal stopMission()
    signal expansionChanged(bool expanded)
    
    width: parent.width
    height: isExpanded ? expandedHeight : collapsedHeight
    
    property int collapsedHeight: 180
    property int expandedHeight: 260 + (missionData.tasks ? missionData.tasks.length * 80 : 0)
    
    radius: 12
    color: isSelected ? Qt.rgba(0.08, 0.25, 0.35, 0.9) : Qt.rgba(0.04, 0.12, 0.18, 0.8)
    border.width: 2
    border.color: isSelected ? "#00ffff" : (missionData.started ? "#00ff88" : "#2a6b6f")
    
    // Animated glow effect for selected mission
    Rectangle {
        anchors.fill: parent
        anchors.margins: -4
        radius: parent.radius + 2
        color: "transparent"
        border.width: 1
        border.color: isSelected ? Qt.rgba(0, 1, 1, 0.6) : "transparent"
        opacity: isSelected ? 1 : 0
        
        Behavior on opacity { NumberAnimation { duration: 300 } }
        
        SequentialAnimation on border.color {
            running: isSelected
            loops: Animation.Infinite
            ColorAnimation { 
                from: Qt.rgba(0, 1, 1, 0.6)
                to: Qt.rgba(0, 1, 1, 0.2)
                duration: 1500
            }
            ColorAnimation { 
                from: Qt.rgba(0, 1, 1, 0.2)
                to: Qt.rgba(0, 1, 1, 0.6)
                duration: 1500
            }
        }
    }
    
    Behavior on height { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
    Behavior on color { ColorAnimation { duration: 300 } }
    
    MouseArea {
        anchors.fill: parent
        anchors.bottomMargin: isExpanded ? tasksSection.height : 0
        onClicked: {
            missionCard.missionSelected()
            isExpanded = !isExpanded
            missionCard.expansionChanged(isExpanded)
        }
    }
    
    Component.onCompleted: {
        isExpanded = initialExpanded
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10
        
        // Header section
        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            Layout.preferredHeight: 50
            
            // Mission status indicator
            Rectangle {
                width: 12
                height: 12
                radius: 6
                Layout.alignment: Qt.AlignVCenter
                color: {
                    if (missionData.started && !missionData.paused) return "#00ff88"
                    if (missionData.paused) return "#ffaa00"
                    if (missionData.progress >= 100) return "#4488ff"
                    return "#666666"
                }
                
                SequentialAnimation on opacity {
                    running: missionData.started && !missionData.paused
                    loops: Animation.Infinite
                    NumberAnimation { from: 1; to: 0.3; duration: 800 }
                    NumberAnimation { from: 0.3; to: 1; duration: 800 }
                }
            }
            
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                
                Text {
                    text: missionData.name || "Unnamed Mission"
                    color: "#e0ffff"
                    font.pixelSize: 16
                    font.bold: true
                    font.family: "monospace"
                }
                
                Text {
                    text: `DURATION: ${Math.floor(missionData.max_duration_seconds / 60)}:${String(missionData.max_duration_seconds % 60).padStart(2, '0')} | ELAPSED: ${Math.floor(missionData.elapsed_seconds / 60)}:${String(missionData.elapsed_seconds % 60).padStart(2, '0')}`
                    color: "#88ccdd"
                    font.pixelSize: 11
                    font.family: "monospace"
                }
            }
            
            // Progress indicator
            Rectangle {
                width: 70
                height: 35
                radius: 4
                color: Qt.rgba(0.02, 0.08, 0.12, 0.8)
                border.color: "#2a6b6f"
                Layout.alignment: Qt.AlignVCenter
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    
                    Text {
                        text: "PROGRESS"
                        color: "#88ccdd"
                        font.pixelSize: 8
                        font.family: "monospace"
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: Math.round(missionData.progress || 0) + "%"
                        color: "#00ffff"
                        font.pixelSize: 12
                        font.bold: true
                        font.family: "monospace"
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
        
        // Mission description
        Text {
            text: missionData.description || "No mission briefing available"
            color: "#aaddee"
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            maximumLineCount: 2
            elide: Text.ElideRight
            font.family: "Arial"
        }
        
        // Control buttons
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 35
            spacing: 10
            
            SpaceButton {
                text: "START"
                enabled: !missionData.started
                glowColor: "#00ff88"
                onClicked: missionCard.startMission()
            }
            
            SpaceButton {
                text: missionData.paused ? "RESUME" : "PAUSE"
                enabled: missionData.started
                glowColor: missionData.paused ? "#ffaa00" : "#ff8800"
                onClicked: missionData.paused ? missionCard.resumeMission() : missionCard.pauseMission()
            }
            
            SpaceButton {
                text: "STOP"
                enabled: missionData.started
                glowColor: "#ff4444"
                onClicked: missionCard.stopMission()
            }
            
            Item { Layout.fillWidth: true }
        }
        
        // Tasks section (only visible when expanded)
        Rectangle {
            id: tasksSection
            Layout.fillWidth: true
            Layout.preferredHeight: isExpanded ? tasksColumn.height + 20 : 0
            visible: isExpanded
            opacity: isExpanded ? 1 : 0
            color: Qt.rgba(0.02, 0.06, 0.09, 0.6)
            border.color: "#1a4a5a"
            radius: 6
            
            Behavior on opacity { NumberAnimation { duration: 300 } }
            
            Column {
                id: tasksColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 8
                
                Text {
                    text: "MISSION TASKS"
                    color: "#00ffff"
                    font.pixelSize: 14
                    font.bold: true
                    font.family: "Courier New"
                }
                
                Repeater {
                    model: missionData.tasks
                    
                    TaskItem {
                        width: tasksColumn.width
                        taskData: modelData
                        missionId: missionData.id
                    }
                }
            }
        }
    }
}