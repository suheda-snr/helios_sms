import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: container
    width: 420
    height: 64
    radius: 8
    color: "transparent"

    property string suitTemp: "-"
    property string externalTemp: "-"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 24

        Column {
            spacing: 2
            Text { text: "Suit Temp"; color: "lightgray"; font.pixelSize: 12 }
            Text { text: suitTemp + " °C"; color: "white"; font.pixelSize: 18; font.bold: true }
        }

        Column {
            spacing: 2
            Text { text: "External Temp"; color: "lightgray"; font.pixelSize: 12 }
            Text { text: externalTemp + " °C"; color: "white"; font.pixelSize: 18; font.bold: true }
        }

        Item { Layout.fillWidth: true }
    }
}
