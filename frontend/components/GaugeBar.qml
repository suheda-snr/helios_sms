import QtQuick 2.15
import QtQuick.Controls 2.15

Column {
    property string label: ""
    property real value: 0
    property real maximum: 100
    spacing: 4

    Text { text: label; color: "white" }
    ProgressBar {
        id: progressBar
        from: 0; to: maximum
        value: value
        width: 400; height: 20
    }
    Text {
        text: Math.round(progressBar.value*100)/100 + " %";
        color: label === "Oxygen (O2)" ? "lightgreen" :
               label === "Carbon Dioxide (CO2)" ? "orange" : "lightyellow"
    }
}
