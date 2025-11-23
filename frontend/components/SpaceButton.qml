import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: spaceButton
    property string text: ""
    property color glowColor: "#00ffff"
    property bool enabled: true
    
    signal clicked()
    
    width: Math.max(text.length * 8 + 24, 70)
    height: 32
    radius: 4
    color: enabled ? Qt.rgba(0.06, 0.15, 0.22, 0.9) : Qt.rgba(0.03, 0.08, 0.12, 0.6)
    border.width: 2
    border.color: enabled ? (mouseArea.pressed ? glowColor : Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.6)) : "#333333"
    
    // Glow effect
    Rectangle {
        anchors.fill: parent
        anchors.margins: -2
        radius: parent.radius + 1
        color: "transparent"
        border.width: 1
        border.color: enabled && mouseArea.containsMouse ? Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.8) : "transparent"
        opacity: enabled && mouseArea.containsMouse ? 1 : 0
        
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }
    
    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }
    
    Text {
        text: spaceButton.text
        anchors.centerIn: parent
        color: enabled ? (mouseArea.pressed ? "#ffffff" : glowColor) : "#666666"
        font.pixelSize: 12
        font.bold: true
        font.family: "monospace"
        
        Behavior on color { ColorAnimation { duration: 200 } }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: spaceButton.enabled
        hoverEnabled: true
        onClicked: spaceButton.clicked()
        
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}