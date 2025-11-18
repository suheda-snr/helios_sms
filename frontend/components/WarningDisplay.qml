import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: warningDisplay
    width: 400
    height: 20

    // Expose warning text to parent QML
    property alias warningText: warningLabel.text

    Text {
        id: warningLabel
        anchors.fill: parent
        color: "red"
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
