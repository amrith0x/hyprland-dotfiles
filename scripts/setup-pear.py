#!/usr/bin/env python3
"""Apply the wallpaper theme and MPRIS settings to a closed Pear Desktop app."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import runpy
import shutil

ROOT = Path(__file__).resolve().parents[1]


def configure(settings, theme):
    options = settings.setdefault('options', {})
    themes = options.setdefault('themes', [])
    if str(theme) not in themes:
        themes.append(str(theme))
    options['hideMenu'] = True
    shortcuts = settings.setdefault('plugins', {}).setdefault('shortcuts', {})
    shortcuts['enabled'] = True
    # Hyprland already handles media keys through playerctl.
    shortcuts['overrideMediaKeys'] = False
    return settings


def pear_running():
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            executable = (process / 'cmdline').read_bytes().split(b'\0')[0].decode()
            if Path(executable).name.lower() in ('pear-desktop', 'youtube-music', 'pear-desktop-bin'):
                return True
        except (OSError, UnicodeError):
            pass
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, help='Override the detected Pear config.json path')
    parser.add_argument('--create', action='store_true', help='Create first-launch settings when needed')
    parser.add_argument('--defer-running', action='store_true', help='Let the installer defer setup if Pear is running')
    args = parser.parse_args()
    config_root = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    if args.config:
        target = args.config.expanduser()
    else:
        candidates = [config_root / name / 'config.json' for name in (
            'YouTube Music', 'youtube-music', 'Pear Desktop', 'pear-desktop',
            'com.github.th-ch.youtube-music')]
        existing = [path for path in candidates if path.is_file()]
        if not existing and args.create:
            target = config_root / 'YouTube Music/config.json'
        elif len(existing) == 1:
            target = existing[0]
        else:
            raise SystemExit('Open Pear once, then quit it completely and rerun this script. '
                             'If multiple configs exist, pass --config /path/to/config.json.')
    if not target.is_file() and not args.create:
        raise SystemExit('Config does not exist. Open Pear once, then quit it completely first.')
    # Do not race Electron's config writes or silently stop its playback.
    if pear_running():
        if args.defer_running:
            print('Pear is running; quit it and run scripts/setup-pear.py to refresh its settings.')
            return
        raise SystemExit('Quit Pear completely before applying its settings.')
    settings = json.loads(target.read_text()) if target.exists() else {}
    theme_module = runpy.run_path(str(ROOT / 'hypr/.config/hypr/scripts/wallpaper-theme.py'))
    colors = None if theme_module['DISABLED'].exists() else theme_module['palette'](theme_module['selected_wallpaper']())
    theme = ROOT / 'pear/theme.css'
    theme_module['atomic'](theme, theme_module['outputs'](colors)['pear/theme.css'])
    updated = configure(settings, theme)
    content = json.dumps(updated, indent=2, ensure_ascii=False) + '\n'
    if not target.exists() or content != target.read_text():
        backup = target.with_name('config.json.rice-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.copy2(target, backup)
        temporary = target.with_name('config.json.rice-tmp')
        temporary.write_text(content)
        temporary.chmod(target.stat().st_mode & 0o777 if target.exists() else 0o600)
        temporary.replace(target)
        if backup.exists():
            print('Settings backed up to:', backup)
    print('Pear wallpaper theme and MPRIS controls configured. Reopen Pear.')


if __name__ == '__main__':
    main()
