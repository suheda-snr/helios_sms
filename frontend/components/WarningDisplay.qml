import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: warningDisplay
    width: parent ? parent.width : 420
    height: 36

    // Expose warning text to parent QML
    property alias warningText: warningLabel.text

    Rectangle {
        id: bg
        anchors.fill: parent
        radius: 6
        color: warningLabel.text === "" ? Qt.rgba(0,0,0,0) : Qt.rgba(0.5,0,0,0.85)
        border.color: "#ff4444"
        opacity: warningLabel.text === "" ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 300 } }
    }

    Text {
        id: warningLabel
        anchors.centerIn: parent
        color: "#ffdddd"
        font.pixelSize: 14
        font.bold: true
    }
}
