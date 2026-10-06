// Based on sddm-astronaut-theme by Keyitdev; GPL-3.0-or-later.
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import QtQuick.Controls.impl
import QtQuick.Effects

RowLayout {
    id: powerButtons
    spacing: 16
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
            Layout.preferredWidth: 110
            Layout.preferredHeight: 94
            padding: 8
            property bool emphasized: hovered || visualFocus
            property real glow: emphasized ? 1.0 : 0.0
            Behavior on glow { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
            text: modelData[1]
            font.family: root.font.family
            font.pixelSize: 13
            font.weight: Font.Medium
            icon.source: Qt.resolvedUrl("../Assets/" + modelData[0] + ".svg")
            icon.width: 34
            icon.height: 34
            icon.color: emphasized ? Qt.lighter(config.HoverSystemButtonsIconsColor, 1.12)
                                   : Qt.tint(config.SystemButtonsIconsColor, "#70ffffff")
            palette.buttonText: icon.color
            display: AbstractButton.TextUnderIcon
            visible: config.HideSystemButtons != "true" && (config.BypassSystemButtonsChecks == "true" || modelData[2])
            hoverEnabled: true
            scale: down ? 0.96 : emphasized ? 1.05 : 1.0
            transform: Translate {
                y: powerButton.down ? 0 : powerButton.emphasized ? -3 : 0
                Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            }
            Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on icon.color { ColorAnimation { duration: 180 } }
            contentItem: Column {
                spacing: 9
                IconImage {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: powerButton.icon.width
                    height: powerButton.icon.height
                    source: powerButton.icon.source
                    color: powerButton.icon.color
                    layer.enabled: true
                    layer.effect: MultiEffect {
                        shadowEnabled: true
                        shadowColor: config.HoverSystemButtonsIconsColor
                        shadowOpacity: powerButton.glow * 0.85
                        shadowBlur: 0.8
                        blurMax: 16
                        shadowHorizontalOffset: 0
                        shadowVerticalOffset: 0
                    }
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: powerButton.text
                    font: powerButton.font
                    color: powerButton.icon.color
                    style: Text.Outline
                    styleColor: Qt.alpha(config.BackgroundColor, 0.7)
                }
            }
            background: Item {
                // Quiet at rest: only a small accent underline appears on interaction.
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 2
                    width: powerButton.emphasized ? 34 : 12
                    height: 2
                    radius: 1
                    color: config.HoverSystemButtonsIconsColor
                    opacity: powerButton.emphasized ? 0.85 : 0
                    Behavior on width { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                    Behavior on opacity { NumberAnimation { duration: 180 } }
                    layer.enabled: true
                    layer.effect: MultiEffect {
                        shadowEnabled: true
                        shadowColor: config.HoverSystemButtonsIconsColor
                        shadowOpacity: powerButton.glow * 0.8
                        shadowBlur: 0.8
                        blurMax: 12
                        shadowHorizontalOffset: 0
                        shadowVerticalOffset: 0
                    }
                }
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
