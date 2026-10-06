#!/usr/bin/env python3
"""Enable login-screen Num Lock, preserving existing SDDM settings."""
from datetime import datetime
import os
from pathlib import Path
import shutil

from configuration import set_ini_option


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo: sudo python3 ~/dotfiles/sddm/enable-numlock.py')
    config = Path('/etc/sddm.conf')
    if config.is_symlink():
        raise SystemExit('Inspect the symlinked SDDM configuration before modifying it.')
    old = config.read_text() if config.exists() else ''
    updated = set_ini_option(old, 'General', 'Numlock', 'on')
    if updated != old:
        backup = Path('/var/backups/sddm-hyprland-rice') / ('numlock-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        backup.mkdir(parents=True, mode=0o700)
        if config.exists():
            shutil.copy2(config, backup / 'sddm.conf')
        else:
            (backup / 'sddm.conf-was-absent').touch()
        config.write_text(updated)
        config.chmod(0o644)
        print('Previous SDDM settings backed up to:', backup)
    print('Num Lock enabled for the next login screen. No services restarted.')


if __name__ == '__main__':
    main()
