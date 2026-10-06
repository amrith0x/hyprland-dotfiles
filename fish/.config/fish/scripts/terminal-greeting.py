#!/usr/bin/env python3
"""Show a small padded portrait using Kitty's native image renderer."""
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
PORTRAITS = ROOT / 'assets/terminal'


def main():
    if not sys.stdout.isatty() or not os.environ.get('KITTY_WINDOW_ID'):
        return
    renderer = shutil.which('kitten')
    if not renderer:
        return
    images = sorted(path for path in PORTRAITS.iterdir()
                    if path.is_file() and path.suffix.lower() in {'.png', '.webp', '.jpg', '.jpeg'})
    if not images:
        return
    terminal = os.get_terminal_size(sys.stdout.fileno())
    width = min(22, terminal.columns - 6)
    height = min(10, terminal.lines - 6)
    if width < 6 or height < 3:
        return
    # Reserve space for the image, save the prompt's position, and restore it
    # after icat's absolute placement moves the cursor to the image's corner.
    sys.stdout.write('\n' * (height + 3) + '\x1b7')
    sys.stdout.flush()
    try:
        subprocess.run(
            [renderer, 'icat', '--stdin=no', '--engine=builtin', '--loop=0',
             '--transfer-mode=stream', '--align=left',
             '--place', f'{width}x{height}@3x1', str(random.choice(images))],
            stderr=subprocess.PIPE, timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        pass
    finally:
        sys.stdout.write('\x1b8')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
