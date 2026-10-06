# Desktop appearance

The bundled GTK3 Rose-Pine theme is the existing local theme from this rice,
originally distributed by Fausto Korpsvart's Rose-Pine-GTK-Theme project:
https://github.com/Fausto-Korpsvart/Rose-Pine-GTK-Theme (GPL-3.0).
The missing `px` unit on a header-bar rule is corrected in both stylesheets.
Only GTK3 files and their image assets are included; unused window-manager and
GNOME Shell themes are omitted. GTK settings are applied by setup-thunar.py.

Qt uses the shared Papirus icons and JetBrainsMono font. Hyprland selects Kvantum
through its toolkit environment variables; no separate Kvantum theme is required.
