// Based on sddm-astronaut-theme by Keyitdev; GPL-3.0-or-later.
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

RowLayout {
    id: powerButtons
    spacing: 12
    property ComboBox exposedSession
    property Item firstButton: buttonRepeater.itemAt(0)
    property var shutdown: ["Shutdown", config.TranslateShutdown || textConstants.shutdown, sddm.canPowerOff]
    property var reboot: ["Reboot", config.TranslateReboot || textConstants.reboot, sddm.canReboot]
    property var suspend: ["Suspend", config.TranslateSuspend || textConstants.suspend, sddm.canSuspend]
    property var hibernate: ["Hibernate", config.TranslateHibernate || textConstants.hibernate, sddm.canHibernate]

    Repeater {
        id: buttonRepeater
        model: [powerButtons.shutdown, powerButtons.reboot, powerButtons.suspend, powerButtons.hibernate]
        Button {
            id: powerButton
            objectName: "power-" + modelData[0].toLowerCase()
            Layout.preferredWidth: 108
            Layout.preferredHeight: 88
            padding: 12
            property bool emphasized: hovered || visualFocus
            text: modelData[1]
            font.family: root.font.family
            font.pixelSize: 14
            font.weight: Font.DemiBold
            icon.source: Qt.resolvedUrl("../Assets/" + modelData[0] + ".svg")
            icon.width: 28
            icon.height: 28
            icon.color: emphasized ? config.HoverSystemButtonsIconsColor : config.SystemButtonsIconsColor
            palette.buttonText: icon.color
            display: AbstractButton.TextUnderIcon
            visible: config.HideSystemButtons != "true" && (config.BypassSystemButtonsChecks == "true" || modelData[2])
            hoverEnabled: true
            scale: down ? 0.97 : emphasized ? 1.05 : 1.0
            Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            Behavior on icon.color { ColorAnimation { duration: 150 } }
            background: Rectangle {
                radius: 18
                color: powerButton.down ? Qt.lighter(config.BackgroundColor, 1.6)
                       : powerButton.emphasized ? Qt.lighter(config.BackgroundColor, 1.35)
                       : config.BackgroundColor
                border.width: powerButton.emphasized ? 2 : 1
                border.color: powerButton.emphasized ? config.HoverSystemButtonsIconsColor
                              : Qt.alpha(config.SystemButtonsIconsColor, 0.55)
                Behavior on color { ColorAnimation { duration: 150 } }
                Behavior on border.color { ColorAnimation { duration: 150 } }
            }
            Keys.onReturnPressed: clicked()
            Keys.onEnterPressed: clicked()
            KeyNavigation.left: index > 0 ? buttonRepeater.itemAt(index - 1) : null
            KeyNavigation.right: index < buttonRepeater.count - 1 ? buttonRepeater.itemAt(index + 1) : powerButtons.exposedSession
            onClicked: {
                powerButtons.forceActiveFocus()
                if (index === 0) sddm.powerOff()
                else if (index === 1) sddm.reboot()
                else if (index === 2) sddm.suspend()
                else sddm.hibernate()
            }
        }
    }
}
