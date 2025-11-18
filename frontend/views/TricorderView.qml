import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Item {
    id: tricorderView
    property var telemetryData
    signal warningIssued(string warningMsg)

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        GaugeBar {
            label: "Oxygen (O2)"
            value: Number(telemetryData.o2)
            maximum: 100
        }
        GaugeBar {
            label: "Carbon Dioxide (CO2)"
            value: Number(telemetryData.co2)
            maximum: 1
        }
        TempDisplay {
            suitTemp: telemetryData.suit_temp ? telemetryData.suit_temp : "-"
            externalTemp: telemetryData.external_temp ? telemetryData.external_temp : "-"
        }
        GaugeBar {
            label: "Battery"
            value: Number(telemetryData.battery)
            maximum: 100
        }

        WarningDisplay {
            id: warningDisplay
            warningText: ""
        }

        Connections {
            target: backend
            function onWarningIssued(msg) {
                warningDisplay.warningText = msg
            }
        }
    }
}
