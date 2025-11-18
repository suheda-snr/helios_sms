import QtQuick 2.15
import QtQuick.Controls 2.15

Row {
    property string suitTemp: "-"
    property string externalTemp: "-"
    spacing: 16

    Text { text: "Suit Temp: " + suitTemp + " °C"; color: "white" }
    Text { text: "External Temp: " + externalTemp + " °C"; color: "white" }
}
