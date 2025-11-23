import QtQuick 2.15

Item {
    id: root
    property real value: 0
    property real maximum: 100
    property string label: ""
    implicitWidth: 160
    implicitHeight: 160

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext('2d');
            ctx.reset();
            var w = width, h = height;
            var cx = w/2, cy = h/2;
            var r = Math.min(w,h)/2 - 8;
            ctx.clearRect(0,0,w,h);

            // subtle inner background
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, 2*Math.PI);
            ctx.fillStyle = 'rgba(8,16,20,0.65)';
            ctx.fill();

            // track arc
            ctx.beginPath();
            ctx.lineWidth = 8;
            ctx.strokeStyle = 'rgba(255,255,255,0.06)';
            ctx.lineCap = 'round';
            ctx.arc(cx, cy, r-10, -Math.PI*0.75, Math.PI*0.75);
            ctx.stroke();

            // value arc
            var norm = Math.max(0, Math.min(value/maximum, 1));
            var start = -Math.PI*0.75;
            var span = norm * (Math.PI*1.5);
            ctx.beginPath();
            ctx.lineWidth = 8;
            var color = '#FFD700';
            if (label.indexOf('Oxygen') !== -1) color = '#7CFC00';
            else if (label.indexOf('Battery') !== -1) color = '#00BFFF';
            else if (label.indexOf('Carbon') !== -1) color = '#FFA500';
            ctx.strokeStyle = color;
            ctx.lineCap = 'round';
            ctx.arc(cx, cy, r-10, start, start+span);
            ctx.stroke();

            // center value
            ctx.fillStyle = 'white';
            ctx.font = Math.round(r/2.7) + 'px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            var display = (label.indexOf('CO2')!==-1) ? (value.toFixed(2)) : Math.round(value)+'';
            ctx.fillText(display, cx, cy);

            // small unit text
            ctx.fillStyle = 'lightgray';
            ctx.font = Math.round(r/6) + 'px sans-serif';
            var unit = (label.indexOf('CO2')!==-1) ? '%' : '%';
            ctx.fillText(unit, cx, cy + r/2.6);
        }
    }

    onValueChanged: canvas.requestPaint()
    onMaximumChanged: canvas.requestPaint()
    Component.onCompleted: canvas.requestPaint()

    Text {
        text: label
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.bottom
        color: 'lightgray'
        font.pixelSize: 12
    }
}