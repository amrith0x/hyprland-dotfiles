#!/usr/bin/env bash
# Remove only replacements/debug symbols identified during the rice audit.
set -euo pipefail
case "${1:---dry-run}" in
    --dry-run) APPLY=false ;;
    --apply) APPLY=true ;;
    *) echo "Usage: $0 [--dry-run|--apply]" >&2; exit 1 ;;
esac
REMOVE=()
for package in numlockx wlogout pear-desktop-bin-debug yay-debug; do
    if pacman -Q "$package" >/dev/null 2>&1; then
        REMOVE+=("$package")
    fi
done
if (( ${#REMOVE[@]} )); then
    printf 'Remove unused packages:'; printf ' %s' "${REMOVE[@]}"; printf '\n'
    if $APPLY; then
        # Do not recurse into dependencies: GTK and authentication packages are
        # used by scripts even when pacman labels them as orphans.
        sudo pacman -R "${REMOVE[@]}"
    fi
else
    echo "No audited package leftovers remain."
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BYTECODE_DIR="$SCRIPT_DIR/../sddm/__pycache__"
if [[ -d "$BYTECODE_DIR" ]]; then
    echo "Remove SDDM installer bytecode: $BYTECODE_DIR"
    if $APPLY; then
        sudo rm -rf -- "$BYTECODE_DIR"
    fi
fi
echo "Other orphan packages are left alone; some support this rice or unrelated applications."
