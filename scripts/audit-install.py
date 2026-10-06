#!/usr/bin/env python3
"""Validate the rice in an isolated temporary checkout and Stow target."""
import ast
import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('hypr', 'waybar', 'kitty', 'fish', 'nvim', 'rofi', 'wlogout',
            'thunar', 'dunst', 'mpv', 'desktop')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)


def main():
    for path in ROOT.rglob('*.py'):
        if '.git' not in path.parts:
            ast.parse(path.read_text(), filename=str(path))
    for path in (ROOT / 'install.sh', ROOT / 'sddm/install.sh', ROOT / 'scripts/cleanup-packages.sh'):
        run('bash', '-n', str(path))
    for path in (ROOT / 'hypr').rglob('*.lua'):
        run('luac', '-p', str(path))
    for path in (ROOT / 'sddm/hyprland-rice').rglob('*.qml'):
        run('qmllint', str(path))
    print('Python, Bash, Lua, and QML syntax passed.')

    with tempfile.TemporaryDirectory(prefix='rice-audit-') as temporary:
        staging = Path(temporary) / 'dotfiles'
        profile = Path(temporary) / 'profile'
        profile.mkdir()
        # Include current source changes, but never ignored runtime state or credentials.
        files = subprocess.check_output(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
        for name in files.decode().split('\0'):
            source = ROOT / name
            if not name or not source.is_file():
                continue
            destination = staging / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        module = runpy.run_path(str(staging / 'hypr/.config/hypr/scripts/wallpaper-theme.py'))
        static = module['outputs'](None)
        roles = set(module['ROLES'].values()) | set(module['KITTY_ROLES'].values())
        palette = {role: '#234567' for role in roles}
        palette['primary'] = '#abcdef'
        dynamic = module['outputs'](palette)
        assert 'foreground=89b4fa' in static['mpv/.config/mpv/script-opts/uosc.conf']
        assert 'foreground=abcdef' in dynamic['mpv/.config/mpv/script-opts/uosc.conf']
        assert '--rice-accent: #abcdef;' in dynamic['pear/theme.css']
        assert not re.search(r'\{\{\w+\}\}', dynamic['pear/theme.css'])
        module['publish'](static)
        shutil.copy2(staging / 'assets/wallpapers/main.png',
                     staging / 'hypr/.config/hypr/lock-wallpaper.png')

        run('stow', '--dir=' + str(staging), '--target=' + str(profile), '--stow', *PACKAGES)
        run('stow', '--dir=' + str(staging), '--target=' + str(profile), '--restow', *PACKAGES)
        for config in ('hypr/hyprland.lua', 'waybar/config.jsonc', 'mpv/script-opts/uosc.conf',
                       'wlogout/power-dock.py', 'qt6ct/qt6ct.conf'):
            assert (profile / '.config' / config).is_file(), config
        assert (profile / '.local/share/themes/Rose-Pine/gtk-3.0/gtk.css').is_file()
        assert not (profile / 'uosc-rice.conf').exists()
        assert not (profile / 'README.md').exists()
        print('Fresh-profile Stow installation and repeat installation passed.')

        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        have_display = Gtk.init_check()[0]
        css_files = (
            'waybar/.config/waybar/style.css', 'waybar/.config/waybar/wifi.css',
            'wlogout/.config/wlogout/power-dock.css', 'hypr/.config/hypr/wallpaper-selector.css',
            'thunar/.config/thunar-rice/style.css',
            'desktop/.local/share/themes/Rose-Pine/gtk-3.0/gtk.css',
            'desktop/.local/share/themes/Rose-Pine/gtk-3.0/gtk-dark.css')
        for name in css_files:
            provider = Gtk.CssProvider()
            errors = []
            provider.connect('parsing-error', lambda p, s, e: errors.append(str(e)))
            if not have_display and name.startswith('desktop/'):
                # Symbolic icon lookups need a display; still parse every style rule.
                css = (staging / name).read_text()
                css = re.sub(r'-gtk-icon-source:[^;]*;', '-gtk-icon-source: none;', css)
                provider.load_from_data(css.encode())
            else:
                provider.load_from_path(str(staging / name))
            assert not errors, (name, errors)
        bar = json.loads((staging / 'waybar/.config/waybar/config.jsonc').read_text())
        for group in ('group/music', 'group/hardware', 'group/volume'):
            assert all(item in bar for item in bar[group]['modules'])
        dock = runpy.run_path(str(staging / 'wlogout/.config/wlogout/power-dock.py'), run_name='audit_dock')
        actions = list(dock['actions']())
        assert len(actions) == 5
        assert next(a for a in actions if a['label'] == 'logout')['action'] == "hyprctl dispatch 'hl.dsp.exit()'"
        print('Generated palettes, GTK stylesheets, Waybar drawers, and power actions passed.')

        # Exercise first-launch Pear configuration without touching the real account.
        (staging / '.theme-runtime').mkdir(exist_ok=True)
        (staging / '.theme-runtime/disabled').write_text('disabled\n')
        pear_config = Path(temporary) / 'pear/config.json'
        setup = runpy.run_path(str(staging / 'scripts/setup-pear.py'), run_name='audit_pear')
        def setup_pear(*flags):
            with patch.dict(setup['main'].__globals__, pear_running=lambda: False), \
                 patch.object(sys, 'argv', ['setup-pear.py', '--config', str(pear_config), *flags]):
                setup['main']()
        setup_pear('--create')
        settings = json.loads(pear_config.read_text())
        assert settings['plugins']['shortcuts']['enabled']
        settings['options']['tray'] = True
        settings['options']['themes'].insert(0, 'another.css')
        pear_config.write_text(json.dumps(settings))
        setup_pear()
        previous = pear_config.read_text()
        setup_pear()
        assert pear_config.read_text() == previous
        settings = json.loads(previous)
        assert settings['options']['tray'] is True
        assert settings['options']['themes'] == ['another.css', str(staging / 'pear/theme.css')]
        print('Pear first-launch setup, setting preservation, and repeat setup passed.')

        for flags in ((), ('--with-nvidia',), ('--with-sddm',), ('--with-nvidia', '--with-sddm')):
            result = run('bash', str(staging / 'install.sh'), '--dry-run', *flags)
            assert 'org.mozilla.firefox' in result.stdout
            assert 'setup-pear.py' in result.stdout
            assert 'pipewire-pulse' in result.stdout
            assert ('install-theme.py' in result.stdout) == ('--with-sddm' in flags)
            assert ('nvidia-open' in result.stdout) == ('--with-nvidia' in flags)
        print('All four installer plans passed without changing the desktop.')

    print('Rice audit passed. Package installation and real SDDM authentication need a target machine.')


if __name__ == '__main__':
    main()
