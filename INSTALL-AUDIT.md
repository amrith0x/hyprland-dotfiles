# Rice installation audit

Audited 2026-10-07 against the configured Arch + Hyprland desktop.

## Reproduction

```bash
./install.sh --dry-run --with-nvidia --with-sddm
./install.sh --with-nvidia --with-sddm
```

The installer must run as the desktop user. It uses sudo for official packages,
system services and optional SDDM installation. It bootstraps yay when needed,
installs AUR packages, configures Firefox's Flatpak, generates all wallpaper
includes and links eleven Stow packages. Existing foreign configs are backed up.
Pear is configured before first launch; an already-running Pear is left running
and prints the command to refresh settings after it quits.

| Component | Recreated by |
| --- | --- |
| Hyprland layout, opacity, keybinds, Num Lock | hypr Stow package |
| Wallpaper gallery, lock background and palettes | bundled wallpapers + wallpaper-theme.py |
| Waybar hardware/audio drawers and Pear media controls | waybar Stow package + playerctl |
| Wi-Fi and Bluetooth panels | NetworkManager, BlueZ, Python/GTK3/layer shell |
| Glass power dock | custom GTK panel; wlogout application is no longer needed |
| Thunar appearance, preferences and folder handler | bundled Rose-Pine GTK3 theme + setup-thunar.py |
| Kitty/Fish images and prompt | bundled portrait assets + Kitty renderer + Starship |
| mpv/uosc | bundled 5.13.0 scripts, fonts and Linux helper + generated config |
| Pear Desktop | pear-desktop-bin + setup-pear.py + generated CSS |
| Firefox and VS Code keybind targets | Firefox Flatpak + visual-studio-code-bin |
| Desktop audio and file dialogs | PipeWire/PulseAudio bridge, WirePlumber and portals |
| Login theme, physical keyboard and Num Lock | --with-sddm + sync-theme.py + install-theme.py |
| NVIDIA support on this laptop | --with-nvidia |

The default wallpaper is main.png. Existing wallpaper selection is retained.
This laptop's eDP-1 monitor rule and hardware labels are intentionally preserved.
Versions follow Arch/AUR repositories rather than a pinned OS image. Sign-in
sessions, credentials, unrelated applications and personal browser data are
excluded. A fresh machine still needs SDDM enabled if it is the selected display
manager; the installer avoids interrupting an existing graphical session.

## Validation

```bash
python3 -B scripts/audit-install.py
```

This checks Python/Bash/Lua/QML syntax, GTK CSS including the bundled theme,
static/dynamic palette output, new-profile Stow installation and repeat Stow,
Pear first-launch setup and setting preservation, and every installer flag
combination. It uses a temporary checkout/profile and never substitutes the
real home directory. QML checks require qmllint from qt6-declarative.
Official package names were checked against the configured pacman databases.
Ctrl+Escape now reloads Waybar rather than stopping it on the first press.
The existing desktop's greeter test mode, mpv/uosc and Pear/MPRIS were also
validated during setup. A full Arch reinstall and real SDDM authentication have
not been exercised by this audit.

## Cleanup

Removed the obsolete wlogout stylesheet and unused macOS/Windows uosc binaries.
Session-created download metadata, release ZIP and preview files were removed
from /tmp. Generated palettes and active wallpaper caches remain ignored.
Root-owned installer bytecode and the four audited unused packages were removed
on this machine and verified absent. The same cleanup can be rerun with:

```bash
bash scripts/cleanup-packages.sh --dry-run
bash scripts/cleanup-packages.sh --apply
```

Targets: numlockx, wlogout, pear-desktop-bin-debug and yay-debug. The script uses
nonrecursive package removal so it cannot remove GTK dependencies used by custom
panels. Other orphan packages are retained: polkit-kde-agent, for example, is
actively launched by this rice even though pacman previously listed it as an
orphan. Application caches and rollback backups are preserved.
