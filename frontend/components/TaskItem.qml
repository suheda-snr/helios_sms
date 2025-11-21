import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: taskRow
    width: parent.width
    spacing: 8
    CheckBox { id: chk; checked: task ? task.completed : false; onClicked: { task.completed = checked; taskToggled(checked) } }
    Text { text: task ? task.name : "(no task)"; color: "#dfe" }

    signal taskToggled(bool checked)
    property var task: null
}
