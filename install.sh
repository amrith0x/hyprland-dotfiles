#!/usr/bin/env bash

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

PACMAN_FILE="$DOTFILES_DIR/packages-pacman.txt"
AUR_FILE="$DOTFILES_DIR/packages-aur.txt"
NVIDIA_FILE="$DOTFILES_DIR/packages-nvidia.txt"
SDDM_FILE="$DOTFILES_DIR/packages-sddm.txt"
INSTALL_NVIDIA=false
INSTALL_SDDM=false

for argument in "$@"; do
    case "$argument" in
        --with-nvidia) INSTALL_NVIDIA=true ;;
        --with-sddm) INSTALL_SDDM=true ;;
        -h|--help)
            echo "Usage: ./install.sh [--with-nvidia] [--with-sddm]"
            echo "  --with-nvidia  Install the NVIDIA open driver for Turing/newer GPUs and the stock linux kernel."
            echo "  --with-sddm    Install SDDM dependencies and the wallpaper-matched login theme."
            exit 0
            ;;
        *) echo "Unknown option: $argument" >&2; exit 1 ;;
    esac
done

STOW_PACKAGES=(
    hypr
    waybar
    kitty
    fish
    nvim
    tofi
    wlogout
    thunar
    dunst
)

echo "======================================"
echo "      Hyprland Bootstrap Installer"
echo "======================================"
echo

# --------------------------------------------------
# Arch check
# --------------------------------------------------

if ! command -v pacman >/dev/null 2>&1; then
    echo "[!] This installer currently supports Arch-based systems only."
    exit 1
fi

# --------------------------------------------------
# Read package file helper
# --------------------------------------------------

read_packages() {
    grep -vE '^[[:space:]]*(#|$)' "$1"
}

# --------------------------------------------------
# Official packages
# --------------------------------------------------

if [[ ! -f "$PACMAN_FILE" ]]; then
    echo "[!] Missing packages-pacman.txt"
    exit 1
fi

mapfile -t PACMAN_PACKAGES < <(read_packages "$PACMAN_FILE")

if $INSTALL_NVIDIA; then
    if [[ ! -f "$NVIDIA_FILE" ]]; then
        echo "[!] Missing packages-nvidia.txt" >&2
        exit 1
    fi
    mapfile -t NVIDIA_PACKAGES < <(read_packages "$NVIDIA_FILE")
    PACMAN_PACKAGES+=("${NVIDIA_PACKAGES[@]}")
fi

if $INSTALL_SDDM; then
    if [[ ! -f "$SDDM_FILE" ]]; then
        echo "[!] Missing packages-sddm.txt" >&2
        exit 1
    fi
    mapfile -t SDDM_PACKAGES < <(read_packages "$SDDM_FILE")
    PACMAN_PACKAGES+=("${SDDM_PACKAGES[@]}")
fi

echo "[+] Installing official Arch packages..."

sudo pacman -S --needed "${PACMAN_PACKAGES[@]}"

echo
echo "[✓] Official packages installed"
echo

# The selectors use system services; enable them once for subsequent boots.
echo "[+] Enabling Wi-Fi and Bluetooth services..."
sudo systemctl enable --now NetworkManager.service bluetooth.service

# --------------------------------------------------
# AUR helper
# --------------------------------------------------

if [[ -f "$AUR_FILE" ]]; then

    mapfile -t AUR_PACKAGES < <(read_packages "$AUR_FILE")

    if (( ${#AUR_PACKAGES[@]} > 0 )); then

        if command -v yay >/dev/null 2>&1; then
            echo "[+] Installing AUR packages with yay..."

            yay -S --needed "${AUR_PACKAGES[@]}"

        elif command -v paru >/dev/null 2>&1; then
            echo "[+] Installing AUR packages with paru..."

            paru -S --needed "${AUR_PACKAGES[@]}"

        else
            echo "[!]"
            echo "[!] AUR packages are required but no AUR helper was found."
            echo
            echo "Required AUR packages:"
            printf '    - %s\n' "${AUR_PACKAGES[@]}"
            echo
            echo "Install yay or paru, then run this script again."
            exit 1
        fi

        echo
        echo "[✓] AUR packages installed"
        echo
    fi
fi

# --------------------------------------------------
# Validate Stow packages
# --------------------------------------------------

echo "[+] Checking dotfile packages..."

for package in "${STOW_PACKAGES[@]}"; do
    if [[ ! -d "$DOTFILES_DIR/$package" ]]; then
        echo "[!] Missing dotfile package: $package"
        exit 1
    fi

    echo "    ✓ $package"
done

# --------------------------------------------------
# Backup configs
# --------------------------------------------------

# Generate included files before moving any existing configuration out of the way.
echo "[+] Preparing wallpaper colors and lock-screen background..."
python3 "$DOTFILES_DIR/hypr/.config/hypr/scripts/wallpaper-theme.py" apply --no-reload

backup_config() {

    local name="$1"
    if [[ "$name" == thunar ]]; then
        backup_config Thunar
        backup_config thunar-rice
        return
    fi
    local target="$HOME/.config/$name"

    if [[ -L "$target" ]]; then
        return
    fi

    if [[ -e "$target" ]]; then

        mkdir -p "$BACKUP_DIR/.config"

        echo "[+] Backing up existing $name"
        mv "$target" "$BACKUP_DIR/.config/"
    fi
}

echo
echo "[+] Checking existing configs..."

for package in "${STOW_PACKAGES[@]}"; do
    backup_config "$package"
done

# --------------------------------------------------
# Stow
# --------------------------------------------------

echo
echo "[+] Creating symlinks..."

cd "$DOTFILES_DIR"

for package in "${STOW_PACKAGES[@]}"; do

    echo "    → $package"

    stow \
        --restow \
        --target="$HOME" \
        "$package"

done

# Thunar's settings live in GTK and Xfconf rather than ~/.config/thunar.
if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    python3 "$DOTFILES_DIR/scripts/setup-thunar.py"
else
    dbus-run-session -- python3 "$DOTFILES_DIR/scripts/setup-thunar.py"
fi

if $INSTALL_SDDM; then
    echo "[+] Installing the matching SDDM login theme..."
    python3 "$DOTFILES_DIR/sddm/sync-theme.py"
    sudo python3 "$DOTFILES_DIR/sddm/install-theme.py" "$DOTFILES_DIR/sddm/hyprland-rice"
fi

# --------------------------------------------------
# Fish info
# --------------------------------------------------

if command -v fish >/dev/null 2>&1; then

    FISH_PATH="$(command -v fish)"

    if [[ "${SHELL:-}" != "$FISH_PATH" ]]; then

        echo
        echo "[i] Fish is installed but isn't your login shell."
        echo
        echo "To change it:"
        echo
        echo "    chsh -s $FISH_PATH"

    fi
fi

# --------------------------------------------------
# Done
# --------------------------------------------------

echo
echo "======================================"
echo "          Bootstrap complete"
echo "======================================"

if [[ -d "$BACKUP_DIR" ]]; then

    echo
    echo "Previous configs:"
    echo "$BACKUP_DIR"

fi

echo
echo "Linked configs:"

printf '  - %s\n' "${STOW_PACKAGES[@]}"

echo

if $INSTALL_NVIDIA; then
    echo "NVIDIA driver installed. Reboot to load it, then verify with nvidia-smi."
fi

if $INSTALL_SDDM; then
    echo "SDDM theme installed for the next login; the display manager was not restarted."
fi
