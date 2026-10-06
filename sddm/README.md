# Hyprland Rice SDDM theme

Uses the current Hyprlock wallpaper and generated palette, JetBrains Mono Nerd Font,
rounded charcoal login fields, and a bottom-right 12-hour clock with AM/PM.
No greeting is displayed. User/session selection and power controls remain available.
Num Lock is enabled by the installer. Hyprland enables it separately for the desktop.
To apply just the login-screen setting to an existing installation:

```sh
sudo python3 ~/dotfiles/sddm/enable-numlock.py
```

Power controls use 34px icons and bright 13px labels without card backgrounds or borders.
Hover or keyboard focus smoothly lifts the icon and adds a wallpaper-accent neon glow,
with a glowing underline. Pressing gives a subtle compression animation.

Based on Keyitdev/sddm-astronaut-theme, GPL-3.0-or-later; see hyprland-rice/LICENSE.

Preview in your desktop terminal:

```sh
python3 ~/dotfiles/hypr/.config/hypr/scripts/wallpaper-theme.py apply --no-reload
python3 ~/dotfiles/sddm/sync-theme.py
sddm-greeter-qt6 --test-mode --theme ~/dotfiles/sddm/hyprland-rice
```

Install:

```sh
bash ~/dotfiles/sddm/install.sh
```

The installer refreshes the wallpaper and palette, installs a separate theme to
/usr/share/sddm/themes/hyprland-rice, and sets both General InputMethod and
QT_IM_MODULE in GreeterEnvironment to `compose` in /etc/sddm.conf. This selects
physical-keyboard input instead of the virtual-keyboard plugin. The theme has no
virtual-keyboard components or controls. Existing configuration is backed up under
/var/backups/sddm-hyprland-rice/<timestamp>/sddm.conf. SDDM is not restarted.
Re-run the installer after changing wallpapers to synchronize the login screen.
The main bootstrap also supports `./install.sh --with-sddm`, optionally combined
with `--with-nvidia`. Both installation paths install the packages listed in
`packages-sddm.txt`. Neither path enables or restarts the display manager.
The staged background is generated locally and is not committed.

To disable the keyboard on an existing installation without reinstalling the theme:

```sh
sudo python3 ~/dotfiles/sddm/disable-keyboard.py
sudo pacman -R qt6-virtualkeyboard
```

This updates the existing `virtualkbd.conf` override too. The change applies when
the next greeter is started. It does not restart SDDM or interrupt your session.

To revert, copy the printed backup's sddm.conf to /etc/sddm.conf using sudo.
Hyprlock configuration is tracked in the dotfiles repository.

Validation: greeter test mode loaded successfully; a Qt Quick render was visually
inspected. Authentication was not tested in a real SDDM session.
