// Based on sddm-astronaut-theme by Keyitdev; GPL-3.0-or-later.
import QtQuick 2.15
import SddmComponents 2.0 as SDDM

Item {
    id: formContainer
    SDDM.TextConstants { id: textConstants }
    Input {
        id: input
        width: Math.min(280, parent.width - 48)
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -20
    }
    SessionButton {
        id: sessionSelect
        width: 280
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 40
    }
    SystemButtons {
        id: systemButtons
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 36
        anchors.bottomMargin: 36
        exposedSession: input.exposeSession
    }
}
