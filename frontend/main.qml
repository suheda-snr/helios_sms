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

    TricorderView {
        anchors.fill: parent
        telemetryData: root.telemetryData
        onWarningIssued: function(msg) {
            root.warningIssued(msg)
        }
    }

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
