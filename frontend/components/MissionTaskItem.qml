import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property alias title: taskTitle.text
    property bool completed: false
    signal toggled()
    signal requestDelete()

    Rectangle {
        id: container
        width: parent.width
        height: 46
        radius: 6
        color: completed ? "#0b3b33" : "#072727"
        border.color: "#0f5a58"

        RowLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 10

            CheckBox {
                id: cb
                checked: root.completed
                onCheckedChanged: {
                    root.completed = checked
                    root.toggled()
                }
            }

            Text {
                id: taskTitle
                text: ""
                color: root.completed ? "#c8ffd2" : "#e6ffff"
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                font.pixelSize: 14
                Layout.fillWidth: true
            }

            Button {
                id: delBtn
                text: "Remove"
                onClicked: root.requestDelete()
                width: 72
                height: 28
            }
        }
    }
}
