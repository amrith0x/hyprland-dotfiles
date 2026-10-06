// Based on sddm-astronaut-theme by Keyitdev; GPL-3.0-or-later.
import QtQuick 2.15
import QtQuick.Controls 2.15
import "Components"

Pane {
    id: root
    width: 1920
    height: 1080
    padding: 0
    font.family: config.Font
    font.pointSize: Number(config.FontSize) || 14
    palette.window: config.BackgroundColor
    palette.highlight: config.HighlightBackgroundColor
    palette.highlightedText: config.HighlightTextColor
    palette.buttonText: config.SystemButtonsIconsColor
    background: Rectangle { color: config.BackgroundColor }

    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(config.Background)
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    LoginForm {
        id: form
        anchors.fill: parent
    }
    Clock {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: Math.min(100, root.width * 0.06)
        anchors.bottomMargin: 40
    }
    Loader {
        id: virtualKeyboard
        active: false
        visible: false
    }
}
