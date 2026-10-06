# mpv + uosc

Bundled upstream uosc 5.13.0 from https://github.com/tomasklaen/uosc/releases/tag/5.13.0.
Release archive SHA-256: 4be9da3289285300fa374496c3f1bfd7bb20ac08e890d25bd5a06b28eebe4882.
Upstream files under `.config/mpv/scripts` and `.config/mpv/fonts` are unmodified;
only the unused macOS and Windows helper binaries are omitted from this Linux rice.
See UOSC-LICENSE for the upstream LGPL license.

Edit `uosc-rice.conf` for layout. The wallpaper generator appends the current
palette to `.config/mpv/script-opts/uosc.conf`; reopening mpv loads the new colors.
The bootstrap installer generates this file before linking the mpv package.
Playback stays opaque through the existing Hyprland mpv window rule.
