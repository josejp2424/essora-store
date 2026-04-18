#!/usr/bin/env python3
# Essora Store
# Copyright (C) 2025 josejp2424
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Pango
from pathlib import Path
from translations import tr

INSTALLED_BADGE_PATH = "/usr/local/essora-store/icons/installed.svg"
INSTALLED_BADGE_FALLBACK_PATH = "/usr/local/essora-store/icons/install.png"
INSTALLED_BADGE_MAX_WIDTH = 92
INSTALLED_BADGE_MAX_HEIGHT = 46

def _ensure_css():
    css = b"""
    .pkg-card {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        background: rgba(255,255,255,0.03);
    }
    .pkg-card:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.18);
    }
    .pkg-inner {
        padding: 14px;
    }
    .pkg-action-btn,
    .update-row-btn {
        border-radius: 10px;
        min-width: 42px;
        min-height: 34px;
        padding: 0;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

_css_loaded = False

def _pixbuf_from_file(path: str, width: int, height: int = None):
    try:
        p = Path(path)
        if p.exists():
            if height is None:
                height = width
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p), width, height, True)
    except Exception:
        return None
    return None

class PackageRow(Gtk.ListBoxRow):
    """Fila visual de paquete con:
      - Badge (install.png) SOLO si está instalado
      - Acciones:
          instalado  -> reinstalar + desinstalar (sin botón instalar)
          no instalado -> instalar (sin reinstalar/desinstalar)
    """
    def __init__(self, app, activity, selectable=False, on_selection_changed=None):
        super().__init__()
        global _css_loaded
        if not _css_loaded:
            _ensure_css()
            _css_loaded = True

        self.app = app
        self.activity = activity
        # #agregado por josejp2424 — soporte selección múltiple (solo DEB)
        self.selectable = bool(selectable)
        self._on_selection_changed = on_selection_changed
        self.check_select = None

        self.set_selectable(False)
        self.set_activatable(False)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.get_style_context().add_class("pkg-card")
        self.add(frame)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        inner.get_style_context().add_class("pkg-inner")
        frame.add(inner)

        icon_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        icon_wrap.set_size_request(66, -1)
        icon_wrap.set_halign(Gtk.Align.CENTER)
        icon_wrap.set_valign(Gtk.Align.CENTER)
        inner.pack_start(icon_wrap, False, False, 0)

        # #agregado por josejp2424 — checkbox encima del icono para selección múltiple
        if self.selectable:
            self.check_select = Gtk.CheckButton()
            self.check_select.set_halign(Gtk.Align.CENTER)
            self.check_select.set_tooltip_text(tr("Select for batch install"))
            try:
                self.check_select.set_can_focus(False)
            except Exception:
                pass
            self.check_select.connect("toggled", self._on_check_toggled)
            icon_wrap.pack_start(self.check_select, False, False, 0)

        img = Gtk.Image()
        pix = _pixbuf_from_file(getattr(app, "icon_path", ""), 56)
        if pix:
            img.set_from_pixbuf(pix)
        else:
            img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
            img.set_pixel_size(56)
        icon_wrap.pack_start(img, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.set_hexpand(True)
        inner.pack_start(content, True, True, 0)

        title = Gtk.Label()
        title.set_use_markup(True)
        title.set_xalign(0)
        title.set_line_wrap(False)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_max_width_chars(44)
        safe = GLib.markup_escape_text(getattr(app, "name", "") or getattr(app, "app_id", ""))
        title.set_markup(f"<b>{safe}</b>")
        content.pack_start(title, False, False, 0)

        desc = Gtk.Label()
        desc.set_use_markup(True)
        desc.set_xalign(0)
        desc.set_line_wrap(False)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        desc.set_max_width_chars(78)
        s = (getattr(app, "summary", "") or "").strip()
        if len(s) > 150:
            s = s[:147] + "…"
        desc.set_markup(f"<span size='small'>{GLib.markup_escape_text(s)}</span>")
        desc.get_style_context().add_class("dim-label")
        content.pack_start(desc, False, False, 0)

        meta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        content.pack_start(meta, False, False, 0)

        installed_ver = getattr(app, "installed_version", "") or ""
        available_ver = getattr(app, "available_version", "") or ""
        self.version_label = Gtk.Label()
        self.version_label.set_use_markup(True)
        self.version_label.set_xalign(0)
        self.version_label.set_line_wrap(False)
        self.version_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.version_label.get_style_context().add_class("dim-label")
        meta.pack_start(self.version_label, True, True, 0)

        if installed_ver or available_ver:
            if installed_ver and available_ver and installed_ver != available_ver:
                version_text = f"<span size='small' color='#FFA500'>{tr('Version')}: {GLib.markup_escape_text(installed_ver)} → {GLib.markup_escape_text(available_ver)}</span>"
            elif installed_ver:
                version_text = f"<span size='small'>{tr('Version')}: {GLib.markup_escape_text(installed_ver)}</span>"
            elif available_ver:
                version_text = f"<span size='small'>{tr('Version')}: {GLib.markup_escape_text(available_ver)}</span>"
            else:
                version_text = ""
            if version_text:
                self.version_label.set_markup(version_text)

        self.badge_installed = Gtk.Image()
        self.badge_installed.set_no_show_all(True)
        self.badge_installed.set_tooltip_text(tr("Installed"))
        badge_pix = _pixbuf_from_file(INSTALLED_BADGE_PATH, INSTALLED_BADGE_MAX_WIDTH, INSTALLED_BADGE_MAX_HEIGHT)
        if not badge_pix:
            badge_pix = _pixbuf_from_file(INSTALLED_BADGE_FALLBACK_PATH, 18, 18)
        if badge_pix:
            self.badge_installed.set_from_pixbuf(badge_pix)
        else:
            self.badge_installed.set_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.BUTTON)
            try:
                self.badge_installed.set_pixel_size(18)
            except Exception:
                pass
        meta.pack_end(self.badge_installed, False, False, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.set_size_request(104, -1)
        right.set_halign(Gtk.Align.END)
        right.set_valign(Gtk.Align.CENTER)
        inner.pack_end(right, False, False, 0)

        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.pack_end(self.action_box, False, False, 0)

        install_icons = [
            "package-x-generic-symbolic",
            "package-x-generic",
            "system-software-install-symbolic",
            "system-software-install",
            "application-x-deb",
        ]
        self.btn_install = self._mk_icon_btn(install_icons, tr("Install"))
        self.btn_install.connect("clicked", self._on_install)

        self.btn_reinstall = self._mk_icon_btn(["view-refresh-symbolic", "view-refresh"], tr("Reinstall"))
        self.btn_reinstall.connect("clicked", self._on_reinstall)

        self.btn_uninstall = self._mk_icon_btn(["user-trash-symbolic", "user-trash"], tr("Uninstall"))
        self.btn_uninstall.get_style_context().add_class("destructive-action")
        self.btn_uninstall.connect("clicked", self._on_uninstall)

        for w in (self.btn_install, self.btn_reinstall, self.btn_uninstall):
            w.set_no_show_all(True)
            w.get_style_context().add_class("pkg-action-btn")

        self.action_box.pack_start(self.btn_install, False, False, 0)
        self.action_box.pack_start(self.btn_reinstall, False, False, 0)
        self.action_box.pack_start(self.btn_uninstall, False, False, 0)

        self.refresh()

    def _pick_icon_name(self, icon_names):
        if isinstance(icon_names, (list, tuple)):
            names = list(icon_names)
        else:
            names = [str(icon_names)]
        try:
            theme = Gtk.IconTheme.get_default()
        except Exception:
            theme = None
        for n in names:
            if not n:
                continue
            if theme is None:
                return n
            try:
                if theme.has_icon(n):
                    return n
            except Exception:
                return n
        return None

    def _mk_icon_btn(self, icon_names, tooltip: str) -> Gtk.Button:
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(tooltip)
        btn.set_size_request(42, 34)
        btn.get_style_context().add_class("pkg-action-btn")
        try:
            btn.set_focus_on_click(False)
        except Exception:
            pass
        try:
            btn.set_can_focus(False)
        except Exception:
            pass

        icon = self._pick_icon_name(icon_names)
        if icon:
            image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            try:
                image.set_pixel_size(18)
            except Exception:
                pass
            btn.set_image(image)
            btn.set_always_show_image(True)
        else:

            btn.set_label(tooltip)

        return btn

    def _set_busy(self, busy: bool = True):
        for b in (self.btn_install, self.btn_reinstall, self.btn_uninstall):
            try:
                b.set_sensitive(not busy)
            except Exception:
                pass

    def refresh(self):
        installed = bool(getattr(self.app, "installed", False))

        if installed:

            self.btn_install.hide()
            self.btn_reinstall.show()
            self.btn_uninstall.show()
            self.badge_installed.show()
        else:

            self.btn_install.show()
            self.btn_reinstall.hide()
            self.btn_uninstall.hide()
            self.badge_installed.hide()

        # #agregado por josejp2424 — el check solo tiene sentido si NO está instalado
        if self.check_select is not None:
            if installed:
                self.check_select.set_active(False)
                self.check_select.hide()
            else:
                self.check_select.show()

    # #agregado por josejp2424 — helpers para selección múltiple
    def _on_check_toggled(self, _btn):
        if callable(self._on_selection_changed):
            try:
                self._on_selection_changed(self)
            except Exception:
                pass

    def is_selected(self) -> bool:
        return bool(self.check_select and self.check_select.get_active())

    def set_selected(self, value: bool):
        if self.check_select is not None:
            self.check_select.set_active(bool(value))

    def _on_install(self, *_):
        self._set_busy(True)
        self.activity.install(self.app)

    def _on_uninstall(self, *_):
        self._set_busy(True)
        self.activity.uninstall(self.app)

    def _on_reinstall(self, *_):
        self._set_busy(True)
        if hasattr(self.activity, "reinstall"):
            self.activity.reinstall(self.app)
        else:

            self.activity.install(self.app)



class UpdateRow(Gtk.ListBoxRow):
    """Fila para la solapa 'Actualizar'.

    - Icono del backend (DEB / Flatpak / AppImage)
    - Nombre del paquete/app
    - Detalle opcional (por ej. versión instalada → versión nueva)
    - Botón 'Actualizar' para actualizar SOLO ese ítem
    """

    def __init__(self, pkg_type: str, pkg_id: str, activity, icon_path: str = "", detail: str = ""):
        super().__init__()
        global _css_loaded
        if not _css_loaded:
            _ensure_css()
            _css_loaded = True

        self.pkg_type = (pkg_type or "").strip().lower()
        self.pkg_id = (pkg_id or "").strip()
        self.activity = activity

        self.set_selectable(False)
        self.set_activatable(False)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.get_style_context().add_class("pkg-card")
        self.add(frame)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        inner.get_style_context().add_class("pkg-inner")
        frame.add(inner)


        icon_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        icon_wrap.set_size_request(52, -1)
        icon_wrap.set_halign(Gtk.Align.CENTER)
        icon_wrap.set_valign(Gtk.Align.CENTER)

        img = Gtk.Image()
        pix = _pixbuf_from_file(icon_path, 42)
        if pix:
            img.set_from_pixbuf(pix)
        else:
            img.set_from_icon_name("package-x-generic", Gtk.IconSize.DIALOG)
            try:
                img.set_pixel_size(42)
            except Exception:
                pass
        icon_wrap.pack_start(img, False, False, 0)
        inner.pack_start(icon_wrap, False, False, 0)


        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = Gtk.Label(label=self.pkg_id, xalign=0)
        name.set_ellipsize(3)
        try:
            name.set_markup(f"<b>{GLib.markup_escape_text(self.pkg_id)}</b>")
        except Exception:
            pass
        v.pack_start(name, False, False, 0)

        if detail:
            d = Gtk.Label(label=detail, xalign=0)
            d.get_style_context().add_class("dim-label")
            d.set_ellipsize(3)
            v.pack_start(d, False, False, 0)

        inner.pack_start(v, True, True, 0)


        self.btn_update = Gtk.Button()
        self.btn_update.set_relief(Gtk.ReliefStyle.NONE)
        self.btn_update.get_style_context().add_class("update-row-btn")
        self.btn_update.set_tooltip_text(tr("Update"))
        try:
            self.btn_update.set_can_focus(False)
        except Exception:
            pass

        image = Gtk.Image.new_from_icon_name("system-software-update-symbolic", Gtk.IconSize.BUTTON)
        try:
            image.set_pixel_size(18)
        except Exception:
            pass
        self.btn_update.set_image(image)
        self.btn_update.set_always_show_image(True)

        self.btn_update.connect("clicked", self._on_update)
        inner.pack_end(self.btn_update, False, False, 0)

    def _set_busy(self, busy: bool = True):
        try:
            self.btn_update.set_sensitive(not busy)
        except Exception:
            pass

    def _on_update(self, *_):
        self._set_busy(True)
        if hasattr(self.activity, "update_one"):
            self.activity.update_one(self.pkg_type, self.pkg_id)
        else:
  
            if hasattr(self.activity, "update_all"):
                self.activity.update_all(self.pkg_type)
