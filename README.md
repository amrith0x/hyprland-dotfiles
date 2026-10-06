# Hyprland Dotfiles

My Arch Linux + Hyprland setup.

## Includes

- Hyprland
- Hyprlock
- Hypridle
- Waybar
- Kitty
- Fish
- Neovim
- Tofi
- Wlogout
- Wallpapers

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

## Wallpaper selector

Press **Super+Shift+W**. A full-screen
carousel displays tall wallpaper cards, with larger cards toward the center on
a transparent background, without labels or tooltips. Move the pointer over a side
card to slide it toward the center. Click a card to apply it with a fade; the
selector closes automatically after applying it. Scroll or use Left/Right
to browse, Enter to apply the focused wallpaper, and Escape or right-click to close.
Cards scale with the focused monitor's available logical resolution, including
1440p displays and HiDPI scaling.

Images are read from `assets/wallpapers` each time the selector opens. PNG, JPEG,
WebP, BMP, and GIF files are supported. The selected wallpaper is saved under
`~/.local/state/wallpaper-selector/current` (or `$XDG_STATE_HOME`) and restored
at login. This uses the existing `awww`, `python-gobject`, and `gtk-layer-shell`
dependencies. Run directly with:

```bash
python3 ~/.config/hypr/scripts/wallpaper-selector.py
```

## Bluetooth

Click the Bluetooth icon beside Wi-Fi in Waybar to open the matching device
panel. Turn Bluetooth on or off, scan for nearby devices, and click a device
to pair/connect or disconnect. Pairing prompts appear inside the panel. Escape
or clicking outside closes it and stops its scan.

Bluetooth requires the `bluez` package and its service:

```bash
sudo systemctl enable --now bluetooth.service
```

## Shortcut mappings

Super is the Windows key. These are the explicit mappings in this repository;
applications also have their own default shortcuts.

| Shortcut | Action |
| --- | --- |
| Super+T | Kitty terminal |
| Super+Q | Close active window |
| Super+M | Exit Hyprland (hyprshutdown if available) |
| Super+F | Dolphin file manager |
| Super+W | Toggle floating window |
| Super+Shift+W | Wallpaper selector |
| Super+A | Tofi application launcher |
| Super+R | Toggle pseudotiling |
| Super+J | Toggle split direction (dwindle) |
| Super+B | Firefox (Flatpak) |
| Super+C | VS Code |
| Ctrl+Escape | Run `killall waybar || waybar` (stops running Waybar; starts it if absent) |
| Super+V | Clipboard history through Tofi |
| Super+P | Pick color and copy to clipboard |
| Super+L | Lock screen |
| Super+Escape | Wlogout power menu |
| Super+Arrow keys | Focus window in that direction |
| Super+1–9 / 0 | Switch to workspace 1–9 / 10 |
| Super+Shift+1–9 / 0 | Move window to workspace 1–9 / 10 |
| Super+S | Toggle `magic` scratchpad |
| Super+Shift+S | Select screenshot region and copy to clipboard |
| Super+Scroll down / up | Next / previous existing workspace |
| Super+Left mouse drag | Move window |
| Super+Right mouse drag | Resize window |
| Volume up / down | Adjust volume by 5% (maximum 100%) |
| Speaker mute | Toggle output mute |
| Microphone mute | Toggle input mute |
| Brightness up / down | Adjust brightness by 5% |
| Media next / previous | Next / previous track |
| Media play / pause | Toggle playback |
| Three-finger horizontal swipe | Switch workspace |

Inside Wlogout: **S** shuts down, **U** suspends, **L** locks, **E** logs out,
and **R** reboots. No additional key mappings are defined in the tracked Kitty,
Fish, or Neovim configuration.

The current Super+V command begins with `exec,`, which may prevent the clipboard
picker from launching. The Ctrl+Escape command also stops Waybar on its first
press rather than restarting it.
