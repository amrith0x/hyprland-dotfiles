# Pear Desktop rice

The main installer installs `pear-desktop-bin` and creates first-launch settings.
To reapply settings after quitting Pear completely, run:

```sh
python3 ~/dotfiles/scripts/setup-pear.py --create
```

The setup preserves other settings and theme paths, backs up config.json, adds
the generated CSS, hides the native menu (Alt reveals it), and enables the
Shortcuts plugin for MPRIS. Hyprland continues to handle hardware media keys.
If multiple app configs exist, use `--config /path/to/config.json`.

`theme.css.in` controls the layout and styling. The wallpaper generator writes
`theme.css` with the same colors as Waybar and Kitty. Reopen Pear after changing
wallpapers to load its new palette. Album artwork is preserved.

Waybar displays Pear's `YoutubeMusic` MPRIS player next to workspaces. Click to
play/pause, right-click for next, or middle-click for previous. The module hides
when Pear is closed. Reload Waybar after first applying the bar configuration.
Hover over the track to expand a drawer with previous, play/pause, and next
buttons. The middle icon follows the player's playback state.
