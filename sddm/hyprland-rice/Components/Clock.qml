import QtQuick 2.15
import QtQuick.Controls 2.15

Label {
    id: clock
    color: config.TimeTextColor
    font.family: config.Font
    font.pixelSize: Math.min(73, root.width * 0.06)
    font.weight: Font.DemiBold
    renderType: Text.QtRendering
    function updateTime() { text = Qt.formatTime(new Date(), "h:mm AP") }
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: clock.updateTime()
    }
    Component.onCompleted: updateTime()
}
