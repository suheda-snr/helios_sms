import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    // Layout.* attached properties can be set by parent layouts
    width: 260
    height: 200

    // Expose a model property so parent can set it
    property var model: []

    ListView {
        id: missionList
        anchors.fill: parent
        model: root.model
        delegate: ItemDelegate {
            width: parent.width
            text: modelData.name + " (" + Math.floor((modelData.elapsed||0)) + "/" + (modelData.duration||0) + "s)"
            onClicked: {
                missionSelected(modelData)
            }
        }
    }

    signal missionSelected(var mission)
}
