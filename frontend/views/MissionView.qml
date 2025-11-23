import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "../components"

import "../components"

Dialog {
    id: missionDialog
    title: "Missions"
    modal: true
    standardButtons: Dialog.Close
    onAccepted: visible = false

    property var missions: []
    property var selectedMission: null

    function refreshMissions() {
        var currentId = selectedMission ? selectedMission.id : null
        missions = backend.getMissions()
        console.log("MissionView.refreshMissions: got", missions ? missions.length : 0, "missions")
        if (missions.length > 0) {
            // try to restore selection by id
            if (currentId) {
                for (var i = 0; i < missions.length; ++i) {
                    if (missions[i].id === currentId) {
                        selectedMission = missions[i]
                        // sync list index if available
                        try { missionList.currentIndex = i; missionList.positionViewAtIndex(i, ListView.Center) } catch (e) {}
                        return
                    }
                }
            }
            // fallback to first
            selectedMission = missions[0]
            try { missionList.currentIndex = 0; missionList.positionViewAtIndex(0, ListView.Center) } catch (e) {}
        } else {
            selectedMission = null
        }
    }

    onSelectedMissionChanged: {
        if (!selectedMission) return
        for (var i=0;i<missions.length;++i) {
            if (missions[i].id === selectedMission.id) {
                try { missionList.currentIndex = i; missionList.positionViewAtIndex(i, ListView.Center) } catch(e) {}
                break
            }
        }
    }

    onVisibleChanged: {
        if (visible) {
            refreshMissions()
        }
    }

    ColumnLayout {
        width: 420
        spacing: 8
        anchors.fill: parent
        anchors.margins: 8

        ColumnLayout {
            spacing: 6
            Layout.fillWidth: true
            RowLayout {
                spacing: 8
                Layout.fillWidth: true
                TextField { id: nameField; placeholderText: "Mission name"; Layout.fillWidth: true }
                TextField { id: durField; placeholderText: "Duration (s)"; width: 120 }
            }
            TextField { id: descField; placeholderText: "Description (optional)"; Layout.fillWidth: true; onTextChanged: missionDialog.descriptionToCreate = text }

            // task-creation UI removed — missions are created with name, duration, description only

            RowLayout {
                spacing: 8
                Button {
                    text: "Add Mission"
                    onClicked: {
                        var dur = Number(durField.text)
                        if (isNaN(dur)) dur = null
                        // create mission without tasks
                        var created = backend.createMission(nameField.text, dur, null, descField.text)
                        if (created && created.id) {
                            nameField.text = ""
                            durField.text = ""
                            descField.text = ""
                            refreshMissions()
                            selectMissionById(created.id)
                        } else {
                            refreshMissions()
                        }
                    }
                }

                Button {
                    text: "Clear"
                    onClicked: { nameField.text = ""; durField.text = ""; descField.text = "" }
                }
            }
        }

        RowLayout {
            spacing: 12
            Layout.fillWidth: true
                ColumnLayout {
                    spacing: 4
                    Layout.preferredWidth: 180
                    Rectangle { width: 180; height: 28; color: "transparent" }
                    Text { text: "Missions"; font.bold: true; color: theme.textPrimary }
                    ListView {
                        id: missionList
                        model: missions
                        clip: true
                        width: 180
                        height: 200
                        delegate: Item {
                            id: missionItem
                            width: parent.width
                            height: 36
                            property bool isSelected: missionList.currentIndex === index

                            Rectangle {
                                anchors.fill: parent
                                color: missionItem.isSelected ? "#14353a" : "transparent"
                                radius: 4
                            }

                            Row {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6
                                Text {
                                    text: (index+1) + ". " + (modelData && modelData.name ? modelData.name : "(no name)")
                                    color: missionItem.isSelected ? "#ffffff" : "#e6f7f7"
                                    elide: Text.ElideRight
                                    font.pixelSize: 13
                                }
                                Text {
                                    text: (modelData && modelData.state === 'running') ? ' (running)' : ''
                                    color: '#ffd24d'
                                    font.pixelSize: 12
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    // select only; do not auto-start
                                    missionDialog.selectedMission = modelData
                                    missionList.currentIndex = index
                                }
                            }

                            Component.onCompleted: {
                                console.log('Mission delegate loaded:', modelData ? modelData.name : '<null>', 'type=', typeof modelData)
                            }
                        }
                    }

                    // Debug fallback: simple list of names to ensure visibility
                    Repeater {
                        model: missions
                        delegate: Text { text: (index+1) + ". " + (modelData && modelData.name ? modelData.name : '(no name)'); color: "#bfeeee"; visible: false }
                    }
                }
            

                    Rectangle {
                        width: 240; height: 200; radius: 6; color: theme.panel; border.color: theme.panelAlt
                ColumnLayout { anchors.fill: parent; anchors.margins: 8; spacing: 6
                    Text { text: selectedMission ? selectedMission.name : "No mission selected"; font.bold: true; color: theme.textPrimary }
                    Text { text: selectedMission && selectedMission.description ? selectedMission.description : ""; wrapMode: Text.WordWrap; color: theme.textMuted }
                    Text { text: selectedMission ? "State: " + selectedMission.state : ""; color: theme.textMuted }
                    Text { text: selectedMission ? "Elapsed: " + (selectedMission.elapsed ? selectedMission.elapsed : 0) + "s" : ""; color: theme.textMuted }
                    RowLayout { spacing: 6
                        Button {
                            text: "Start"
                            enabled: selectedMission && selectedMission.state !== 'running'
                            onClicked: {
                                backend.startMission(selectedMission.id)
                                refreshMissions()
                            }
                            background: Rectangle { color: theme.accent; radius: 6 }
                            contentItem: Text { text: qsTr("Start"); color: theme.panel; font.bold: true }
                        }
                        Button {
                            text: "Pause"
                            enabled: selectedMission && selectedMission.state === 'running'
                            onClicked: {
                                backend.pauseMission(selectedMission.id)
                                refreshMissions()
                            }
                            background: Rectangle { color: theme.panelAlt; radius: 6 }
                            contentItem: Text { text: qsTr("Pause"); color: theme.textPrimary }
                        }
                        Button {
                            text: "Stop"
                            enabled: selectedMission && selectedMission.state !== 'stopped'
                            onClicked: {
                                backend.stopMission(selectedMission.id)
                                refreshMissions()
                            }
                            background: Rectangle { color: theme.danger; radius: 6 }
                            contentItem: Text { text: qsTr("Stop"); color: theme.panel }
                        }
                    }
                }
            }
        }

        // Tasks UI removed — missions are name/description/duration only

    }

    Connections { target: backend; function onMissionsUpdated() { missionDialog.refreshMissions() } }

    // Update selected mission when backend emits progress for smoother elapsed updates
    Connections {
        target: backend
        function onMissionProgress(m) {
            try {
                if (selectedMission && m.id === selectedMission.id) {
                    // replace selectedMission with fresh object so bindings update
                    selectedMission = m
                }
            } catch (e) {}
        }
    }

    Component.onCompleted: refreshMissions()

    function selectMissionById(id) {
        if (!id) return
        for (var i=0;i<missions.length;++i) {
            if (missions[i].id === id) {
                selectedMission = missions[i]
                missionList.currentIndex = i
                missionList.positionViewAtIndex(i, ListView.Center)
                return
            }
        }
    }
}
