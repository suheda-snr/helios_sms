import QtQuick 2.15
import QtQuick.Controls 2.15
import "views"

ApplicationWindow {
    id: root
    visible: true
    width: 480
    height: 800
    title: "Tricorder - MGST"
    color: "green"

    property var telemetryData: ({})
    signal warningIssued(string warningMsg)

    Rectangle {
        anchors.fill: parent

        TabBar {
            id: tabBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            TabButton { text: "Vitals" }
            TabButton { text: "Missions" }
        }

        Loader {
            id: viewLoader
            anchors.top: tabBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            sourceComponent: tabBar.currentIndex === 0 ? tricorderComponent : missionComponent
        }
    }

    Component {
        id: tricorderComponent
        TricorderView {
            telemetryData: root.telemetryData
            onWarningIssued: function(msg) { root.warningIssued(msg) }
        }
    }

    Component {
        id: missionComponent
        MissionView { }
    }

    // Alert sound is played from the Python backend using QSoundEffect

    Connections {
        target: backend
        function onTelemetryUpdated(newTelemetry) {
            telemetryData = newTelemetry
        }
        function onWarningIssued(msg) {
            warningIssued(msg)
        }
    }
}
