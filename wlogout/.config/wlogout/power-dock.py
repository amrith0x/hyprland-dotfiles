#!/usr/bin/env python3
"""A compact layer-shell power dock using the existing wlogout actions."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gdk, Gtk, GtkLayerShell

CONFIG = Path(__file__).resolve().parent
ICONS = {'shutdown': 'system-shutdown-symbolic', 'suspend': 'weather-clear-night-symbolic',
         'lock': 'system-lock-screen-symbolic', 'logout': 'system-log-out-symbolic',
         'reboot': 'system-reboot-symbolic'}


def actions():
    # wlogout uses successive JSON objects rather than a JSON array.
    remaining = (CONFIG / 'layout').read_text().strip()
    decoder = json.JSONDecoder()
    while remaining:
        action, end = decoder.raw_decode(remaining)
        yield action
        remaining = remaining[end:].strip()


class PowerDock(Gtk.Window):
    def __init__(self):
        super().__init__(title='Power dock')
        self.set_visual(self.get_screen().get_rgba_visual())
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'power-dock')
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, edge, True)
        self.connect('destroy', Gtk.main_quit)
        self.connect('key-press-event', self.key_pressed)
        provider = Gtk.CssProvider()
        provider.load_from_path(str(CONFIG / 'power-dock.css'))
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        backdrop = Gtk.EventBox()
        backdrop.set_visible_window(False)
        backdrop.connect('button-press-event', lambda *_: self.destroy() or True)
        self.add(backdrop)
        # An inner event box absorbs clicks in the pill, outside its buttons.
        pill = Gtk.EventBox()
        pill.set_visible_window(False)
        pill.set_halign(Gtk.Align.CENTER)
        pill.set_valign(Gtk.Align.CENTER)
        pill.connect('button-press-event', lambda *_: True)
        backdrop.add(pill)
        dock = Gtk.Box(spacing=12)
        dock.set_name('power-dock')
        pill.add(dock)
        self.shortcuts = {}
        for action in actions():
            column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            column.set_size_request(72, -1)
            button = Gtk.Button()
            button.set_size_request(64, 64)
            button.set_halign(Gtk.Align.CENTER)
            button.set_valign(Gtk.Align.CENTER)
            button.get_accessible().set_name(action['text'])
            icon = Gtk.Image.new_from_icon_name(ICONS[action['label']], Gtk.IconSize.DIALOG)
            icon.set_pixel_size(28)
            icon.set_halign(Gtk.Align.CENTER)
            icon.set_valign(Gtk.Align.CENTER)
            button.add(icon)
            caption = Gtk.Label(label=action['text'])
            caption.get_style_context().add_class('caption')
            caption.set_opacity(0)
            def update_caption(b, old=None, label=caption):
                active = b.get_state_flags() & (Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.FOCUSED)
                label.set_opacity(1 if active else 0)
            button.connect('state-flags-changed', update_caption)
            button.connect('state-flags-changed', lambda b, old: b.queue_draw())
            button.connect('clicked', lambda b, a=action: self.activate(a))
            column.pack_start(button, False, False, 0)
            column.pack_start(caption, False, False, 0)
            dock.pack_start(column, False, False, 0)
            self.shortcuts[action['keybind']] = action
        self.show_all()

    def activate(self, action):
        subprocess.Popen(['/bin/sh', '-c', action['action']], start_new_session=True)
        self.destroy()

    def key_pressed(self, _, event):
        key = Gdk.keyval_name(event.keyval)
        if key == 'Escape':
            self.destroy()
            return True
        if key.lower() in self.shortcuts:
            self.activate(self.shortcuts[key.lower()])
            return True
        return False


if __name__ == '__main__':
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
    with (runtime / f'power-dock-{os.getuid()}.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit(0)
        PowerDock()
        Gtk.main()
