#!/usr/bin/env python3
"""Install the prepared theme, preserving previous configuration for rollback."""
from pathlib import Path
from datetime import datetime
import os
import shutil
import sys

from configuration import disable_keyboard, set_ini_option

if os.geteuid() != 0:
    raise SystemExit('Run through install.sh with sudo.')
source = Path(sys.argv[1]).resolve(strict=True)
destination = Path('/usr/share/sddm/themes/hyprland-rice')
config = Path('/etc/sddm.conf')
if destination.is_symlink() or config.is_symlink():
    raise SystemExit('Refusing to overwrite a symlink; inspect the destination first.')
if not (source / 'Main.qml').is_file() or not (source / 'Backgrounds/lock-wallpaper.png').is_file():
    raise SystemExit('Theme files are missing.')
backup = Path('/var/backups/sddm-hyprland-rice') / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup.mkdir(parents=True, mode=0o700)
if config.exists():
    shutil.copy2(config, backup / 'sddm.conf')
else:
    (backup / 'sddm.conf-was-absent').touch()
if destination.exists():
    shutil.copytree(destination, backup / 'hyprland-rice')
shutil.copytree(source, destination, dirs_exist_ok=True)
for item in [destination, *destination.rglob('*')]:
    if item.is_symlink():
        raise SystemExit('Unexpected symlink in installed theme.')
    item.chmod(0o755 if item.is_dir() else 0o644)
    os.chown(item, 0, 0)
old = config.read_text() if config.exists() else ''

updated = set_ini_option(old, 'Theme', 'Current', 'hyprland-rice')
# Force the physical-keyboard Compose input method, including the Qt environment.
updated = disable_keyboard(updated)
updated = set_ini_option(updated, 'General', 'Numlock', 'on')
config.write_text(updated)
config.chmod(0o644)
print('Installed /usr/share/sddm/themes/hyprland-rice')
print('Disabled the SDDM on-screen keyboard (InputMethod/QT_IM_MODULE=compose).')
print('Enabled Num Lock at the login screen.')
print('Previous configuration backed up to:', backup)
