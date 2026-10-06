#!/usr/bin/env python3
"""Refresh the staged login theme from the current Hyprlock wallpaper and colors."""
from pathlib import Path
import re
import shutil

source = Path(__file__).resolve().parent.parent / 'hypr/.config/hypr'
theme = Path(__file__).resolve().parent / 'hyprland-rice'
palette = dict(re.findall(r'\$(\w+) = rgb\(([0-9a-fA-F]{6})\)', (source / 'wallpaper-colors.conf').read_text()))
foreground, background, accent = ('#' + palette[n] for n in ('wp_a6adc8', 'wp_11111b', 'wp_89b4fa'))
text = (theme / 'theme.conf').read_text()
background_keys = {'FormBackgroundColor', 'BackgroundColor', 'DimBackgroundColor', 'LoginFieldBackgroundColor', 'PasswordFieldBackgroundColor', 'DropdownBackgroundColor'}
accent_keys = {'DropdownSelectedBackgroundColor', 'HighlightBackgroundColor', 'HoverUserIconColor', 'HoverPasswordIconColor', 'HoverSystemButtonsIconsColor', 'HoverSessionButtonTextColor', 'HoverVirtualKeyboardButtonTextColor'}
for key in re.findall(r'^(\w+Color)=', text, re.M):
    color = '#cc2222' if key == 'WarningColor' else background if key in background_keys else accent if key in accent_keys else foreground
    text = re.sub(r'^' + key + r'=.*$', key + '="' + color + '"', text, flags=re.M)
(theme / 'theme.conf').write_text(text)
(theme / 'Backgrounds').mkdir(parents=True, exist_ok=True)
shutil.copyfile(source / 'lock-wallpaper.png', theme / 'Backgrounds/lock-wallpaper.png')
print('Staged theme refreshed from the current system wallpaper and palette.')
