# Hyprland Rice SDDM theme

Uses the current Hyprlock wallpaper and generated palette, JetBrains Mono Nerd Font,
rounded charcoal login fields, and a bottom-right 12-hour clock with AM/PM.
No greeting is displayed. User/session selection and power controls remain available. Power buttons have opaque charcoal cards and animated lavender hover/focus borders.

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
/usr/share/sddm/themes/hyprland-rice, and updates the Theme Current selection plus General InputMethod=
in /etc/sddm.conf to disable the automatic on-screen keyboard. Existing configuration is backed up under
/var/backups/sddm-hyprland-rice/<timestamp>/sddm.conf. SDDM is not restarted.
Re-run the installer after changing wallpapers to synchronize the login screen.
The main bootstrap also supports `./install.sh --with-sddm`, optionally combined
with `--with-nvidia`. Both installation paths install the packages listed in
`packages-sddm.txt`. Neither path enables or restarts the display manager.
The staged background is generated locally and is not committed.

To revert, copy the printed backup's sddm.conf to /etc/sddm.conf using sudo.
Hyprlock changes have their own backup under ~/dotfiles-backup/login-theme-*.

Validation: greeter test mode loaded successfully; a Qt Quick render was visually
inspected. Authentication was not tested in a real SDDM session.
