#!/usr/bin/env python3
"""Hold logind idle/sleep inhibitors while Fish terminals have running jobs."""
import fcntl
import os
from pathlib import Path
import signal
import time

from gi.repository import Gio, GLib


def terminal_busy(proc=Path('/proc')):
    for directory in proc.iterdir():
        if not directory.name.isdigit():
            continue
        try:
            # Fields after comm start at state (field 3); tty_nr is field 7.
            stat = (directory / 'stat').read_text()
            comm = stat[stat.index('(') + 1:stat.rindex(')')]
            values = stat[stat.rindex(')') + 2:].split()
            if comm != 'fish' or values[4] == '0':
                continue
            children = (directory / 'task' / directory.name / 'children').read_text().split()
            for child in children:
                try:
                    child_stat = (proc / child / 'stat').read_text()
                    state = child_stat[child_stat.rindex(')') + 2:].split()[0]
                    if state not in ('T', 't', 'Z', 'X'):
                        return True
                except (OSError, ValueError, IndexError):
                    continue
        except (OSError, ValueError, IndexError):
            continue
    return False


def acquire(bus):
    reply, descriptors = bus.call_with_unix_fd_list_sync(
        'org.freedesktop.login1', '/org/freedesktop/login1',
        'org.freedesktop.login1.Manager', 'Inhibit',
        GLib.Variant('(ssss)', ('idle:sleep', 'Terminal jobs',
                               'A command is running in a Fish terminal', 'block')),
        GLib.VariantType.new('(h)'), Gio.DBusCallFlags.NONE, 5000, None, None)
    return descriptors.get(reply.unpack()[0])


def main():
    lock = open(Path(os.environ['XDG_RUNTIME_DIR']) / 'terminal-inhibit.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    inhibitor = None
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while running:
            busy = terminal_busy()
            if busy and inhibitor is None:
                try:
                    inhibitor = acquire(bus)
                except GLib.Error as error:
                    print(f'Cannot inhibit terminal idle: {error}', flush=True)
                    time.sleep(5)
            elif not busy and inhibitor is not None:
                os.close(inhibitor)
                inhibitor = None
            time.sleep(0.5)
    finally:
        if inhibitor is not None:
            os.close(inhibitor)


if __name__ == '__main__':
    main()
