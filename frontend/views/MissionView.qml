import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

Rectangle {
    id: missionView
    width: parent.width
    height: 260
    color: "transparent"
    radius: 8

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Text { text: "Missions"; color: "#dff6f6"; font.pixelSize: 14; font.bold: true }

        RowLayout {
            spacing: 12

            MissionList {
                id: missionsListComp
                Layout.preferredWidth: 260
                Layout.preferredHeight: 200
                model: []
                onMissionSelected: function(m) {
                    selectedMission = m
                }
            }

            MissionDetail {
                id: detailComp
                Layout.preferredWidth: 360
                Layout.preferredHeight: 200
                mission: selectedMission
                tasksModel: tasksModel
            }
        }
    }

    property var selectedMission: null
    property var tasksModel: []

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: {
            // Prefer the direct `missionManager` context property (exposed from Python)
            var mm = missionManager ? missionManager : (backend && backend.missionManager ? backend.missionManager : null)
            if (mm) {
                var all = []
                try {
                    if (mm.getAllWithProgress) all = mm.getAllWithProgress()
                    else if (mm.listMissions) all = mm.listMissions()
                } catch (e) {
                    console.log("MissionView: error fetching missions", e)
                }
                console.log("MissionView: fetched missions count", all ? (all.length !== undefined ? all.length : typeof all) : all)
                // ensure model is always an array
                missionsListComp.model = all || []

                if (selectedMission && all && all.length) {
                    for (var i=0;i<all.length;i++) { if (all[i].id === selectedMission.id) { selectedMission = all[i]; break } }
                    tasksModel = selectedMission ? selectedMission.tasks : []
                } else if (all && all.length>0) {
                    selectedMission = all[0]
                    tasksModel = selectedMission.tasks
                }
            }
        }
    }
}
