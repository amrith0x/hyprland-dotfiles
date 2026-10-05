#!/usr/bin/env python3
"""Graphical NetworkManager selector for Waybar."""
import os
import subprocess
import threading
import fcntl

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import GLib, Gtk, Gdk, GtkLayerShell


def nm(*args):
    return subprocess.run(['nmcli', '--wait', '20', *args],
                          capture_output=True, text=True,
                          env={**os.environ, 'LC_ALL': 'C'})


def fields(line):
    values, value, escaped = [], '', False
    for char in line:
        if escaped:
            value += char
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            values.append(value)
            value = ''
        else:
            value += char
    return values + [value]


class Wifi(Gtk.Window):
    def __init__(self):
        super().__init__(title='Wi-Fi')
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())
        self.set_name('wifi-dropdown')
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'wifi-dropdown')
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, edge, True)
        self.connect('key-press-event', self.key_pressed)
        self.connect('destroy', Gtk.main_quit)
        backdrop = Gtk.EventBox()
        backdrop.connect('button-press-event', self.outside_click)
        self.add(backdrop)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.panel = box
        box.get_style_context().add_class('wifi-panel')
        box.set_halign(Gtk.Align.END)
        box.set_valign(Gtk.Align.START)
        box.set_margin_top(44)
        box.set_margin_end(12)
        box.set_size_request(350, 360)
        box.set_border_width(0)
        backdrop.add(box)
        header = Gtk.Box(spacing=12)
        title = Gtk.Label(label='󰤨  Wi-Fi', xalign=0)
        title.get_style_context().add_class('title')
        header.pack_start(title, True, True, 0)
        self.refresh = Gtk.Button(label='󰑐')
        self.refresh.set_tooltip_text('Refresh networks')
        self.refresh.get_style_context().add_class('icon-button')
        self.refresh.connect('clicked', self.scan)
        header.pack_end(self.refresh, False, False, 0)
        box.pack_start(header, False, False, 0)
        self.status = Gtk.Label(label='Finding nearby networks…', xalign=0)
        self.status.get_style_context().add_class('muted')
        self.status.set_max_width_chars(36)
        self.status.set_line_wrap(True)
        box.pack_start(self.status, False, False, 0)
        self.password_box = Gtk.Box(spacing=8)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text('Wi-Fi password')
        self.password_entry.connect('activate', self.submit_password)
        self.password_box.pack_start(self.password_entry, True, True, 0)
        connect = Gtk.Button(label='Connect')
        connect.connect('clicked', self.submit_password)
        self.password_box.pack_end(connect, False, False, 0)
        box.pack_start(self.password_box, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.networks = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.add(self.networks)
        box.pack_start(scroll, True, True, 0)
        footer = Gtk.Label(label='Esc to close', xalign=1)
        footer.get_style_context().add_class('footer')
        box.pack_end(footer, False, False, 0)
        self.show_all()
        self.password_box.hide()
        self.scan()

    def key_pressed(self, window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def outside_click(self, widget, event):
        x, y = self.panel.translate_coordinates(widget, 0, 0)
        allocation = self.panel.get_allocation()
        if not (x <= event.x < x + allocation.width and
                y <= event.y < y + allocation.height):
            self.destroy()
        return False

    def background(self, work, done):
        self.refresh.set_sensitive(False)
        self.networks.set_sensitive(False)
        def run():
            result = work()
            GLib.idle_add(finish, result)
        def finish(result):
            self.refresh.set_sensitive(True)
            self.networks.set_sensitive(True)
            done(result)
            return False
        threading.Thread(target=run, daemon=True).start()

    def scan(self, *_):
        self.status.set_text('Finding nearby networks…')
        self.background(lambda: nm('-t', '-f', 'IN-USE,SSID,SIGNAL,SECURITY',
                                   'device', 'wifi', 'list', '--rescan', 'yes'),
                        self.show_networks)

    def show_networks(self, result):
        for child in self.networks.get_children():
            child.destroy()
        if result.returncode:
            self.status.set_text(result.stderr.strip() or 'Unable to scan Wi-Fi.')
            return
        seen = set()
        for line in result.stdout.splitlines():
            active, ssid, signal, security = fields(line)
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            button = Gtk.Button()
            button.get_style_context().add_class('network-row')
            row = Gtk.Box(spacing=12)
            strength = int(signal)
            icon = Gtk.Label(label='󰤨' if strength >= 75 else '󰤥' if strength >= 50 else '󰤢' if strength >= 25 else '󰤟')
            icon.get_style_context().add_class('network-icon')
            row.pack_start(icon, False, False, 0)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            name = Gtk.Label(label=ssid, xalign=0)
            name.set_ellipsize(3)
            name.set_max_width_chars(23)
            name.get_style_context().add_class('network-name')
            text.pack_start(name, False, False, 0)
            detail = 'Connected' if active == '*' else ('Secured' if security != '--' else 'Open network')
            subtitle = Gtk.Label(label=detail, xalign=0)
            subtitle.get_style_context().add_class('network-detail')
            text.pack_start(subtitle, False, False, 0)
            row.pack_start(text, True, True, 0)
            trailing = Gtk.Label(label='󰄬' if active == '*' else f'{signal}%')
            trailing.get_style_context().add_class('network-detail')
            row.pack_end(trailing, False, False, 0)
            button.add(row)
            if active == '*':
                button.get_style_context().add_class('connected')
            button.connect('clicked', self.connect_network, ssid, security)
            self.networks.pack_start(button, False, False, 0)
        self.status.set_text('Choose a network to connect' if seen else 'No networks found. Check that Wi-Fi is enabled.')
        self.networks.show_all()

    def connect_network(self, button, ssid, security):
        self.password_box.hide()
        self.status.set_text(f'Connecting to {ssid}…')
        self.background(lambda: nm('device', 'wifi', 'connect', ssid),
                        lambda result: self.connected(result, ssid, security))

    def connected(self, result, ssid, security):
        if not result.returncode:
            self.scan()
            return
        if security == '--' or not any(word in result.stderr.lower() for word in ('secret', 'password')):
            self.status.set_text(result.stderr.strip() or 'Connection failed.')
            return
        self.pending_ssid = ssid
        self.status.set_text(f'Enter the password for {ssid}')
        self.password_entry.set_text('')
        self.password_box.show_all()
        self.password_entry.grab_focus()

    def submit_password(self, *_):
        password = self.password_entry.get_text()
        if not password:
            return
        ssid = self.pending_ssid
        self.password_entry.set_text('')
        self.password_box.hide()
        self.status.set_text(f'Connecting to {ssid}…')
        self.background(lambda: nm('device', 'wifi', 'connect', ssid, 'password', password),
                        self.connection_finished)

    def connection_finished(self, result):
        if result.returncode:
            self.status.set_text(result.stderr.strip() or 'Connection failed.')
        else:
            self.scan()


if __name__ == '__main__':
    lock = open(os.path.join(os.environ['XDG_RUNTIME_DIR'], 'waybar-wifi.lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(0)
    css = Gtk.CssProvider()
    css.load_from_path(os.path.join(os.path.dirname(__file__), '..', 'wifi.css'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    Wifi()
    Gtk.main()
