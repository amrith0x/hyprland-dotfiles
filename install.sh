#!/usr/bin/env bash

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

PACKAGES=(
    hypr
    waybar
    kitty
    fish
    nvim
    tofi
    wlogout
)

echo "======================================"
echo "      Hyprland Dotfiles Installer"
echo "======================================"
echo
echo "Dotfiles directory: $DOTFILES_DIR"
echo

# --------------------------------------------------
# Install GNU Stow if missing
# --------------------------------------------------

if ! command -v stow >/dev/null 2>&1; then
    echo "[+] GNU Stow not found."

    if command -v pacman >/dev/null 2>&1; then
        echo "[+] Installing GNU Stow..."
        sudo pacman -S --needed stow
    else
        echo "[!] Could not detect pacman."
        echo "Install GNU Stow manually and run this script again."
        exit 1
    fi
else
    echo "[✓] GNU Stow installed"
fi

echo

# --------------------------------------------------
# Check packages
# --------------------------------------------------

echo "[+] Checking dotfile packages..."

for package in "${PACKAGES[@]}"; do
    if [[ ! -d "$DOTFILES_DIR/$package" ]]; then
        echo "[!] Missing package: $package"
        exit 1
    fi

    echo "    ✓ $package"
done

echo

# --------------------------------------------------
# Backup existing configs
# --------------------------------------------------

backup_config() {
    local name="$1"
    local target="$HOME/.config/$name"

    # Ignore existing symlinks
    if [[ -L "$target" ]]; then
        return
    fi

    if [[ -e "$target" ]]; then
        mkdir -p "$BACKUP_DIR/.config"

        echo "[+] Backing up existing $name config"
        mv "$target" "$BACKUP_DIR/.config/"
    fi
}

backup_config "hypr"
backup_config "waybar"
backup_config "kitty"
backup_config "fish"
backup_config "nvim"
backup_config "tofi"
backup_config "wlogout"

echo

# --------------------------------------------------
# Stow dotfiles
# --------------------------------------------------

cd "$DOTFILES_DIR"

echo "[+] Creating symlinks..."

for package in "${PACKAGES[@]}"; do
    echo "    → $package"
    stow --restow --target="$HOME" "$package"
done

echo
echo "======================================"
echo "       Installation complete 🎉"
echo "======================================"

if [[ -d "$BACKUP_DIR" ]]; then
    echo
    echo "Old configuration files were backed up to:"
    echo "$BACKUP_DIR"
fi

echo
echo "Symlinked packages:"
printf '  - %s\n' "${PACKAGES[@]}"
echo
echo "You may need to restart applications or log out/in."
