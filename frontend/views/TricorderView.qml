import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: tricorderView
    property var telemetryData
    signal warningIssued(string warningMsg)
    property var activeWarnings: []

    // Background with enhanced space theme
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.01, 0.05, 0.08, 1)
        
        // Subtle animated grid pattern
        Canvas {
            anchors.fill: parent
            opacity: 0.1
            
            onPaint: {
                var ctx = getContext('2d');
                ctx.clearRect(0, 0, width, height);
                ctx.strokeStyle = '#00ffff';
                ctx.lineWidth = 0.5;
                
                var gridSize = 40;
                for (var x = 0; x <= width; x += gridSize) {
                    ctx.beginPath();
                    ctx.moveTo(x, 0);
                    ctx.lineTo(x, height);
                    ctx.stroke();
                }
                for (var y = 0; y <= height; y += gridSize) {
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(width, y);
                    ctx.stroke();
                }
            }
            
            Timer {
                interval: 2000
                repeat: true
                running: true
                onTriggered: parent.requestPaint()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Enhanced header with more space theme
        Rectangle {
            Layout.fillWidth: true
            height: 70
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
                border.color: Qt.rgba(0, 1, 0.5, 0.4)
                
                SequentialAnimation on border.color {
                    loops: Animation.Infinite
                    ColorAnimation { 
                        from: Qt.rgba(0, 1, 0.5, 0.4)
                        to: Qt.rgba(0, 1, 0.5, 0.1)
                        duration: 1500
                    }
                    ColorAnimation { 
                        from: Qt.rgba(0, 1, 0.5, 0.1)
                        to: Qt.rgba(0, 1, 0.5, 0.4)
                        duration: 1500
                    }
                }
            }

            RowLayout {
                anchors.centerIn: parent
                spacing: 16
                
                Text {
                    text: "◈"
                    color: "#00ffaa"
                    font.pixelSize: 20
                    font.bold: true
                }
                
                Text {
                    text: "TELEMETRY MONITORING SYSTEM"
                    color: "#bfeeee"
                    font.bold: true
                    font.pixelSize: 18
                    font.family: "Courier New"
                }
                
                Text {
                    text: "◈"
                    color: "#00ffaa"
                    font.pixelSize: 20
                    font.bold: true
                }
            }
            
            Text {
                text: "REAL-TIME ENVIRONMENTAL STATUS"
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 8
                color: "#88ccdd"
                font.pixelSize: 11
                font.family: "Courier New"
            }
        }

        // Center vitals with enhanced styling
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 50
            Layout.alignment: Qt.AlignCenter

            RowLayout {
                spacing: 40
                Layout.alignment: Qt.AlignHCenter

                VitalsDial {
                    label: "OXYGEN LEVELS"
                    value: Number(telemetryData.o2 ? telemetryData.o2 : 0)
                    maximum: 100
                }

            VitalsDial {
                label: "CARBON DIOXIDE"
                value: Number(telemetryData.co2 ? telemetryData.co2 : 0)
                maximum: 6.0
            }                VitalsDial {
                    label: "POWER SYSTEMS"
                    value: Number(telemetryData.battery ? telemetryData.battery : 0)
                    maximum: 100
                }
            }

            // Enhanced temperature and leak status display centered below the vitals
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 40
                
                TempDisplay {
                    suitTemp: telemetryData.suit_temp ? telemetryData.suit_temp : "-"
                    externalTemp: telemetryData.external_temp ? telemetryData.external_temp : "-"
                }
                
                // Suit integrity status
                Rectangle {
                    width: 200
                    height: 80
                    radius: 8
                    color: telemetryData.leak ? Qt.rgba(0.4, 0.05, 0.05, 0.9) : Qt.rgba(0.02, 0.08, 0.12, 0.8)
                    border.color: telemetryData.leak ? "#ff4444" : "#0f393f"
                    border.width: 2
                    
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: -2
                        radius: parent.radius + 1
                        color: "transparent"
                        border.width: 1
                        border.color: telemetryData.leak ? Qt.rgba(1, 0.3, 0.3, 0.6) : Qt.rgba(0, 0.8, 1, 0.3)
                        opacity: 0.6
                        
                        SequentialAnimation on opacity {
                            loops: telemetryData.leak ? Animation.Infinite : 1
                            running: telemetryData.leak
                            NumberAnimation { from: 0.6; to: 0.2; duration: 500 }
                            NumberAnimation { from: 0.2; to: 0.6; duration: 500 }
                        }
                    }
                    
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        
                        Text { 
                            text: "SUIT INTEGRITY"
                            color: "#88ccdd" 
                            font.pixelSize: 11
                            font.family: "Courier New"
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text { 
                            text: telemetryData.leak ? "⚠ LEAK DETECTED" : "✓ SEALED"
                            color: telemetryData.leak ? "#ff6666" : "#00ff88"
                            font.pixelSize: 14
                            font.bold: true
                            font.family: "Courier New"
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text { 
                            text: telemetryData.leak ? "IMMEDIATE ATTENTION" : "NOMINAL STATUS"
                            color: telemetryData.leak ? "#ffaaaa" : "#88ccdd"
                            font.pixelSize: 9
                            font.family: "Courier New"
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }
        }

        // Enhanced status footer
        Rectangle {
            Layout.fillWidth: true
            height: 50
            radius: 8
            color: Qt.rgba(0.02, 0.07, 0.12, 0.85)
            border.width: 2
            border.color: "#1a4a6a"
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 30
                
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
                        text: "SENSORS ACTIVE"
                        color: "#88ccdd"
                        font.pixelSize: 11
                        font.family: "Courier New"
                    }
                }
                
                Rectangle {
                    width: 2
                    height: 20
                    color: "#2a6b6f"
                }
                
                Text {
                    text: "HELIOS EVA SUIT v3.2"
                    color: "#88ccdd"
                    font.pixelSize: 11
                    font.family: "Courier New"
                }
                
                Rectangle {
                    width: 2
                    height: 20
                    color: "#2a6b6f"
                }
                
                Text {
                    text: `WARNINGS: ${activeWarnings.length}`
                    color: activeWarnings.length > 0 ? "#ffaa44" : "#88ccdd"
                    font.pixelSize: 11
                    font.family: "Courier New"
                }
            }
        }
    }

    // Enhanced warnings panel (right side overlay)
    Rectangle {
        id: warningsPanel
        width: 240
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 160
        height: Math.min(parent.height - 200, activeWarnings.length * 60 + 60)
        radius: 8
        color: Qt.rgba(0.04, 0.08, 0.09, 0.9)
        border.color: "#aa4444"
        border.width: 2
        visible: activeWarnings.length > 0
        opacity: activeWarnings.length > 0 ? 1 : 0
        
        Behavior on opacity { NumberAnimation { duration: 300 } }
        
        // Glow effect for warnings panel
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: parent.radius + 2
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(1, 0.3, 0.3, 0.5)
            visible: parent.visible
        }

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            Text { 
                text: "⚠ ACTIVE WARNINGS"
                color: "#ffdddd"
                font.pixelSize: 13
                font.bold: true
                font.family: "Courier New"
            }

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
