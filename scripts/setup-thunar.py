#!/usr/bin/env python3
"""Connect the Thunar rice to GTK, Xfconf, and the default folder handler."""
import configparser
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess

CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
BACKUP = Path.home() / '.dotfiles-backup' / ('thunar-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))


def write_preserving(path, content):
    if path.exists():
        if path.read_text() == content:
            return
        backup = BACKUP / path.relative_to(CONFIG)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main():
    if not shutil.which('thunar'):
        raise SystemExit('Install Thunar before running this setup script.')
    css_path = CONFIG / 'gtk-3.0/gtk.css'
    css = css_path.read_text() if css_path.exists() else ''
    include = '@import url("../thunar-rice/style.css");'
    if include not in css:
        # Imports must precede rules. Preserve existing GTK colors/customizations.
        write_preserving(css_path, include + '\n' + css)
    settings_path = CONFIG / 'gtk-3.0/settings.ini'
    settings = configparser.ConfigParser(interpolation=None)
    settings.optionxform = str
    if settings_path.exists():
        settings.read(settings_path)
    if not settings.has_section('Settings'):
        settings.add_section('Settings')
    settings['Settings']['gtk-application-prefer-dark-theme'] = 'true'
    settings['Settings']['gtk-theme-name'] = 'Rose-Pine'
    settings['Settings']['gtk-cursor-theme-name'] = 'breeze_cursors'
    settings['Settings']['gtk-cursor-theme-size'] = '24'
    settings['Settings']['gtk-icon-theme-name'] = 'Papirus-Dark'
    settings['Settings']['gtk-font-name'] = 'JetBrainsMono Nerd Font 10'
    from io import StringIO
    buffer = StringIO()
    settings.write(buffer, space_around_delimiters=False)
    write_preserving(settings_path, buffer.getvalue())
    # Set only Thunar preferences; never overwrite a live xfconfd XML file.
    preferences = {
        'last-view': ('string', 'ThunarIconView'),
        'last-icon-view-zoom-level': ('string', 'THUNAR_ZOOM_LEVEL_100_PERCENT'),
        'last-side-pane': ('string', 'ThunarShortcutsPane'),
        'last-location-bar': ('string', 'ThunarLocationButtons'),
        'last-menubar-visible': ('bool', 'false'),
        'last-statusbar-visible': ('bool', 'true'),
        'misc-thumbnail-mode': ('string', 'THUNAR_THUMBNAIL_MODE_ONLY_LOCAL'),
    }
    for name, (kind, value) in preferences.items():
        subprocess.run(['xfconf-query', '-c', 'thunar', '-p', '/' + name,
                        '--create', '-t', kind, '-s', value], check=True)
    subprocess.run(['xdg-mime', 'default', 'thunar.desktop', 'inode/directory'], check=True)
    if shutil.which('gsettings'):
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface',
                        'icon-theme', 'Papirus-Dark'], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface',
                        'gtk-theme', 'Rose-Pine'], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface',
                        'cursor-theme', 'breeze_cursors'], check=True)
    if BACKUP.exists():
        print('Previous GTK settings backed up to ' + str(BACKUP))
    print('Thunar configured: dark GTK styling, Papirus icons, folder default.')


if __name__ == '__main__':
    main()
