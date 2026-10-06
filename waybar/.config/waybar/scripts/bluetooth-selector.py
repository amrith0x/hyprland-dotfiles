#!/usr/bin/env python3
"""Bluetooth device panel sharing the Wi-Fi panel's layout and styling."""
import fcntl
import os
import sys
import runpy

Wifi = runpy.run_path(os.path.join(os.path.dirname(__file__), 'wifi-selector.py'),
                     run_name='wifi_selector')['Wifi']
from gi.repository import Gio, GLib, Gtk, Gdk, GtkLayerShell


ADAPTER = 'org.bluez.Adapter1'
DEVICE = 'org.bluez.Device1'
PROPERTIES = 'org.freedesktop.DBus.Properties'
AGENT_PATH = '/org/waybar/BluetoothAgent'
AGENT_XML = '''<node><interface name="org.bluez.Agent1">
<method name="Release"/>
<method name="Cancel"/>
<method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
<method name="RequestAuthorization"><arg type="o" direction="in"/></method>
<method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
<method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
<method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
<method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
<method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
</interface></node>'''


class Bluetooth(Wifi):
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.adapter = None
        self.scanning = False
        self.busy = False
        self.pending = None
        self.closed = False
        self.agent_info = Gio.DBusNodeInfo.new_for_xml(AGENT_XML)
        self.agent_id = self.bus.register_object(
            AGENT_PATH, self.agent_info.interfaces[0], self.agent_call, None, None)
        super().__init__()
        self.set_title('Bluetooth')
        self.set_name('bluetooth-dropdown')
        GtkLayerShell.set_namespace(self, 'bluetooth-dropdown')
        header = self.panel.get_children()[0]
        header.get_children()[0].set_text('󰂯  Bluetooth')
        self.refresh.set_tooltip_text('Scan for devices')
        self.refresh.get_accessible().set_name('Scan for devices')
        self.refresh.get_style_context().add_class('bluetooth-refresh')
        self.power = Gtk.Switch()
        self.power.set_valign(Gtk.Align.CENTER)
        self.power.get_style_context().add_class('bluetooth-power')
        self.power.set_tooltip_text('Bluetooth power')
        self.power.connect('state-set', self.toggle_power)
        header.pack_end(self.power, False, False, 0)
        self.power.show()
        self.password_box.destroy()
        self.confirm_box = Gtk.Box(spacing=8)
        self.pin = Gtk.Entry()
        self.pin.set_placeholder_text('Pairing PIN')
        self.pin.connect('activate', self.confirm)
        self.confirm_box.pack_start(self.pin, True, True, 0)
        for label, action in [('Pair', self.confirm), ('Cancel', self.reject)]:
            button = Gtk.Button(label=label)
            button.connect('clicked', action)
            self.confirm_box.pack_start(button, False, False, 0)
        self.panel.pack_start(self.confirm_box, False, False, 0)
        self.panel.reorder_child(self.confirm_box, 2)
        self.connect('destroy', self.cleanup)
        self.call('/org/bluez', 'org.bluez.AgentManager1', 'RegisterAgent',
                  GLib.Variant('(os)', (AGENT_PATH, 'KeyboardDisplay')))
        self.timer = GLib.timeout_add_seconds(2, self.refresh_devices)
        self.refresh_devices()
        self.scan()

    def call(self, path, interface, method, args=None, done=None):
        def finished(bus, result):
            if self.closed:
                return
            try:
                reply = bus.call_finish(result)
                if done:
                    done(reply, None)
            except GLib.Error as error:
                if done:
                    done(None, error)
                else:
                    self.status.set_text(error.message)
        self.bus.call('org.bluez', path, interface, method, args, None,
                      Gio.DBusCallFlags.NONE, 60000, None, finished)

    def objects(self):
        return self.bus.call_sync(
            'org.bluez', '/', 'org.freedesktop.DBus.ObjectManager',
            'GetManagedObjects', None, None, Gio.DBusCallFlags.NONE,
            2000, None).unpack()[0]

    def scan(self, *_):
        # The shared layout calls this during construction.
        if hasattr(self, 'power'):
            self.refresh_devices()
            if self.adapter and self.powered and not self.scanning:
                self.call(self.adapter, ADAPTER, 'StartDiscovery',
                          done=self.discovery_started)

    def discovery_started(self, reply, error):
        if error:
            self.status.set_text(error.message)
        else:
            self.scanning = True
            self.status.set_text('Scanning… Put your device in pairing mode.')

    def refresh_devices(self):
        if self.closed:
            return False
        if self.busy or self.pending:
            return True
        try:
            objects = self.objects()
        except GLib.Error:
            self.status.set_text('Bluetooth service unavailable.')
            return True
        adapters = [(path, info[ADAPTER]) for path, info in objects.items() if ADAPTER in info]
        if not adapters:
            self.status.set_text('No Bluetooth adapter found.')
            self.power.set_sensitive(False)
            return True
        self.adapter, properties = adapters[0]
        self.power.set_sensitive(True)
        self.powered = properties.get('Powered', False)
        self.power.set_state(self.powered)
        self.power.set_active(self.powered)
        self.scanning = self.scanning and self.powered
        for child in self.networks.get_children():
            child.destroy()
        devices = [(path, info[DEVICE]) for path, info in objects.items()
                   if DEVICE in info and info[DEVICE].get('Adapter') == self.adapter]
        devices.sort(key=lambda item: (not item[1].get('Connected', False),
                                     not item[1].get('Paired', False),
                                     item[1].get('Alias', '')))
        for path, info in devices:
            connected = info.get('Connected', False)
            name = info.get('Alias', info.get('Address', 'Unknown device'))
            detail = 'Connected · Click to disconnect' if connected else (
                'Paired · Click to connect' if info.get('Paired') else 'Click to pair and connect')
            button = Gtk.Button()
            button.get_style_context().add_class('network-row')
            if connected:
                button.get_style_context().add_class('connected')
            row = Gtk.Box(spacing=12)
            icon = Gtk.Label(label='󰂱' if connected else '󰂯')
            icon.get_style_context().add_class('network-icon')
            row.pack_start(icon, False, False, 0)
            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            title = Gtk.Label(label=name, xalign=0)
            title.set_ellipsize(3)
            title.set_max_width_chars(24)
            title.get_style_context().add_class('network-name')
            subtitle = Gtk.Label(label=detail, xalign=0)
            subtitle.get_style_context().add_class('network-detail')
            labels.pack_start(title, False, False, 0)
            labels.pack_start(subtitle, False, False, 0)
            row.pack_start(labels, True, True, 0)
            button.add(row)
            button.set_sensitive(self.powered)
            button.connect('clicked', self.select_device, path, info)
            self.networks.pack_start(button, False, False, 0)
        self.networks.show_all()
        self.status.set_text('Choose a device or scan for nearby devices.' if self.powered
                             else 'Bluetooth is off. Turn it on to connect.')
        return True

    def toggle_power(self, switch, enabled):
        if self.adapter and enabled != self.powered:
            self.power.set_sensitive(False)
            self.call(self.adapter, PROPERTIES, 'Set',
                      GLib.Variant('(ssv)', (ADAPTER, 'Powered', GLib.Variant('b', enabled))),
                      done=lambda reply, error: self.operation_done(reply, error))
        return True

    def select_device(self, button, path, info):
        self.busy = True
        self.networks.set_sensitive(False)
        self.status.set_text('Disconnecting…' if info.get('Connected') else 'Connecting…')
        if info.get('Connected'):
            self.call(path, DEVICE, 'Disconnect', done=self.operation_done)
        elif info.get('Paired'):
            self.call(path, DEVICE, 'Connect', done=self.operation_done)
        else:
            def paired(reply, error):
                if error:
                    self.operation_done(reply, error)
                    return
                self.call(path, DEVICE, 'Connect', done=self.operation_done)
            self.call(path, DEVICE, 'Pair', done=paired)

    def operation_done(self, reply, error):
        self.busy = False
        self.networks.set_sensitive(True)
        self.refresh_devices()
        if error:
            self.status.set_text(error.message)

    def agent_call(self, bus, sender, path, interface, method, params, invocation):
        values = params.unpack()
        if method in ('Release', 'Cancel'):
            self.reject()
            invocation.return_value(None)
        elif method.startswith('Display'):
            self.status.set_text(f'Enter {values[1]} on the device to pair.')
            invocation.return_value(None)
        elif method in ('RequestConfirmation', 'RequestAuthorization', 'AuthorizeService',
                        'RequestPinCode', 'RequestPasskey'):
            if self.pending:
                invocation.return_dbus_error('org.bluez.Error.Rejected', 'Pairing already in progress')
                return
            self.pending = (method, invocation)
            self.status.set_text(f'Confirm pairing code: {values[1]:06d}' if method == 'RequestConfirmation'
                                 else 'Enter the pairing PIN.' if method in ('RequestPinCode', 'RequestPasskey')
                                 else 'Allow this device to pair?')
            self.confirm_box.show_all()
            self.pin.set_text('')
            self.pin.set_visible(method in ('RequestPinCode', 'RequestPasskey'))
        else:
            invocation.return_dbus_error('org.bluez.Error.Rejected', 'Unsupported pairing request')

    def confirm(self, *_):
        if not self.pending:
            return
        method, invocation = self.pending
        value = self.pin.get_text().strip()
        if method == 'RequestPinCode':
            if not value or len(value) > 16:
                return
            reply = GLib.Variant('(s)', (value,))
        elif method == 'RequestPasskey':
            if not value.isdigit() or not 0 <= int(value) <= 999999:
                return
            reply = GLib.Variant('(u)', (int(value),))
        else:
            reply = None
        invocation.return_value(reply)
        self.pending = None
        self.confirm_box.hide()
        self.status.set_text('Pairing…')

    def reject(self, *_):
        if self.pending:
            self.pending[1].return_dbus_error('org.bluez.Error.Rejected', 'Pairing cancelled')
            self.pending = None
            self.confirm_box.hide()

    def cleanup(self, *_):
        self.closed = True
        self.reject()
        GLib.source_remove(self.timer)
        if self.scanning:
            self.bus.call('org.bluez', self.adapter, ADAPTER, 'StopDiscovery', None,
                          None, Gio.DBusCallFlags.NONE, 2000, None, None)
        self.bus.unregister_object(self.agent_id)


if __name__ == '__main__':
    lock = open(os.path.join(os.environ['XDG_RUNTIME_DIR'], 'waybar-bluetooth.lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(0)
    css = Gtk.CssProvider()
    css.load_from_path(os.path.join(os.path.dirname(__file__), '..', 'wifi.css'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    Bluetooth()
    Gtk.main()
