#!/usr/bin/env python3
"""Hover previews and a sliding wallpaper gallery for Hyprland."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[4]
WALLPAPERS = ROOT / 'assets/wallpapers'
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'wallpaper-selector/current'
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}


def wallpapers():
    return sorted((p for p in WALLPAPERS.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS),
                  key=lambda p: p.name.casefold()) if WALLPAPERS.is_dir() else []


def current():
    try:
        saved = Path(STATE.read_text().strip())
        if saved.is_file():
            return saved
    except OSError:
        pass
    return WALLPAPERS / 'main.png'


def apply(path, persist=True):
    subprocess.run(['awww', 'img', '--transition-type', 'fade',
                    '--transition-duration', '0.6', str(path)],
                   check=True, capture_output=True, text=True, timeout=20)
    if persist:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        temporary = STATE.with_suffix('.tmp')
        temporary.write_text(str(path) + '\n')
        temporary.replace(STATE)

    theme_script = Path(__file__).resolve().with_name('wallpaper-theme.py')
    if theme_script.exists():
        try:
            result = subprocess.run([sys.executable, str(theme_script), 'apply', str(path)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                print(result.stderr.strip(), file=sys.stderr)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f'Wallpaper applied; theme update unavailable: {error}', file=sys.stderr)


def restore():
    for attempt in range(20):
        try:
            apply(current(), persist=False)
            return
        except subprocess.CalledProcessError:
            if attempt == 19:
                raise
            time.sleep(0.25)


def selector():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, GtkLayerShell
    Gtk.init(None)

    class Gallery(Gtk.Window):
        def __init__(self):
            super().__init__(title='Wallpapers')
            self.set_name('wallpaper-selector')
            self.set_decorated(False)
            self.set_app_paintable(True)
            visual = self.get_screen().get_rgba_visual()
            if visual is not None:
                self.set_visual(visual)
            GtkLayerShell.init_for_window(self)
            GtkLayerShell.set_namespace(self, 'wallpaper-selector')
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
            for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                         GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
                GtkLayerShell.set_anchor(self, edge, True)
            self.connect('destroy', self.cleanup)
            self.connect('key-press-event', self.key_pressed)
            self.selected = current()
            self.busy = False
            self.alive = True
            self.position = 0.0
            self.target = 0
            self.last_frame = time.monotonic()
            self.images = {}
            self.cards = {}
            self.cache = {}
            self.card_sizes = {}
            self.card_positions = {}
            self.gallery_size = None
            self.stage = Gtk.Layout()
            monitor = self.get_display().get_primary_monitor() or self.get_display().get_monitor(0)
            # Open on the focused Hyprland output, including multi-monitor setups.
            try:
                outputs = json.loads(subprocess.check_output(['hyprctl', '-j', 'monitors'],
                                                             text=True, timeout=2))
                focused = next(output for output in outputs if output.get('focused'))
                monitor = self.get_display().get_monitor_at_point(focused['x'] + 1, focused['y'] + 1)
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, StopIteration):
                pass
            GtkLayerShell.set_monitor(self, monitor)
            geometry = monitor.get_geometry()
            self.stage.set_size_request(geometry.width, geometry.height)
            self.stage.set_halign(Gtk.Align.FILL)
            self.stage.set_valign(Gtk.Align.FILL)
            self.stage.set_hexpand(True)
            self.stage.set_vexpand(True)
            # Off-screen cards must not increase the window's requested width.
            # Overlay children do not contribute to the parent's natural size.
            overlay = Gtk.Overlay()
            backdrop = Gtk.Box()
            backdrop.set_size_request(geometry.width, geometry.height)
            overlay.add(backdrop)
            overlay.add_overlay(self.stage)
            self.add(overlay)
            self.stage.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK |
                                  Gdk.EventMask.SMOOTH_SCROLL_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
            self.stage.connect('scroll-event', self.scrolled)
            self.stage.connect('button-press-event', lambda _, event: self.destroy() if event.button == 3 else False)
            self.stage.connect('size-allocate', self.resized)
            for path in wallpapers():
                try:
                    self.images[path] = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 1280, 800, True)
                except GLib.Error:
                    continue
                card = Gtk.EventBox()
                card.get_style_context().add_class('card')
                card.set_can_focus(True)
                image = Gtk.Image()
                card.add(image)
                index = len(self.cards)
                card.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK |
                                Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.SCROLL_MASK)
                card.connect('enter-notify-event', self.hover, index)
                card.connect('motion-notify-event', self.hover, index)
                card.connect('button-press-event', self.clicked, path)
                card.connect('scroll-event', self.scrolled)
                self.stage.put(card, 0, 0)
                self.cards[path] = (card, image)
            self.paths = list(self.cards)
            if self.paths:
                self.target = self.paths.index(self.selected) if self.selected in self.cards else len(self.paths) // 2
                self.position = float(self.target)
                self.focus_card(self.target)
                self.mark_selected()
            self.show_all()
            self.timer = self.stage.add_tick_callback(self.animate)
            GLib.idle_add(self.resized)

        @staticmethod
        def crop(pixbuf, width, height):
            scale = max(width / pixbuf.get_width(), height / pixbuf.get_height())
            source_width = min(pixbuf.get_width(), max(1, round(width / scale)))
            source_height = min(pixbuf.get_height(), max(1, round(height / scale)))
            cropped = pixbuf.new_subpixbuf((pixbuf.get_width() - source_width) // 2,
                                          (pixbuf.get_height() - source_height) // 2,
                                          source_width, source_height)
            return cropped.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        def resized(self, *_):
            self.layout_cards()

        def focus_card(self, index):
            for i, (card, _) in enumerate(self.cards.values()):
                context = card.get_style_context()
                (context.add_class if i == index else context.remove_class)('focused')

        def hover(self, _, event, index):
            # Ignore crossing events caused by cards moving under a stationary pointer.
            if event.type == Gdk.EventType.MOTION_NOTIFY:
                self.target = index
                self.focus_card(index)
            return True

        def layout_cards(self):
            allocation = self.stage.get_allocation()
            if allocation.width < 2 or allocation.height < 2:
                return
            base_height = allocation.height * 0.55
            base_width = min(base_height * 0.45, allocation.width * 0.18)
            gallery_size = (allocation.width, allocation.height)
            if gallery_size != self.gallery_size:
                self.gallery_size = gallery_size
                self.cache.clear()
                self.card_sizes.clear()
                # Prepare all zoom levels once, rather than resize images during animation.
                for path in self.cards:
                    portrait = self.crop(self.images[path], max(20, int(base_width)), max(40, int(base_height)))
                    for level in range(41):
                        factor = 0.60 + level * 0.01
                        width = max(20, round(base_width * factor))
                        height = max(40, round(base_height * factor))
                        self.cache[path, level] = portrait.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
            sizes = []
            centers = []
            for index in range(len(self.cards)):
                factor = max(0.60, 1 - abs(index - self.position) * 0.10)
                level = max(0, min(40, round((factor - 0.60) * 100)))
                width = max(20, round(base_width * (0.60 + level * 0.01)))
                height = max(40, round(base_height * (0.60 + level * 0.01)))
                sizes.append((level, width, height))
                centers.append(0 if index == 0 else centers[-1] + (sizes[index - 1][1] + width) / 2 + 8)
            if not centers:
                return
            left = min(len(centers) - 1, int(self.position))
            right = min(len(centers) - 1, left + 1)
            origin = centers[left] + (centers[right] - centers[left]) * (self.position - left)
            changed = False
            for index, (path, (card, image)) in enumerate(self.cards.items()):
                level, width, height = sizes[index]
                if self.card_sizes.get(path) != level:
                    image.set_from_pixbuf(self.cache[path, level])
                    card.set_size_request(width, height)
                    self.card_sizes[path] = level
                    changed = True
                x = allocation.width / 2 + centers[index] - origin - width / 2
                y = allocation.height * 0.50 - height / 2
                position = (round(x), round(y))
                if self.card_positions.get(path) != position:
                    self.stage.move(card, *position)
                    self.card_positions[path] = position
                    changed = True
                card.get_preferred_size()
                rectangle = Gdk.Rectangle()
                rectangle.x, rectangle.y = position
                rectangle.width, rectangle.height = width, height
                card.size_allocate(rectangle)
            if changed:
                # Fixed screen bounds keep the parent's size request constant,
                # so explicitly allocate children after moving/resizing them.
                self.stage.queue_allocate()
                self.queue_draw()

        def animate(self, widget, frame_clock):
            now = time.monotonic()
            elapsed = min(0.1, now - self.last_frame)
            self.last_frame = now
            difference = self.target - self.position
            if abs(difference) > 0.01:
                self.position += difference * (1 - pow(0.000001, elapsed))
                self.layout_cards()
            elif self.position != self.target:
                self.position = float(self.target)
                self.layout_cards()
            return True

        def navigate(self, step):
            if self.paths:
                self.target = max(0, min(len(self.paths) - 1, self.target + step))
                self.focus_card(self.target)

        def scrolled(self, _, event):
            if event.direction == Gdk.ScrollDirection.SMOOTH:
                _, dx, dy = event.get_scroll_deltas()
                delta = dx if abs(dx) > abs(dy) else dy
                if abs(delta) < 0.1:
                    return True
                self.navigate(1 if delta > 0 else -1)
            else:
                self.navigate(-1 if event.direction in (Gdk.ScrollDirection.UP, Gdk.ScrollDirection.LEFT) else 1)
            return True

        def key_pressed(self, _, event):
            if event.keyval == Gdk.KEY_Escape:
                self.destroy()
            elif event.keyval in (Gdk.KEY_Left, Gdk.KEY_Right):
                self.navigate(-1 if event.keyval == Gdk.KEY_Left else 1)
            elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and self.paths:
                self.choose(self.paths[self.target])
            else:
                return False
            return True

        def clicked(self, _, event, path):
            if event.button == 1:
                self.choose(path)
            elif event.button == 3:
                self.destroy()
            return True

        def mark_selected(self):
            for path, (card, _) in self.cards.items():
                context = card.get_style_context()
                (context.add_class if path == self.selected else context.remove_class)('selected')

        def cleanup(self, *_):
            self.alive = False
            self.stage.remove_tick_callback(self.timer)
            Gtk.main_quit()

        def choose(self, path):
            if self.busy:
                return
            self.busy = True
            self.stage.set_sensitive(False)

            def work():
                error = None
                try:
                    apply(path)
                except (OSError, subprocess.SubprocessError) as exc:
                    error = getattr(exc, 'stderr', None) or str(exc)
                GLib.idle_add(finish, error)

            def finish(error):
                if not self.alive:
                    return False
                self.busy = False
                if error:
                    self.stage.set_sensitive(True)
                    print(f'Unable to apply wallpaper: {error}', file=sys.stderr)
                else:
                    self.destroy()
                return False

            threading.Thread(target=work, daemon=False).start()

    css = Gtk.CssProvider()
    css.load_from_path(str(Path(__file__).resolve().parent.parent / 'wallpaper-selector.css'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    Gallery()
    Gtk.main()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true', help='Restore saved wallpaper at login')
    args = parser.parse_args()
    if args.restore:
        restore()
    else:
        with open(Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')) / f'wallpaper-selector-{os.getuid()}.lock', 'w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SystemExit(0)
            selector()
