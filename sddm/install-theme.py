#!/usr/bin/env python3
"""Install the prepared theme, preserving previous configuration for rollback."""
from pathlib import Path
from datetime import datetime
import os
import re
import shutil
import sys

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
def set_ini_option(text, section_name, key, value):
    lines = text.splitlines(keepends=True)
    section_start = next((i for i, line in enumerate(lines)
                          if line.strip() == '[' + section_name + ']'), None)
    entry = key + '=' + value + '\n'
    if section_start is None:
        return text.rstrip() + '\n\n[' + section_name + ']\n' + entry
    section_end = next((i for i in range(section_start + 1, len(lines))
                        if lines[i].lstrip().startswith('[')), len(lines))
    matches = [i for i in range(section_start + 1, section_end)
               if re.match(r'^[ \t]*' + re.escape(key) + r'[ \t]*=', lines[i])]
    if matches:
        for i in matches:
            lines[i] = entry
    else:
        if section_end and not lines[section_end - 1].endswith('\n'):
            lines[section_end - 1] += '\n'
        lines.insert(section_end, entry)
    return ''.join(lines)

updated = set_ini_option(old, 'Theme', 'Current', 'hyprland-rice')
# /etc/sddm.conf takes precedence over virtualkbd.conf in the drop-in directory.
updated = set_ini_option(updated, 'General', 'InputMethod', '')
config.write_text(updated)
config.chmod(0o644)
print('Installed /usr/share/sddm/themes/hyprland-rice')
print('Disabled the SDDM on-screen keyboard (General/InputMethod=).')
print('Previous configuration backed up to:', backup)
