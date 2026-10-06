#!/usr/bin/env bash
set -euo pipefail
THEME_SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mapfile -t SDDM_PACKAGES < <(grep -vE '^[[:space:]]*(#|$)' "$THEME_SOURCE_DIR/../packages-sddm.txt")
sudo pacman -S --needed "${SDDM_PACKAGES[@]}"
python3 "$THEME_SOURCE_DIR/../hypr/.config/hypr/scripts/wallpaper-theme.py" apply --no-reload
python3 "$THEME_SOURCE_DIR/sync-theme.py"
sudo python3 -B "$THEME_SOURCE_DIR/install-theme.py" "$THEME_SOURCE_DIR/hyprland-rice"
printf '\nTheme installed. It will appear at your next graphical login.\n'
printf 'SDDM was not restarted; your current session stays running.\n'
