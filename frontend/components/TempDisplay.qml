import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: container
    width: 280
    height: 80
    radius: 8
    color: Qt.rgba(0.02, 0.08, 0.12, 0.8)
    border.width: 2
    border.color: "#0f393f"

    property string suitTemp: "-"
    property string externalTemp: "-"
    
    // Enhanced glow effect
    Rectangle {
        anchors.fill: parent
        anchors.margins: -2
        radius: parent.radius + 1
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(0, 0.8, 1, 0.3)
        opacity: 0.6
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 24

        Column {
            spacing: 6
            Text { 
                text: "SUIT TEMPERATURE"
                color: "#88ccdd"
                font.pixelSize: 10
                font.family: "monospace"
            }
            Text { 
                text: suitTemp + " °C"
                color: "#e0ffff"
                font.pixelSize: 16
                font.bold: true
                font.family: "monospace"
            }
        }

        Rectangle {
            width: 2
            height: 40
            color: "#2a6b6f"
        }

        Column {
            spacing: 6
            Text { 
                text: "EXTERNAL TEMP"
                color: "#88ccdd"
                font.pixelSize: 10
                font.family: "monospace"
            }
            Text { 
                text: externalTemp + " °C"
                color: "#e0ffff"
                font.pixelSize: 16
                font.bold: true
                font.family: "monospace"
            }
        }

        Item { Layout.fillWidth: true }
    }
}
