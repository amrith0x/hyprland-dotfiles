#!/usr/bin/env bash
set -euo pipefail

DOTFILES_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config"
BACKUP_DIR="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S-%N)"
INSTALL_NVIDIA=false
INSTALL_SDDM=false
DRY_RUN=false
for argument in "$@"; do
    case "$argument" in
        --with-nvidia) INSTALL_NVIDIA=true ;;
        --with-sddm) INSTALL_SDDM=true ;;
        --dry-run) DRY_RUN=true ;;
        -h|--help)
            echo "Usage: ./install.sh [--with-nvidia] [--with-sddm] [--dry-run]"
            echo "  --with-nvidia  NVIDIA open driver for Turing/newer GPUs and the stock linux kernel."
            echo "  --with-sddm    Install the matching login screen and enable Num Lock."
            echo "  --dry-run      Print the complete installation plan without changing anything."
            exit 0 ;;
        *) echo "Unknown option: $argument" >&2; exit 1 ;;
    esac
done
if (( EUID == 0 )); then
    echo "Run as your desktop user, not root; the script uses sudo only where needed." >&2
    exit 1
fi
if [[ "${XDG_CONFIG_HOME:-$CONFIG_DIR}" != "$CONFIG_DIR" ]]; then
    echo "This Stow layout requires XDG_CONFIG_HOME to be ~/.config." >&2
    exit 1
fi
if ! $DRY_RUN && ! command -v pacman >/dev/null; then
    echo "This installer supports Arch-based systems only." >&2
    exit 1
fi

run() {
    if $DRY_RUN; then
        printf '[plan]'; printf ' %q' "$@"; printf '\n'
    else
        "$@"
    fi
}
read_packages() { sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$1"; }
STOW_PACKAGES=(hypr waybar kitty fish nvim rofi wlogout thunar dunst mpv desktop)
for package in "${STOW_PACKAGES[@]}"; do
    [[ -d "$DOTFILES_DIR/$package" ]] || { echo "Missing Stow package: $package" >&2; exit 1; }
done
for file in packages-pacman.txt packages-aur.txt packages-nvidia.txt packages-sddm.txt; do
    [[ -f "$DOTFILES_DIR/$file" ]] || { echo "Missing manifest: $file" >&2; exit 1; }
done
mapfile -t OFFICIAL_PACKAGES < <(read_packages "$DOTFILES_DIR/packages-pacman.txt")
mapfile -t AUR_PACKAGES < <(read_packages "$DOTFILES_DIR/packages-aur.txt")
if $INSTALL_NVIDIA; then
    mapfile -t EXTRA_PACKAGES < <(read_packages "$DOTFILES_DIR/packages-nvidia.txt")
    OFFICIAL_PACKAGES+=("${EXTRA_PACKAGES[@]}")
fi
if $INSTALL_SDDM; then
    mapfile -t EXTRA_PACKAGES < <(read_packages "$DOTFILES_DIR/packages-sddm.txt")
    OFFICIAL_PACKAGES+=("${EXTRA_PACKAGES[@]}")
fi
run sudo pacman -S --needed "${OFFICIAL_PACKAGES[@]}"
run sudo systemctl enable --now NetworkManager.service bluetooth.service

# Install an AUR helper on a fresh Arch machine, using the user's account for makepkg.
if command -v yay >/dev/null; then
    AUR_HELPER=yay
elif command -v paru >/dev/null; then
    AUR_HELPER=paru
elif $DRY_RUN; then
    echo "[plan] Build yay from https://aur.archlinux.org/yay.git using makepkg -si."
    AUR_HELPER=yay
else
    AUR_BUILD_DIR="$(mktemp -d -t dotfiles-yay.XXXXXXXX)"
    trap 'rm -rf -- "$AUR_BUILD_DIR"' EXIT
    git clone https://aur.archlinux.org/yay.git "$AUR_BUILD_DIR/yay"
    (cd "$AUR_BUILD_DIR/yay" && makepkg -si)
    AUR_HELPER=yay
fi
run "$AUR_HELPER" -S --needed "${AUR_PACKAGES[@]}"

# Super+B and the Fish wrapper use the Firefox Flatpak.
if $DRY_RUN || ! flatpak info org.mozilla.firefox >/dev/null 2>&1; then
    run flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    run flatpak install --user --noninteractive flathub org.mozilla.firefox
fi

# Generate ignored includes before Stow, including mpv and Pear themes.
run python3 "$DOTFILES_DIR/hypr/.config/hypr/scripts/wallpaper-theme.py" apply --no-reload

backup_path() {
    local relative="$1" target="$HOME/$1"
    if [[ -L "$target" ]] && [[ "$(realpath -m -- "$target")" == "$DOTFILES_DIR/"* ]]; then
        return
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        run mkdir -p "$BACKUP_DIR/$(dirname -- "$relative")"
        run mv -- "$target" "$BACKUP_DIR/$relative"
    fi
}
for package in "${STOW_PACKAGES[@]}"; do
    case "$package" in
        thunar) backup_path .config/Thunar; backup_path .config/thunar-rice ;;
        desktop) backup_path .config/qt6ct; backup_path .local/share/themes/Rose-Pine ;;
        *) backup_path ".config/$package" ;;
    esac
done
# Remove only the obsolete launcher link belonging to this checkout.
if [[ -L "$CONFIG_DIR/tofi" ]] && [[ "$(realpath -m -- "$CONFIG_DIR/tofi")" == "$DOTFILES_DIR/tofi/.config/tofi" ]]; then
    run unlink "$CONFIG_DIR/tofi"
fi
for package in "${STOW_PACKAGES[@]}"; do
    run stow --dir="$DOTFILES_DIR" --restow --target="$HOME" "$package"
done

if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    run python3 "$DOTFILES_DIR/scripts/setup-thunar.py"
else
    run dbus-run-session -- python3 "$DOTFILES_DIR/scripts/setup-thunar.py"
fi
run python3 "$DOTFILES_DIR/scripts/setup-pear.py" --create --defer-running
if $INSTALL_SDDM; then
    run python3 "$DOTFILES_DIR/sddm/sync-theme.py"
    run sudo python3 -B "$DOTFILES_DIR/sddm/install-theme.py" "$DOTFILES_DIR/sddm/hyprland-rice"
fi
if $DRY_RUN; then
    echo "Dry run complete; no files, packages, or services changed."
else
    echo "Rice installed. Existing configurations, if replaced, are in $BACKUP_DIR."
    echo "Kitty starts Fish automatically. To make Fish your login shell: chsh -s /usr/bin/fish"
    echo "Select Hyprland at login. Personal accounts still require signing in."
    if $INSTALL_SDDM; then
        echo "SDDM theme installed; the display manager was not enabled or restarted."
        echo "For a fresh machine using SDDM: sudo systemctl enable sddm.service"
    fi
    if $INSTALL_NVIDIA; then
        echo "Reboot to load the NVIDIA driver, then verify with nvidia-smi."
    fi
fi
