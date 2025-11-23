import QtQuick 2.15

Item {
    id: root
    property real value: 0
    property real maximum: 100
    property string label: ""
    width: 180; height: 180

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext('2d');
            ctx.reset();
            var w = width, h = height;
            var cx = w/2, cy = h/2;
            var r = Math.min(w,h)/2 - 12;
            ctx.clearRect(0,0,w,h);

            // Enhanced background with multiple layers
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, 2*Math.PI);
            var grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
            grad.addColorStop(0, 'rgba(2,12,20,0.9)');
            grad.addColorStop(1, 'rgba(8,16,20,0.65)');
            ctx.fillStyle = grad;
            ctx.fill();

            // Outer rim
            ctx.beginPath();
            ctx.lineWidth = 3;
            ctx.strokeStyle = 'rgba(26,74,106,0.8)';
            ctx.arc(cx, cy, r-2, 0, 2*Math.PI);
            ctx.stroke();

            // Track arc with enhanced styling
            ctx.beginPath();
            ctx.lineWidth = 10;
            ctx.strokeStyle = 'rgba(255,255,255,0.08)';
            ctx.lineCap = 'round';
            ctx.arc(cx, cy, r-15, -Math.PI*0.75, Math.PI*0.75);
            ctx.stroke();

            // Value arc with gradient
            var norm = Math.max(0, Math.min(value/maximum, 1));
            var start = -Math.PI*0.75;
            var span = norm * (Math.PI*1.5);
            
            if (span > 0) {
                ctx.beginPath();
                ctx.lineWidth = 10;
                var color = '#00BFFF';
                if (label.indexOf('OXYGEN') !== -1 || label.indexOf('Oxygen') !== -1) color = '#7CFC00';
                else if (label.indexOf('POWER') !== -1 || label.indexOf('Battery') !== -1) color = '#FFD700';
                else if (label.indexOf('CARBON') !== -1) color = '#FFA500';
                
                // Create glow effect
                ctx.shadowColor = color;
                ctx.shadowBlur = 15;
                ctx.strokeStyle = color;
                ctx.lineCap = 'round';
                ctx.arc(cx, cy, r-15, start, start+span);
                ctx.stroke();
                ctx.shadowBlur = 0;
            }

            // Center value with enhanced styling
            ctx.fillStyle = '#e0ffff';
            ctx.font = 'bold ' + Math.round(r/2.2) + 'px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            var display = (label.indexOf('CO2')!==-1) ? (value.toFixed(2)) : Math.round(value)+'';
            ctx.fillText(display, cx, cy-8);

            // Unit text
            ctx.fillStyle = '#88ccdd';
            ctx.font = Math.round(r/5) + 'px monospace';
            var unit = '%';
            ctx.fillText(unit, cx, cy + r/3);
            
            // Status indicators
            var status = "NOMINAL";
            var statusColor = '#00ff88';
            if (norm < 0.2) { status = "CRITICAL"; statusColor = '#ff4444'; }
            else if (norm < 0.4) { status = "LOW"; statusColor = '#ffaa44'; }
            
            ctx.fillStyle = statusColor;
            ctx.font = Math.round(r/8) + 'px monospace';
            ctx.fillText(status, cx, cy + r/1.8);
        }
    }

    onValueChanged: canvas.requestPaint()
    onMaximumChanged: canvas.requestPaint()
    Component.onCompleted: canvas.requestPaint()

    Text {
        text: label
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.bottom
        anchors.topMargin: 8
        color: '#88ccdd'
        font.pixelSize: 12
        font.family: "monospace"
        font.bold: true
    }
}
