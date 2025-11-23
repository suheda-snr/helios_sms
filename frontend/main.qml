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
        color: Qt.rgba(0.01, 0.05, 0.08, 1)

        Rectangle {
            id: tabBarContainer
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 60
            color: Qt.rgba(0.02, 0.07, 0.12, 0.9)
            border.width: 1
            border.color: "#1a4a6a"

            Row {
                anchors.centerIn: parent
                spacing: 20

                Rectangle {
                    width: 80
                    height: 35
                    radius: 6
                    color: tabBar.currentIndex === 0 ? Qt.rgba(0, 0.6, 0.8, 0.3) : Qt.rgba(0.05, 0.1, 0.15, 0.8)
                    border.width: 1
                    border.color: tabBar.currentIndex === 0 ? "#00aacc" : "#666666"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "VITALS"
                        color: tabBar.currentIndex === 0 ? "#ffffff" : "#aaaaaa"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: tabBar.currentIndex = 0
                    }
                }

                Rectangle {
                    width: 80
                    height: 35
                    radius: 6
                    color: tabBar.currentIndex === 1 ? Qt.rgba(0, 0.6, 0.8, 0.3) : Qt.rgba(0.05, 0.1, 0.15, 0.8)
                    border.width: 1
                    border.color: tabBar.currentIndex === 1 ? "#00aacc" : "#666666"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "MISSIONS"
                        color: tabBar.currentIndex === 1 ? "#ffffff" : "#aaaaaa"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: tabBar.currentIndex = 1
                    }
                }
            }
        }

        TabBar {
            id: tabBar
            visible: false
            TabButton { text: "Vitals" }
            TabButton { text: "Missions" }
        }

        Loader {
            id: viewLoader
            anchors.top: tabBarContainer.bottom
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
