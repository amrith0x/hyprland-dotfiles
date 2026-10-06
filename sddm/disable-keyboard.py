#!/usr/bin/env python3
"""Disable SDDM's on-screen keyboard without restarting the display manager."""
from datetime import datetime
import os
from pathlib import Path
import shutil

from configuration import disable_keyboard


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo: sudo python3 sddm/disable-keyboard.py')
    config = Path('/etc/sddm.conf')
    legacy = Path('/etc/sddm.conf.d/virtualkbd.conf')
    if config.is_symlink() or legacy.is_symlink():
        raise SystemExit('Inspect symlinked SDDM config files before modifying them.')
    old = config.read_text() if config.exists() else ''
    updated = disable_keyboard(old)
    backup = Path('/var/backups/sddm-hyprland-rice') / ('keyboard-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    legacy_keyboard = legacy.exists() and 'qtvirtualkeyboard' in legacy.read_text()
    if updated != old or legacy_keyboard:
        backup.mkdir(parents=True, mode=0o700)
        if config.exists():
            shutil.copy2(config, backup / 'sddm.conf')
        if legacy_keyboard:
            shutil.copy2(legacy, backup / 'virtualkbd.conf')
            # Keep any unrelated settings in the drop-in while removing its activation.
            legacy.write_text(disable_keyboard(legacy.read_text()))
        config.write_text(updated)
        config.chmod(0o644)
        print('Previous SDDM settings backed up to:', backup)
    print('SDDM keyboard disabled. No services restarted.')


if __name__ == '__main__':
    main()
