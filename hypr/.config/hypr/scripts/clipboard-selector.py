#!/usr/bin/env python3
"""Select a Cliphist entry with Rofi without clearing the clipboard on cancel."""
import subprocess
import sys


def main():
    history = subprocess.run(['cliphist', 'list'], capture_output=True, check=True).stdout
    placeholder = 'Search clipboard…' if history else 'Copy something to start your history'
    selection = subprocess.run(
        ['rofi', '-dmenu', '-i', '-no-sort', '-no-custom', '-no-show-icons',
         '-display-columns', '2', '-p', '󰄀', '-theme-str',
         'element { children: [ element-text ]; } '
         f'entry {{ placeholder: "{placeholder}"; }}'],
        input=history, capture_output=True,
    )
    if selection.returncode or not selection.stdout.strip():
        return
    # Keep bytes intact so images and text with trailing newlines survive decoding.
    decoded = subprocess.run(['cliphist', 'decode'], input=selection.stdout,
                             capture_output=True, check=True).stdout
    subprocess.run(['wl-copy'], input=decoded, check=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError) as error:
        print(f'Clipboard picker failed: {error}', file=sys.stderr)
        raise SystemExit(1)
