import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: missionView
    property var missions: []
    property int selectedMissionIndex: -1
    property var expandedMissions: ({}) // Track which missions are expanded by ID

    // Background with space-like gradient
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.01, 0.05, 0.08, 1)
        
        // Animated starfield background
        Canvas {
            id: starfield
            anchors.fill: parent
            property var stars: []
            
            onPaint: {
                var ctx = getContext('2d');
                ctx.clearRect(0, 0, width, height);
                
                // Draw stars
                ctx.fillStyle = '#ffffff';
                for (var i = 0; i < stars.length; i++) {
                    var star = stars[i];
                    ctx.globalAlpha = star.alpha;
                    ctx.beginPath();
                    ctx.arc(star.x, star.y, star.size, 0, 2 * Math.PI);
                    ctx.fill();
                }
            }
            
            Component.onCompleted: {
                // Generate random stars
                stars = [];
                for (var i = 0; i < 150; i++) {
                    stars.push({
                        x: Math.random() * width,
                        y: Math.random() * height,
                        size: Math.random() * 1.5 + 0.5,
                        alpha: Math.random() * 0.8 + 0.2
                    });
                }
                requestPaint();
                
                // Animate star twinkling
                twinkleTimer.start();
            }
            
            Timer {
                id: twinkleTimer
                interval: 100
                repeat: true
                onTriggered: {
                    // Update star alpha for twinkling effect
                    for (var i = 0; i < starfield.stars.length; i++) {
                        if (Math.random() < 0.05) {
                            starfield.stars[i].alpha = Math.random() * 0.8 + 0.2;
                        }
                    }
                    starfield.requestPaint();
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Space-themed header
        Rectangle {
            Layout.fillWidth: true
            height: 80
            color: "transparent"
            
            Rectangle {
                anchors.fill: parent
                radius: 12
                color: Qt.rgba(0.02, 0.07, 0.12, 0.85)
                border.width: 2
                border.color: "#1a4a6a"
                
                // Animated header glow
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -4
                    radius: parent.radius + 2
                    color: "transparent"
                    border.width: 1
                    border.color: Qt.rgba(0, 1, 1, 0.3)
                    
                    SequentialAnimation on border.color {
                        loops: Animation.Infinite
                        ColorAnimation { 
                            from: Qt.rgba(0, 1, 1, 0.3)
                            to: Qt.rgba(0, 1, 1, 0.1)
                            duration: 2000
                        }
                        ColorAnimation { 
                            from: Qt.rgba(0, 1, 1, 0.1)
                            to: Qt.rgba(0, 1, 1, 0.3)
                            duration: 2000
                        }
                    }
                }
                
                RowLayout {
                    anchors.centerIn: parent
                    spacing: 16
                    
                    Text {
                        text: "◢"
                        color: "#00ffff"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    
                    Text {
                        text: "MISSION CONTROL CENTER"
                        color: "#e0ffff"
                        font.pixelSize: 22
                        font.bold: true
                        font.family: "Courier New"
                    }
                    
                    Text {
                        text: "◣"
                        color: "#00ffff"
                        font.pixelSize: 24
                        font.bold: true
                    }
                }
                
                Text {
                    text: `ACTIVE MISSIONS: ${missions.filter(m => m.started).length} | COMPLETED: ${missions.filter(m => m.progress >= 100).length} | TOTAL: ${missions.length}`
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottomMargin: 8
                    color: "#88ccdd"
                    font.pixelSize: 12
                    font.family: "Courier New"
                }
            }
        }

        // Mission cards container
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            contentHeight: missionColumn.height
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            
            Column {
                id: missionColumn
                width: parent.width
                spacing: 16
                
                Repeater {
                    model: missions
                    
                    SpaceMissionCard {
                        width: missionColumn.width
                        missionData: modelData
                        isSelected: index === selectedMissionIndex
                        initialExpanded: expandedMissions[modelData.id] || false
                        
                        onMissionSelected: {
                            selectedMissionIndex = index
                        }
                        
                        onExpansionChanged: {
                            var newExpandedMissions = expandedMissions
                            newExpandedMissions[modelData.id] = expanded
                            expandedMissions = newExpandedMissions
                        }
                        
                        onStartMission: {
                            var ok = missionBackend.startMission(modelData.id)
                        }
                        
                        onPauseMission: {
                            var ok = missionBackend.pauseMission(modelData.id)
                        }
                        
                        onResumeMission: {
                            var ok = missionBackend.resumeMission(modelData.id)
                        }
                        
                        onStopMission: {
                            var ok = missionBackend.stopMission(modelData.id)
                        }
                    }
                }
            }
        }

        // Control panel footer
        Rectangle {
            Layout.fillWidth: true
            height: 60
            radius: 8
            color: Qt.rgba(0.02, 0.07, 0.12, 0.85)
            border.width: 2
            border.color: "#1a4a6a"
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 20
                
                SpaceButton {
                    text: "REFRESH"
                    glowColor: "#00aaff"
                    onClicked: {
                        missionView.missions = missionBackend.getMissions()
                    }
                }
                
                Rectangle {
                    width: 2
                    height: 30
                    color: "#2a6b6f"
                }
                
                Text {
                    text: "HELIOS SMS v2.1.0"
                    color: "#88ccdd"
                    font.pixelSize: 11
                    font.family: "Courier New"
                }
                
                Rectangle {
                    width: 2
                    height: 30
                    color: "#2a6b6f"
                }
                
                Row {
                    spacing: 8
                    
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: "#00ff88"
                        
                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            NumberAnimation { from: 1; to: 0.3; duration: 800 }
                            NumberAnimation { from: 0.3; to: 1; duration: 800 }
                        }
                    }
                    
                    Text {
                        text: "SYSTEM ONLINE"
                        color: "#88ccdd"
                        font.pixelSize: 11
                        font.family: "Courier New"
                    }
                }
            }
        }
    }

    // Debounced update to reduce refreshing frequency
    Timer {
        id: updateDebouncer
        interval: 500  // Half second debounce
        repeat: false
        
        property var pendingMissions: []
        
        onTriggered: {
            missions = pendingMissions
        }
    }

    // Listen for backend updates with smart debouncing
    Connections {
        target: missionBackend
        function onMissionsUpdated() {
            var newMissions = missionBackend.getMissions()
            updateDebouncer.pendingMissions = newMissions
            
            // For immediate updates (start, stop, pause, task completion), update right away
            // For elapsed time updates, use debouncing
            var needsImmediateUpdate = false
            
            if (missions.length !== newMissions.length) {
                needsImmediateUpdate = true
            } else {
                for (var i = 0; i < missions.length && !needsImmediateUpdate; i++) {
                    var oldMission = missions[i]
                    var newMission = newMissions[i]
                    
                    // Check for important state changes
                    if (oldMission.started !== newMission.started ||
                        oldMission.paused !== newMission.paused ||
                        oldMission.progress !== newMission.progress) {
                        needsImmediateUpdate = true
                        break
                    }
                    
                    // Check for task completion changes
                    if (oldMission.tasks.length !== newMission.tasks.length) {
                        needsImmediateUpdate = true
                        break
                    }
                    
                    for (var j = 0; j < oldMission.tasks.length; j++) {
                        if (oldMission.tasks[j].completed !== newMission.tasks[j].completed) {
                            needsImmediateUpdate = true
                            break
                        }
                    }
                }
            }
            
            if (needsImmediateUpdate) {
                updateDebouncer.stop()
                missions = newMissions
            } else {
                // Just elapsed time changes - use debouncing
                updateDebouncer.restart()
            }
        }
    }

    Component.onCompleted: {
        missions = missionBackend.getMissions()
    }
}