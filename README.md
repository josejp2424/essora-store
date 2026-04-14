<div align="center">
  <img src="/usr/local/essora-store/essora-store.png" alt="Essora Store" width="128"/>
  <h1>Essora Store</h1>
  <p><strong>Unified package manager for Essora Linux — Flatpak, DEB and AppImage in one place.</strong></p>

  ![Version](https://img.shields.io/badge/version-3.6--1-blue)
  ![License](https://img.shields.io/badge/license-GPL--3.0-green)
  ![Platform](https://img.shields.io/badge/platform-Essora%20Linux-purple)
  ![GTK](https://img.shields.io/badge/GTK-3.0-orange)
  ![Python](https://img.shields.io/badge/Python-3-yellow)
</div>

---

## Overview

**Essora Store** is the native software center for [Essora Linux](https://sourceforge.net/projects/essora/), a custom Devuan-based distribution using OpenRC. It provides a modern, dark-themed GTK3 interface that consolidates three completely different package ecosystems — **Flatpak**, **DEB (APT)** and **AppImage** — into a single, cohesive application.

Instead of switching between a terminal, a separate Flatpak manager, and manual AppImage installs, Essora Store gives you one consistent graphical interface to browse, install, update, and remove software across all three formats.

The application is written entirely in Python 3 using GTK3 (via PyGObject), follows a modular architecture, and includes multilingual support with automatic system language detection.

---

## Features

### Multi-format Package Management
- **Flatpak** — browse and install apps from Flathub and configured Flatpak remotes, with icon cache integration for fast rendering
- **DEB** — full APT integration supporting 67,000+ packages, with pre-generated catalog (`deb-store.json`) for instant load times
- **AppImage** — manage portable AppImage applications stored in `/opt/appimage`, with automatic `.desktop` file integration

### Home Screen
- Rotating **banner slideshow** loaded from `/usr/local/essora-store/banners/`, with navigation dots and auto-advance every 7 seconds
- **Category tiles** with color-coded buttons: Universal Access, Accessories, Audio, Communication, Development, Education, Writing & Languages, Finance
- **Featured Flatpak apps** grid loaded from `flatpak.txt` with icons from the local cache
- **Favorites** grid showing quick-launch tiles from `all_apps.json`

### Search
- **Global search bar** on the home screen that searches across all three package types simultaneously
- **Per-backend search** bar on each section (Flatpak / DEB / AppImage) for focused filtering
- Search results appear in a styled popover with app icons, package type badges, and instant navigation
- Minimum 3-character threshold before searching to avoid noise

### Updates
- **Update tab** in each backend section showing available upgrades
- **Update All** button for batch upgrades
- Per-package update buttons for individual DEB package upgrades
- Automatic update list refresh when switching to the Update tab

### Repository Management
- **Repos tab** for DEB section shows all configured APT sources (`/etc/apt/sources.list` and `/etc/apt/sources.list.d/`)
- Each repository entry displays URI, suite, components, and source file with line number
- **Enable/disable toggle switches** to comment/uncomment repository lines without editing files manually
- Flatpak and AppImage sections show their own repository status and instructions

### Progress & Feedback
- Full **progress dialog** with percentage bar, console output (monospace, dark terminal style), and auto-scroll
- Operations run in background threads to keep the UI responsive
- Console output streams in real time during installs, updates, and removals

### Fix Broken Packages
- Built-in launcher for `essora-fix-broken.py`, a standalone GTK repair tool accessible from the main menu
- Handles APT dependency problems without opening a terminal

### Single Instance Enforcement
- Uses a **Unix socket lock** (`/tmp/essora-store.lock`) to prevent duplicate instances
- If already running, a second launch brings the existing window to focus instead of opening a new one

### Multilingual Support
Automatic language detection via system locale. Translations loaded from `/usr/local/essora-store/lang/<code>.json`. Falls back to English if the language file is not found.

Supported languages include:

| Code | Language |
|------|----------|
| `en` | English (default) |
| `es` | Spanish |
| `pt` | Portuguese |
| `fr` | French |
| `it` | Italian |
| `hu` | Hungarian |
| `ja` | Japanese |
| `ru` | Russian |
| `ca` | Catalan |
| `zh_CN` | Simplified Chinese |

---

## Architecture

```
/usr/local/essora-store/
├── essora-store.py        # Main application window and UI logic
├── essora_core.py         # CatalogManager, ActivityManager, Application dataclass
├── ui_widgets.py          # PackageRow and shared widget components
├── translations.py        # TranslationManager with locale auto-detection
├── essora_about_dialog.py # About dialog (standalone script)
├── essora-fix-broken.py   # Fix Broken Packages tool (standalone GTK app)
├── essora-repo-update.py  # Repository update helper
├── icons.sh               # Icon helper script
│
├── flatpak.txt            # Flatpak catalog (pipe-delimited: type|app_id|name|...|summary)
├── deb-store.json         # Pre-generated DEB catalog (produced by essora-deb-db)
├── appimage-store.json    # AppImage catalog
├── all_apps.json          # Favorites/quick-launch app list
├── icon-cache.json        # Flatpak icon path cache (app_id → local icon path)
│
├── banners/               # Banner images for home slideshow (.svg, .png, .jpg)
├── icons/
│   ├── app_flatpak.png
│   ├── app_debian.png
│   └── app_appimage.png
├── lang/                  # Translation JSON files (es.json, fr.json, pt.json, ...)
│
├── essora-store.png       # Application icon
└── essora-store.svg       # SVG version of application icon
```

Key design decisions:
- **`CatalogManager`** loads all three catalogs from disk into a unified `list[Application]` and handles installed-state detection, update checking, and APT/Flatpak queries
- **`ActivityManager`** runs installs, removals and updates in daemon threads, dispatching progress back to the UI via `GLib.idle_add`
- **`BackendPage`** is a reusable GTK widget instantiated once per package type (Flatpak, DEB, AppImage), each with its own All/Update/Repos notebook
- **Pagination** — the All tab loads 250 packages at a time with a "Load more" button to avoid GTK list lag with large catalogs

---

## Installation

### From DEB Package (recommended)

```bash
sudo dpkg -i essora-store_3.3-1_amd64.deb
sudo apt-get install -f   # resolve dependencies if needed
```

### From SourceForge

Download the latest `.deb` from the [Essora Linux project page](https://sourceforge.net/projects/essora/).

### Dependencies

| Package | Purpose |
|---------|---------|
| `python3` | Runtime |
| `python3-gi` | GTK3 Python bindings |
| `gir1.2-gtk-3.0` | GTK3 introspection data |
| `gir1.2-gdkpixbuf-2.0` | Image loading |
| `gir1.2-pango-1.0` | Text rendering |
| `flatpak` | Flatpak backend |
| `apt` | DEB/APT backend |
| `wget` | Package downloads |

---

## Running

Essora Store requires **Essora Linux**. It is launched automatically from the application menu, or manually:

```bash
essora-store
```

The launcher script handles `pkexec` elevation so APT operations have the necessary permissions. Running directly as root is also supported.

---

## File Structure After Install

```
/usr/local/essora-store/     ← Application files
/usr/share/applications/     ← essora-store.desktop
/usr/share/pixmaps/essora/   ← Window icon (essora.png)
```

---

## Screenshots

> Screenshots coming soon.

---

## License

Copyright © 2025 **josejp2424**

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License version 3** as published by the Free Software Foundation.

See [LICENSE](LICENSE) or <https://www.gnu.org/licenses/gpl-3.0.html> for details.

---

## Author

**josejp2424**

- GitHub: [https://github.com/josejp2424](https://github.com/josejp2424)
- SourceForge: [https://sourceforge.net/projects/essora/](https://sourceforge.net/projects/essora/)
- Contact: [Telgram Essora](https://t.me/essoralinux#)
