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
- Thunar
- Dunst notifications
- Matching SDDM login theme (optional)
- Wallpapers

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

The installer enables NetworkManager and Bluetooth immediately and at boot.
It also installs the Python/GTK dependencies for the wallpaper, Wi-Fi, and
Bluetooth selectors, plus the Fish prompt and Fastfetch dependencies. Thunar,
thumbnails, archive handling, Papirus icons, and dynamic Dunst notifications
are configured automatically. Existing Thunar/Dunst configurations and any
modified GTK settings are backed up before replacement.

To include the matching SDDM login screen:

```bash
./install.sh --with-sddm
```

This installs SDDM and its Qt theme dependencies, refreshes the login background
and colors from the wallpaper, and installs the theme with a configuration
backup. It does not restart or enable the display-manager service. On a fresh
machine, enable SDDM separately if it is your chosen display manager.
See [SDDM setup and rollback](sddm/README.md). Both optional flags can be combined:

```bash
./install.sh --with-nvidia --with-sddm
```

For this laptop's RTX 2060 with the standard Arch `linux` kernel, use:

```bash
./install.sh --with-nvidia
```

This adds the packages in `packages-nvidia.txt`. The open NVIDIA driver requires
a Turing or newer GPU; other kernels or older GPUs need an appropriate driver.
Reboot after installing the driver, then run `nvidia-smi` to check GPU readings.

## Window appearance and Waybar

Active windows use 90% opacity, inactive windows 70%, with 5px corners and
Catppuccin blue/mauve borders. Waybar uses a 12-hour clock with AM/PM and shows
CPU, RAM, and NVIDIA GPU usage; hover expands CPU/GPU temperatures and shows
the hardware models. Battery hover shows remaining runtime when unplugged,
Charging when plugged in, or Fully charged. The Bluetooth panel includes a
power slider. These settings are installed through the existing Stow packages.
Discord and Firefox's YouTube, fullscreen, and picture-in-picture windows stay
fully opaque. Automatic idle dimming, locking, screen-off, and suspend are
currently disabled; **Super+L** still locks manually. Hyprlock uses the wallpaper,
a 12-hour clock, and no greeting. The terminal-inhibitor helper is available in
the scripts directory but is not started while automatic idle handling is disabled.

## Thunar

**Super+F** opens Thunar, the default handler for folders. It uses Papirus-Dark
icons, a compact toolbar, breadcrumb navigation, a Places sidebar, and local
image thumbnails. Right-click a folder for **Open Kitty here**; Xarchiver handles
archive creation/extraction through the archive plugin. Existing GTK settings
are backed up under `~/.dotfiles-backup/thunar-*` when setup changes them.

Thunar's backgrounds, sidebar, selections, and toolbar accents use the same
wallpaper palette as Waybar and Kitty. The wallpaper generator updates
`thunar/.config/thunar-rice/wallpaper-colors.css` automatically. Close all Thunar
windows and reopen it to reload newly generated colors. Papirus icons are shared
with other GTK apps; the custom colors are scoped to Thunar.

To reapply preferences and the default folder handler after Stow:

```bash
python3 scripts/setup-thunar.py
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

## Wallpaper colors and lock screen

Wallpaper colors update automatically when you select an image. New images added
to `assets/wallpapers` appear the next time the selector opens. The lock screen
uses the selected wallpaper too; animated wallpapers use a still first frame.

The installer generates the palette files before linking the configs. To refresh
the palette manually:

```bash
python3 ~/.config/hypr/scripts/wallpaper-theme.py enable
```

This recolors Hyprland borders, Waybar, Wi-Fi/Bluetooth panels, Kitty, Tofi, Thunar, Dunst,
Wlogout, and Hyprlock. The palette stays dark; opacity, rounding, layout, and
warning colors are preserved. Open panels and the lock screen pick up changes
the next time they open. Application themes such as VS Code and Neovim
are not included.

Dunst notifications use dark wallpaper-colored surfaces, matching fonts and
corners, and a wallpaper-derived accent border. Colors live in a generated
`dunstrc.d/wallpaper-colors.conf` drop-in; selecting a wallpaper reloads Dunst
automatically without restarting it. Critical notifications retain a pink/red
border and remain visible until dismissed. Left-click dismisses one notification;
right-click dismisses all, and middle-click invokes an available action.

To switch back to the static colors and disable automatic recoloring:

```bash
python3 ~/.config/hypr/scripts/wallpaper-theme.py revert
```

The main configs load separate generated `wallpaper-colors.*` files, so changing
a wallpaper does not rewrite your layout or keybinds. Generated palettes, the
lock-screen image, and `.theme-runtime/` caches are ignored by Git. No trial
backups are required. `status` reports whether automatic recoloring is enabled.
The installer includes Matugen; a local copy is also supported.

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
| Super+F | Thunar file manager |
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
