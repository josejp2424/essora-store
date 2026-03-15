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
import os
import subprocess
import socket
from translations import tr, init_translations


init_translations()



class ProgressDialog(Gtk.Dialog):
    
    def __init__(self, parent, title=None):
        if title is None:
            title = tr("Processing...")
        super().__init__(
            title=title,
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        self.set_default_size(650, 400)
        self.set_border_width(10)
        

        content = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.pack_start(vbox, True, True, 0)
        

        self.operation_label = Gtk.Label()
        self.operation_label.set_markup(f"<b>{tr('Starting operation...')}</b>")
        self.operation_label.set_xalign(0)
        vbox.pack_start(self.operation_label, False, False, 0)
        

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("0%")
        progress_box.pack_start(self.progress_bar, False, False, 0)
        

        self.percent_label = Gtk.Label(label=tr("Preparing..."))
        self.percent_label.set_xalign(0)
        self.percent_label.get_style_context().add_class("dim-label")
        progress_box.pack_start(self.percent_label, False, False, 0)
        
        vbox.pack_start(progress_box, False, False, 0)
        

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, False, 0)
        

        console_label = Gtk.Label(label=tr("Console output:"))
        console_label.set_xalign(0)
        console_label.set_markup(f"<b>{tr('Console output:')}</b>")
        vbox.pack_start(console_label, False, False, 0)
        

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_left_margin(8)
        self.textview.set_right_margin(8)
        self.textview.set_top_margin(8)
        self.textview.set_bottom_margin(8)
        

        font_desc = Pango.FontDescription.from_string("monospace 9")
        self.textview.override_font(font_desc)
        

        try:
            css = b"""
            textview {
                background-color: #2e3436;
                color: #d3d7cf;
            }
            textview text {
                background-color: #2e3436;
                color: #d3d7cf;
            }
            """
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            context = self.textview.get_style_context()
            context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:
            print(f"Error applying CSS: {e}")
        
        self.textbuffer = self.textview.get_buffer()
        scroll.add(self.textview)
        
        vbox.pack_start(scroll, True, True, 0)
        

        self.close_button = Gtk.Button(label=tr("Close"))
        self.close_button.connect("clicked", lambda *_: self.response(Gtk.ResponseType.CLOSE))
        self.close_button.set_no_show_all(True)
        
        button_box = self.get_action_area()
        button_box.pack_start(self.close_button, False, False, 0)
        

        self.is_complete = False
        self.auto_scroll = True
        
        self.show_all()
    
    def set_operation(self, text):
        self.operation_label.set_markup(f"<b>{GLib.markup_escape_text(text)}</b>")
    
    def update_progress(self, fraction, text=None):
        self.progress_bar.set_fraction(fraction)
        
        if text:
            self.progress_bar.set_text(text)
        else:
            percent = int(fraction * 100)
            self.progress_bar.set_text(f"{percent}%")
        
        self.percent_label.set_text(tr("Progress: {percent}%", percent=int(fraction * 100)))
    
    def pulse_progress(self):
        self.progress_bar.pulse()
    
    def append_text(self, text):
        if not text:
            return
        
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, text + "\n")
        

        if self.auto_scroll:
            self.textview.scroll_to_mark(
                self.textbuffer.get_insert(),
                0.0,
                True,
                0.0,
                1.0
            )
    
    def clear_console(self):
        self.textbuffer.set_text("")
    
    def set_complete(self, success=True):
        self.is_complete = True
        
        if success:
            self.update_progress(1.0, tr("✓ Completed"))
            self.percent_label.set_text(tr("Operation completed successfully"))
        else:
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text(tr("✗ Error"))
            self.percent_label.set_text(tr("Operation failed"))
        

        self.close_button.show()
    
    def set_pulsing(self, is_pulsing):
        if is_pulsing:
            GLib.timeout_add(100, self._pulse_callback)
    
    def _pulse_callback(self):
        if not self.is_complete:
            self.pulse_progress()
            return True
        return False  


class SimpleProgressDialog:
    
    _instance = None
    
    @classmethod
    def show(cls, parent, title, operation_type):
        if cls._instance is None:
            cls._instance = ProgressDialog(parent, title)
        else:
            cls._instance.set_title(title)
            cls._instance.set_operation(title)
            cls._instance.clear_console()
            cls._instance.is_complete = False
            cls._instance.close_button.hide()
            cls._instance.update_progress(0.0)
        
        cls._instance.present()
        return cls._instance
    
    @classmethod
    def update_text(cls, text):
        if cls._instance:
            cls._instance.append_text(text)
    
    @classmethod
    def update_bar(cls, fraction):
        if cls._instance:
            cls._instance.update_progress(fraction)
    
    @classmethod
    def hide(cls):
        if cls._instance:
            cls._instance.set_complete(True)

            GLib.timeout_add_seconds(2, cls._close_delayed)
    
    @classmethod
    def _close_delayed(cls):
        if cls._instance:
            cls._instance.destroy()
            cls._instance = None
        return False
    
    @classmethod
    def set_error(cls, error_msg):
        if cls._instance:
            cls._instance.append_text(tr("⌦ ERROR: {msg}", msg=error_msg))
            cls._instance.set_complete(False)


_HOME_CSS_LOADED = False

_SEARCH_POPOVER_CSS_LOADED = False

CATEGORY_TILE_CLASS = {
    "Universal Access": "tile-a11y",
    "Accessories": "tile-accessories",
    "Audio": "tile-audio",
    "Communication": "tile-comms",
    "Development": "tile-dev",
    "Education": "tile-edu",
    "Writing and Languages": "tile-lang",
    "Finance": "tile-fin",
}

CATEGORY_ICON_SYMBOLIC = {
    "Universal Access": "preferences-desktop-accessibility-symbolic",
    "Accessories": "applications-accessories-symbolic",
    "Audio": "multimedia-volume-control-symbolic",
    "Communication": "internet-chat-symbolic",
    "Development": "applications-development-symbolic",
    "Education": "applications-science-symbolic",
    "Writing and Languages": "preferences-desktop-locale-symbolic",
    "Finance": "accessories-calculator-symbolic",
}

def _ensure_home_css():
    global _HOME_CSS_LOADED
    if _HOME_CSS_LOADED:
        return
    try:
        css = """
        .essora-home-banner {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 0;
        }
        .essora-search-wrap,
        .backend-search-wrap {
            background: rgba(255,255,255,0.035);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.10);
            padding: 10px 12px;
        }
        .essora-search-btn,
        .backend-load-more {
            border-radius: 10px;
            min-height: 40px;
        }
        .essora-tile {
            background: #99AE47;
            border-radius: 12px;
            padding: 0;
            color: #ffffff;
            border: none;
        }
        .essora-tile:hover {
            background: #8aa03e;
        }
        .essora-tile label {
            color: #ffffff;
            font-weight: 600;
            letter-spacing: 0.2px;
        }
        .tile-a11y { background: #7C3AED; }
        .tile-a11y:hover { background: #6D28D9; }
        .tile-accessories { background: #2563EB; }
        .tile-accessories:hover { background: #1D4ED8; }
        .tile-audio { background: #DC2626; }
        .tile-audio:hover { background: #B91C1C; }
        .tile-comms { background: #059669; }
        .tile-comms:hover { background: #047857; }
        .tile-dev { background: #EA580C; }
        .tile-dev:hover { background: #C2410C; }
        .tile-edu { background: #0891B2; }
        .tile-edu:hover { background: #0E7490; }
        .tile-lang { background: #7C2D12; }
        .tile-lang:hover { background: #92400E; }
        .tile-fin { background: #15803D; }
        .tile-fin:hover { background: #166534; }
        .featured-card {
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            padding: 0;
        }
        .featured-card:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.20);
        }
        .fav-tile {
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            padding: 8px 10px;
        }
        .fav-tile:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.22);
        }
        .fav-tile label {
            color: #ffffff;
            font-size: 9pt;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        _HOME_CSS_LOADED = True
    except Exception as e:
        print(f"[CSS] Error cargando CSS: {e}")

def _ensure_search_popover_css():
    global _SEARCH_POPOVER_CSS_LOADED
    if _SEARCH_POPOVER_CSS_LOADED:
        return
    try:
        css = b"""
        /* Popover de resultados del buscador (Essora Store) */
        .essora-search-popover,
        .essora-search-popover.background,
        .essora-search-popover > .background {
          background-color: #282C34;
          background-image: none;
          color: #D3DAE3;
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.10);
        }

        .essora-search-frame,
        .essora-search-frame border {
          background: transparent;
          border: none;
        }

        .essora-search-popover list,
        .essora-search-popover list row,
        .essora-search-popover scrolledwindow,
        .essora-search-popover scrolledwindow viewport,
        .essora-search-popover scrolledwindow viewport.view,
        .essora-search-popover viewport {
          background-color: #282C34;
          background-image: none;
          color: #D3DAE3;
        }

        .essora-search-popover .dim-label {
          color: rgba(211, 218, 227, 0.65);
        }

        .essora-search-popover list row {
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .essora-search-popover list row:hover {
          background-color: rgba(46, 179, 152, 0.22);
        }

        .essora-search-popover list row:selected,
        .essora-search-popover list row:selected:hover {
          background-color: #2eb398;
          color: #ffffff;
        }

        .essora-search-popover list row:selected .dim-label {
          color: rgba(255, 255, 255, 0.85);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        _SEARCH_POPOVER_CSS_LOADED = True
    except Exception as e:
        print(f"[CSS] Error cargando CSS de popover: {e}")


from essora_core import CatalogManager, ActivityManager
from ui_widgets import PackageRow

PAGE_SIZE = 250
HOME_BANNER = "/usr/local/essora-store/banners/a_essora-store.svg"
ICON_HOME = "/usr/local/essora-store/essora-store.svg"
ICON_FLATPAK = "/usr/local/essora-store/icons/app_flatpak.png"
ICON_DEB = "/usr/local/essora-store/icons/app_debian.png"
ICON_APPIMAGE = "/usr/local/essora-store/icons/app_appimage.png"

ICON_MAP = {
    "Universal Access": "preferences-desktop-accessibility",
    "Accessories": "applications-accessories",
    "Audio": "multimedia-volume-control",
    "Communication": "internet-chat",
    "Development": "applications-development",
    "Education": "applications-science",
    "Writing and Languages": "preferences-desktop-locale",
    "Finance": "accessories-calculator",
}

WINDOW_ICON = "/usr/share/pixmaps/essora/essora.png"

class BackendPage(Gtk.Box):
    def __init__(self, title: str, pkg_type: str, catalog: CatalogManager, activity: ActivityManager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        _ensure_home_css()
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.pkg_type = pkg_type
        self.catalog = catalog
        self.activity = activity

        self._active_filter = None
        self._apps_all = []
        self._apps_filtered = []  
        self._offset = {"All": 0}  
        self._init_done = False
        self._backend_search_popover = None
        self._backend_search_listbox = None
        self._backend_search_info = None


        search_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_bar.set_margin_top(8)
        search_bar.set_margin_bottom(6)
        search_bar.set_margin_start(6)
        search_bar.set_margin_end(6)
        search_bar.get_style_context().add_class("backend-search-wrap")

        search_label = Gtk.Label(label=tr("Search in {type}:", type=title))
        search_label.get_style_context().add_class("dim-label")
        search_bar.pack_start(search_label, False, False, 0)
        
        self.backend_search_entry = Gtk.SearchEntry()
        self.backend_search_entry.set_placeholder_text(tr("Type 3+ letters and press Enter..."))
        self.backend_search_entry.set_hexpand(True)
        self.backend_search_entry.set_size_request(-1, 40)
        self.backend_search_entry.connect("activate", self._on_backend_search_activate)
        search_bar.pack_start(self.backend_search_entry, True, True, 0)
        
        self.pack_start(search_bar, False, False, 0)

        self.notebook = Gtk.Notebook()
        self.pack_start(self.notebook, True, True, 0)

        self.tabs = {}
        for tab in ["All", "Update", "Repos"]:
            w = self._build_tab_widget(tab)
            self.tabs[tab] = w
            self.notebook.append_page(w["root"], Gtk.Label(label=tr(tab)))

       
        self.notebook.connect("switch-page", self._on_switch_page)
        self._init_done = True

    def _on_switch_page(self, notebook, page, page_num):

        if not getattr(self, '_init_done', False):
            return

        try:
            lab = notebook.get_tab_label(page)
            tab = lab.get_text() if isinstance(lab, Gtk.Label) else ""
        except Exception:
            tab = ""

        tab_map = {tr("Update"): "Update", tr("Repos"): "Repos"}
        tab = tab_map.get(tab, tab)
        
        if tab == "Update":
            self.refresh_updates()
        elif tab == "Repos":
            self.refresh_repos()
        else:
            self.refresh_after_activity()

    def set_filter(self, label: str = None, patterns=None):
        if not label or not patterns:
            self._active_filter = None
        else:
            self._active_filter = {"label": str(label), "patterns": [str(p).lower() for p in patterns if p]}
        if self.catalog and getattr(self.catalog, "all_apps", None):
            self.set_apps(self.catalog.all_apps)

    def _apply_app_filter(self, apps):
        f = self._active_filter
        if not f:
            return apps
        pats = f.get("patterns") or []
        if not pats:
            return apps
        out = []
        for a in apps:
            blob = f"{a.category} {a.name} {a.summary}".lower()
            if any(p in blob for p in pats):
                out.append(a)
        return out

    def _build_tab_widget(self, tab: str):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(10)
        root.set_margin_bottom(10)
        root.set_margin_start(10)
        root.set_margin_end(10)
        if tab in ("Available", "Installed", "All"):  
            listbox = Gtk.ListBox()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroll.add(listbox)
            root.pack_start(scroll, True, True, 0)
            btn_more = Gtk.Button(label=tr("Load {n} more", n=PAGE_SIZE))
            btn_more.get_style_context().add_class("backend-load-more")
            btn_more.connect("clicked", lambda *_: self.load_more(tab))
            root.pack_start(btn_more, False, False, 0)
            status = Gtk.Label(label="")
            status.set_xalign(0)
            root.pack_start(status, False, False, 0)
            return {"root": root, "list": listbox, "more": btn_more, "status": status}
        if tab == "Update":
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            btn = Gtk.Button(label=tr("Update All"))
            btn.get_style_context().add_class("backend-load-more")
            btn.connect("clicked", lambda *_: self.activity.update_all(self.pkg_type))
            h.pack_start(btn, False, False, 0)
            info = Gtk.Label(label=tr("(updates when opening this tab)"))
            info.set_xalign(0)
            info.get_style_context().add_class("dim-label")
            h.pack_start(info, True, True, 0)
            root.pack_start(h, False, False, 0)
            listbox = Gtk.ListBox()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroll.add(listbox)
            root.pack_start(scroll, True, True, 0)
            return {"root": root, "list": listbox}
        
        if tab == "Repos":
            if self.pkg_type == "deb":
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                btn_refresh = Gtk.Button(label=tr("Refresh Repositories"))
                btn_refresh.get_style_context().add_class("backend-load-more")
                btn_refresh.connect("clicked", lambda *_: self.refresh_repos())
                h.pack_start(btn_refresh, False, False, 0)
                info = Gtk.Label(label=tr("Enable/disable APT repositories"))
                info.set_xalign(0)
                info.get_style_context().add_class("dim-label")
                h.pack_start(info, True, True, 0)
                root.pack_start(h, False, False, 0)
                
                listbox = Gtk.ListBox()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                scroll = Gtk.ScrolledWindow()
                scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                scroll.add(listbox)
                root.pack_start(scroll, True, True, 0)
                return {"root": root, "list": listbox}
            else:
                tv = Gtk.TextView()
                tv.set_editable(False)
                tv.set_cursor_visible(False)
                tv.get_buffer().set_text("")
                scroll = Gtk.ScrolledWindow()
                scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                scroll.add(tv)
                root.pack_start(scroll, True, True, 0)
                return {"root": root, "textview": tv}
        
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.get_buffer().set_text("")
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(tv)
        root.pack_start(scroll, True, True, 0)
        return {"root": root, "textview": tv}

    def set_apps(self, apps):
        self._apps_all = [a for a in apps if a.pkg_type == self.pkg_type]
        self.catalog.refresh_installed_flags(self._apps_all)
        self._apps_filtered = self._apply_app_filter(self._apps_all)
        self._offset = {"All": 0}
        self._reset_tab_view("All")
        self.load_more("All")
        self.refresh_updates()
        self.refresh_repos()

    def _reset_tab_view(self, tab):
        if tab not in self.tabs:
            return
        lb = self.tabs[tab]["list"]
        for child in lb.get_children():
            lb.remove(child)

    def load_more(self, tab):
        if tab == "All":
            src = self._apps_filtered
        else:
            return  
        
        off = self._offset.get(tab, 0)
        end = min(off + PAGE_SIZE, len(src))
        lb = self.tabs[tab]["list"]
        
        for app in src[off:end]:
            lb.add(PackageRow(app, self.activity))
        
        lb.show_all()
        self._offset[tab] = end
        self.tabs[tab]["more"].set_visible(end < len(src))
        
        extra = ""
        if self._active_filter and self._active_filter.get("label"):
            extra = f"  |  {tr('Filter')}: {self._active_filter['label']}"
        
        self.tabs[tab]["status"].set_text(tr("Showing {end}/{total}{extra}", end=end, total=len(src), extra=extra))

    def refresh_after_activity(self):
        self.catalog.load_catalog()
        
        self.set_apps(self.catalog.all_apps)
        
        self.refresh_updates()
    def refresh_updates(self):
        lb = self.tabs["Update"]["list"]
        for child in lb.get_children():
            lb.remove(child)

        items = []
        if self.pkg_type == "deb":
            items = self.catalog.get_deb_upgradable()
        elif self.pkg_type == "flatpak":
            up = self.catalog.get_flatpak_upgradable()
            items = sorted([a.app_id for a in self._apps_all if a.app_id in up])

        if not items:
            row = Gtk.ListBoxRow()
            row.add(Gtk.Label(label="No hay actualizaciones detectadas.", xalign=0))
            lb.add(row)
            lb.show_all()
            return

        def _deb_icon_widget(size=22):
            img = Gtk.Image()
            p = "/usr/local/essora-store/icons/app_debian.png"
            try:
                if os.path.exists(p):
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, size, size, True)
                    img.set_from_pixbuf(pb)
                    return img
            except Exception:
                pass
            img.set_from_icon_name("application-x-deb", Gtk.IconSize.BUTTON)
            img.set_pixel_size(size)
            return img

        for pkg in items[:800]:
            row = Gtk.ListBoxRow()
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            h.set_margin_top(6)
            h.set_margin_bottom(6)
            h.set_margin_start(6)
            h.set_margin_end(6)

            if self.pkg_type == "deb":
                h.pack_start(_deb_icon_widget(22), False, False, 0)

            lab = Gtk.Label(label=str(pkg), xalign=0)
            lab.set_ellipsize(Pango.EllipsizeMode.END)
            h.pack_start(lab, True, True, 0)

            if self.pkg_type == "deb":
                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                ico = Gtk.Image.new_from_icon_name("system-software-update", Gtk.IconSize.BUTTON)
                ico.set_pixel_size(18)
                btn.set_image(ico)
                btn.set_always_show_image(True)
                btn.set_tooltip_text(tr("Update this package"))
                btn.connect("clicked", lambda _b, p=str(pkg): self.activity.upgrade_deb_package(p))
                h.pack_end(btn, False, False, 0)

            row.add(h)
            lb.add(row)

        lb.show_all()

    def refresh_repos(self):
        if self.pkg_type == "deb":
            lb = self.tabs["Repos"]["list"]
            for child in lb.get_children():
                lb.remove(child)
            
            repos = self._read_apt_repositories()
            
            if not repos:
                row = Gtk.ListBoxRow()
                row.set_selectable(False)
                row.set_activatable(False)
                label = Gtk.Label(label=tr("No repositories found or error reading files"))
                label.set_margin_top(20)
                label.set_margin_bottom(20)
                row.add(label)
                lb.add(row)
                lb.show_all()
                return
            
            for repo in repos:
                row = self._create_repo_row(repo)
                lb.add(row)
            
            lb.show_all()
            
        elif self.pkg_type == "flatpak":
            if "textview" in self.tabs["Repos"]:
                tv = self.tabs["Repos"]["textview"]
                buf = tv.get_buffer()
                buf.set_text(tr("Update Flathub repositories:\n\n- To update run: flatpak update -y"))
        else:
            if "textview" in self.tabs["Repos"]:
                tv = self.tabs["Repos"]["textview"]
                buf = tv.get_buffer()
                buf.set_text(tr("AppImage repo:\n\n- appimage-store.json is generated by you.\n- You can save AppImages in /usr/local/essora-store/appimages/"))
    
    def _read_apt_repositories(self):
        import glob
        repos = []
        
        try:
            repos.extend(self._parse_sources_file("/etc/apt/sources.list"))
        except Exception as e:
            print(f"[REPOS] Error reading /etc/apt/sources.list: {e}")
        
        try:
            for filepath in sorted(glob.glob("/etc/apt/sources.list.d/*.list")):
                try:
                    repos.extend(self._parse_sources_file(filepath))
                except Exception as e:
                    print(f"[REPOS] Error reading {filepath}: {e}")
        except Exception as e:
            print(f"[REPOS] Error scanning sources.list.d: {e}")
        
        return repos
    
    def _parse_sources_file(self, filepath):
        repos = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[REPOS] Cannot read {filepath}: {e}")
            return repos
        
        for line_num, line in enumerate(lines, 1):
            original_line = line.rstrip('\n')
            stripped = original_line.strip()
            
            if not stripped:
                continue
            
            enabled = not stripped.startswith('#')
            if not enabled:
                stripped = stripped.lstrip('#').strip()
            
            if not stripped or (not stripped.startswith('deb') and '#' in original_line):
                continue
            
            parts = stripped.split()
            if len(parts) < 3:
                continue
            
            repo_type = parts[0] 
            if repo_type not in ('deb', 'deb-src'):
                continue
            
            uri = parts[1]
            suite = parts[2] if len(parts) > 2 else ""
            components = " ".join(parts[3:]) if len(parts) > 3 else ""
            
            repos.append({
                'file': filepath,
                'line_num': line_num,
                'enabled': enabled,
                'type': repo_type,
                'uri': uri,
                'suite': suite,
                'components': components,
                'original_line': original_line
            })
        
        return repos
    
    def _create_repo_row(self, repo):
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        row.set_activatable(False)
        
        # Box principal
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        hbox.set_margin_start(12)
        hbox.set_margin_end(12)
        row.add(hbox)
        
        # Contenido del repo (izquierda)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_hexpand(True)
        hbox.pack_start(vbox, True, True, 0)
        
        # Línea 1: URI + Suite
        uri_label = Gtk.Label()
        uri_label.set_use_markup(True)
        uri_label.set_xalign(0)
        uri_label.set_line_wrap(False)
        uri_label.set_ellipsize(Pango.EllipsizeMode.END)
        uri_text = f"<b>{GLib.markup_escape_text(repo['uri'])}</b>"
        if repo['suite']:
            uri_text += f" <span color='#888888'>{GLib.markup_escape_text(repo['suite'])}</span>"
        uri_label.set_markup(uri_text)
        vbox.pack_start(uri_label, False, False, 0)
        
        # Línea 2: Components + File
        detail_label = Gtk.Label()
        detail_label.set_use_markup(True)
        detail_label.set_xalign(0)
        detail_label.set_line_wrap(False)
        detail_label.set_ellipsize(Pango.EllipsizeMode.END)
        detail_text = f"<small>{repo['type']}"
        if repo['components']:
            detail_text += f" [{GLib.markup_escape_text(repo['components'])}]"
        detail_text += f" — {GLib.markup_escape_text(repo['file'])}:{repo['line_num']}</small>"
        detail_label.set_markup(detail_text)
        detail_label.get_style_context().add_class("dim-label")
        vbox.pack_start(detail_label, False, False, 0)
        
        # Switch (derecha)
        switch = Gtk.Switch()
        switch.set_active(repo['enabled'])
        switch.set_valign(Gtk.Align.CENTER)
        switch.connect("state-set", self._on_repo_switch_toggled, repo)
        hbox.pack_end(switch, False, False, 0)
        
        return row
    
    def _on_repo_switch_toggled(self, switch, state, repo):
        import subprocess
        
        try:
            with open(repo['file'], 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            self._show_error_dialog(tr("Error reading file"), 
                                   tr("Cannot read {file}: {error}", file=repo['file'], error=str(e)))
            switch.set_active(not state)
            return True
        
        if repo['line_num'] > len(lines):
            self._show_error_dialog(tr("Error"), 
                                   tr("Line number {num} not found in {file}", 
                                      num=repo['line_num'], file=repo['file']))
            switch.set_active(not state)
            return True
        
        idx = repo['line_num'] - 1
        original_line = lines[idx].rstrip('\n')
        
        if state:
            new_line = original_line.lstrip('#').lstrip()
            if not new_line.startswith('deb'):
                new_line = f"{repo['type']} {repo['uri']} {repo['suite']} {repo['components']}"
        else:
            stripped = original_line.lstrip('#').lstrip()
            new_line = f"# {stripped}"
        
        lines[idx] = new_line + '\n'
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp:
                tmp.writelines(lines)
                tmp_path = tmp.name
            
            result = subprocess.run(['cp', tmp_path, repo['file']], 
                                  capture_output=True, text=True, check=False)
            
            # Eliminar temporal
            import os
            os.unlink(tmp_path)
            
            if result.returncode != 0:
                raise Exception(result.stderr or "Copy failed")
            
            # Actualizar estado del repo en memoria
            repo['enabled'] = state
            repo['original_line'] = new_line
            
            # Mostrar notificación
            status_text = tr("enabled") if state else tr("disabled")
            print(f"[REPOS] Repository {status_text}: {repo['uri']}")
            
            return False
            
        except Exception as e:
            self._show_error_dialog(tr("Error saving"), 
                                   tr("Cannot save changes to {file}: {error}", 
                                      file=repo['file'], error=str(e)))
            switch.set_active(not state)
            return True
    
    def _show_error_dialog(self, title, message):
        dlg = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dlg.format_secondary_text(message)
        dlg.run()
        dlg.destroy()


    def _ensure_backend_search_popover(self):
        if self._backend_search_popover:
            return
        _ensure_search_popover_css()
        pop = Gtk.Popover()
        pop.set_relative_to(self.backend_search_entry)
        pop.set_position(Gtk.PositionType.BOTTOM)
        pop.set_modal(True)
        pop.get_style_context().add_class("essora-search-popover")
        frame = Gtk.Frame()
        frame.get_style_context().add_class("essora-search-frame")
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        pop.add(frame)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        v.set_margin_top(8)
        v.set_margin_bottom(8)
        v.set_margin_start(10)
        v.set_margin_end(10)
        frame.add(v)
        self._backend_search_info = Gtk.Label(label=tr("Type to search and press Enter."))
        self._backend_search_info.set_xalign(0)
        self._backend_search_info.get_style_context().add_class("dim-label")
        v.pack_start(self._backend_search_info, False, False, 0)
        lb = Gtk.ListBox()
        lb.get_style_context().add_class("essora-search-list")
        lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        lb.connect("row-activated", self._on_backend_search_row_activated)
        sc = Gtk.ScrolledWindow()
        sc.get_style_context().add_class("essora-search-scrolled")
        sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc.set_size_request(480, 320)
        sc.add(lb)
        v.pack_start(sc, True, True, 0)
        self._backend_search_popover = pop
        self._backend_search_listbox = lb
        pop.show_all()

    def _on_backend_search_activate(self, entry):
        q = (entry.get_text() or "").strip()
        self._ensure_backend_search_popover()
        if len(q) < 3:
            self._backend_search_info.set_text(tr("Type 3 or more letters and press Enter."))
            self._set_backend_search_results([])
            self._backend_search_popover.show_all()
            self._backend_search_popover.popup()
            return
        self._backend_search_info.set_text(tr("Results for: {q}", q=q))
        self._run_backend_search(q)
        self._backend_search_popover.show_all()
        self._backend_search_popover.popup()

    def _set_backend_search_results(self, apps):
        lb = self._backend_search_listbox
        for child in lb.get_children():
            lb.remove(child)
        if not apps:
            row = Gtk.ListBoxRow()
            row.add(Gtk.Label(label=tr("No results."), xalign=0))
            lb.add(row)
            lb.show_all()
            return
        for app in apps[:60]:
            row = Gtk.ListBoxRow()
            row.app = app
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            h.set_margin_top(6)
            h.set_margin_bottom(6)
            h.set_margin_start(6)
            h.set_margin_end(6)
            img = Gtk.Image()
            if getattr(app, "icon_path", "") and os.path.exists(app.icon_path):
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(app.icon_path, 28, 28, True)
                    img.set_from_pixbuf(pix)
                except Exception:
                    img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                    img.set_pixel_size(28)
            else:
                img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                img.set_pixel_size(28)
            h.pack_start(img, False, False, 0)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name = Gtk.Label(label=app.name or app.app_id, xalign=0)
            name.set_ellipsize(3)
            sub = Gtk.Label(label=f"{app.pkg_type.upper()}  •  {app.app_id}", xalign=0)
            sub.get_style_context().add_class("dim-label")
            v.pack_start(name, False, False, 0)
            v.pack_start(sub, False, False, 0)
            h.pack_start(v, True, True, 0)
            row.add(h)
            lb.add(row)
        lb.show_all()

    def _run_backend_search(self, query):
        apps = getattr(self.catalog, "all_apps", []) or []
        if not apps:
            self._set_backend_search_results([])
            self._backend_search_info.set_text(tr("Empty catalog (still loading). Try again in a few seconds."))
            return

        backend_apps = [a for a in apps if a.pkg_type == self.pkg_type]
        q = query.lower()
        out = []
        for a in backend_apps:
            blob = f"{a.name} {a.app_id} {a.summary} {a.category}".lower()
            if q in blob:
                out.append(a)
        self._set_backend_search_results(out)

    def _on_backend_search_row_activated(self, listbox, row):
        app = getattr(row, "app", None)
        if not app:
            return
        q = (self.backend_search_entry.get_text() or "").strip().lower()
        if q:
            try:
                self.set_filter(label=tr("Search: {q}", q=q), patterns=[q])
            except Exception:
                pass
        try:
            self._backend_search_popover.popdown()
        except Exception:
            pass

class HomePage(Gtk.Box):
    def __init__(self, on_open_category, on_open_app=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(14)
        self.set_margin_end(14)
        _ensure_home_css()
        self.on_open_category = on_open_category
        self.on_open_app = on_open_app
        self.banner_paths = self._discover_banners("/usr/local/essora-store/banners")
        if not self.banner_paths:
            self.banner_paths = [HOME_BANNER]
        self.banner_index = 0
        self._last_banner_width = 0

        banner_frame = Gtk.Frame()
        banner_frame.set_shadow_type(Gtk.ShadowType.NONE)
        banner_frame.get_style_context().add_class("essora-home-banner")

        self.banner_overlay = Gtk.Overlay()
        self.banner_overlay.set_halign(Gtk.Align.FILL)
        self.banner_overlay.set_valign(Gtk.Align.START)
        self.banner = Gtk.Image()
        self.banner.set_halign(Gtk.Align.FILL)
        self.banner.set_valign(Gtk.Align.START)
        self.banner_overlay.add(self.banner)
        self.dots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.dots_box.set_halign(Gtk.Align.CENTER)
        self.dots_box.set_valign(Gtk.Align.END)
        self.dots_box.set_margin_bottom(12)
        dots_frame = Gtk.EventBox()
        dots_frame.set_visible_window(False)
        dots_frame.set_halign(Gtk.Align.CENTER)
        dots_frame.set_valign(Gtk.Align.END)
        dots_frame.set_margin_bottom(10)
        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        inner.set_margin_top(4)
        inner.set_margin_bottom(4)
        inner.set_margin_start(10)
        inner.set_margin_end(10)
        inner.pack_start(self.dots_box, False, False, 0)
        dots_frame.add(inner)
        self.banner_overlay.add_overlay(dots_frame)
        banner_frame.add(self.banner_overlay)
        self.pack_start(banner_frame, False, False, 0)
        self.banner_overlay.connect("size-allocate", self._on_banner_allocate)

        search_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_wrap.set_halign(Gtk.Align.CENTER)
        search_wrap.get_style_context().add_class("essora-search-wrap")
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(tr("Search apps (DEB / Flatpak / AppImage)…"))
        self.search_entry.set_width_chars(44)
        self.search_entry.set_size_request(460, 42)
        search_wrap.pack_start(self.search_entry, False, False, 0)

        self.search_button = Gtk.Button.new_from_icon_name("system-search", Gtk.IconSize.BUTTON)
        self.search_button.get_style_context().add_class("essora-search-btn")
        self.search_button.set_tooltip_text(tr("Search"))
        self.search_button.set_size_request(46, 42)
        search_wrap.pack_start(self.search_button, False, False, 0)
        self.pack_start(search_wrap, False, False, 0)

        categories_grid = Gtk.Grid()
        categories_grid.set_column_spacing(12)
        categories_grid.set_row_spacing(12)
        categories_grid.set_column_homogeneous(True)
        categories_grid.set_row_homogeneous(True)
        self.pack_start(categories_grid, False, False, 0)

        categories = [
            ("Universal Access", ["access", "accessibility", "a11y", "acces"], "flatpak"),
            ("Accessories", ["accessory", "accessories", "plugin", "addon", "tool"], "deb"),
            ("Audio", ["audio", "music", "musi", "sound"], "flatpak"),
            ("Communication", ["chat", "mess", "mail", "email", "telegram", "discord", "comunic"], "flatpak"),
            ("Development", ["dev", "develop", "program", "code", "ide", "desarroll"], "deb"),
            ("Education", ["edu", "learn", "course", "educ"], "deb"),
            ("Writing and Languages", ["office", "writer", "document", "lang", "idioma", "escrit"], "deb"),
            ("Finance", ["finance", "finanz", "money", "bank", "wallet"], "deb"),
        ]

        for idx, (label, pats, default_backend) in enumerate(categories):
            btn = Gtk.Button()
            btn.set_hexpand(True)
            btn.set_vexpand(True)
            btn.set_size_request(0, 58)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("essora-tile")
            btn.get_style_context().add_class(CATEGORY_TILE_CLASS.get(label, ""))

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_halign(Gtk.Align.START)
            box.set_valign(Gtk.Align.CENTER)
            box.set_margin_start(14)
            box.set_margin_end(14)
            box.set_margin_top(8)
            box.set_margin_bottom(8)

            icon_name = CATEGORY_ICON_SYMBOLIC.get(label, "applications-other-symbolic")
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            img.set_pixel_size(14)

            lab = Gtk.Label(label=tr(label).upper(), xalign=0)
            lab.set_line_wrap(False)
            lab.set_ellipsize(Pango.EllipsizeMode.END)
            font_desc = Pango.font_description_from_string("9")
            lab.override_font(font_desc)

            box.pack_start(img, False, False, 0)
            box.pack_start(lab, True, True, 0)
            btn.add(box)
            btn.connect("clicked", lambda _b, l=label, p=pats, bk=default_backend: self.on_open_category(l, p, bk))
            categories_grid.attach(btn, idx % 4, idx // 4, 1, 1)

        self.flatpak_scroll = Gtk.ScrolledWindow()
        self.flatpak_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flatpak_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.flatpak_scroll.set_size_request(-1, 520)

        self.flatpak_flow = Gtk.FlowBox()
        self.flatpak_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flatpak_flow.set_homogeneous(True)
        self.flatpak_flow.set_row_spacing(10)
        self.flatpak_flow.set_column_spacing(10)
        self.flatpak_flow.set_max_children_per_line(4)
        self.flatpak_flow.set_min_children_per_line(4)

        self.flatpak_scroll.add(self.flatpak_flow)
        self.pack_start(self.flatpak_scroll, False, False, 0)

        self.fav_flow = Gtk.FlowBox()
        self.fav_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.fav_flow.set_homogeneous(True)
        self.fav_flow.set_row_spacing(8)
        self.fav_flow.set_column_spacing(8)
        self.fav_flow.set_max_children_per_line(8)
        self.fav_flow.set_min_children_per_line(4)
        self.pack_start(self.fav_flow, False, False, 0)

        GLib.idle_add(self._load_flatpak_apps)
        GLib.idle_add(self._load_favorites)
        GLib.idle_add(self._build_dots)
        GLib.idle_add(self._render_current_banner)
        GLib.timeout_add_seconds(7, self._next_banner)

    def _load_flatpak_apps(self):
        flatpak_txt = "/usr/local/essora-store/flatpak.txt"
        icon_cache_json = "/usr/local/essora-store/icon-cache.json"


        for c in getattr(self, "flatpak_flow", Gtk.FlowBox()).get_children():
            try:
                self.flatpak_flow.remove(c)
            except Exception:
                pass

        if not os.path.exists(flatpak_txt):
            lbl = Gtk.Label(label="No se encontró flatpak.txt", xalign=0)
            lbl.set_margin_top(10)
            lbl.set_margin_bottom(10)
            self.flatpak_flow.add(lbl)
            self.flatpak_flow.show_all()
            return False


        icon_cache = {}
        if os.path.exists(icon_cache_json):
            try:
                import json
                with open(icon_cache_json, "r", encoding="utf-8", errors="replace") as f:
                    icon_cache = json.load(f) or {}
            except Exception as e:
                print(f"[FLATPAK] Error leyendo icon-cache.json: {e}")
                icon_cache = {}

        def _make_feature_card(app_id, name, summary):
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_can_focus(False)
            btn.set_hexpand(True)
            btn.get_style_context().add_class("featured-card")
            btn.set_size_request(0, 74)

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_margin_top(10)
            hbox.set_margin_bottom(10)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)

            icon_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            icon_wrap.set_size_request(38, -1)
            icon_wrap.set_halign(Gtk.Align.CENTER)
            icon_wrap.set_valign(Gtk.Align.CENTER)

            icon = Gtk.Image()
            icon_loaded = False
            icon_path = icon_cache.get(app_id)
            if icon_path and os.path.exists(icon_path):
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, 28, 28, True) 
                    icon.set_from_pixbuf(pix)
                    icon_loaded = True
                except Exception as e:
                    print(f"[FLATPAK] Error cargando icono {app_id}: {e}")

            if not icon_loaded:
                if os.path.exists(ICON_FLATPAK):
                    try:
                        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(ICON_FLATPAK, 28, 28, True) 
                        icon.set_from_pixbuf(pix)
                    except Exception:
                        icon.set_from_icon_name("system-software-install", Gtk.IconSize.BUTTON)
                        icon.set_pixel_size(28)  
                else:
                    icon.set_from_icon_name("system-software-install", Gtk.IconSize.BUTTON)
                    icon.set_pixel_size(28)  

            icon_wrap.pack_start(icon, False, False, 0)
            hbox.pack_start(icon_wrap, False, False, 0)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{GLib.markup_escape_text(name)}</b>")
            name_label.set_xalign(0)
            name_label.set_ellipsize(Pango.EllipsizeMode.END)
            name_label.set_max_width_chars(28)

            font_desc_name = Pango.font_description_from_string("9")
            name_label.override_font(font_desc_name)

            sum_label = Gtk.Label(label=summary or "")
            sum_label.set_xalign(0)
            sum_label.set_max_width_chars(38)
            sum_label.set_ellipsize(Pango.EllipsizeMode.END)
            sum_label.get_style_context().add_class("dim-label")

            font_desc_sum = Pango.font_description_from_string("8")
            sum_label.override_font(font_desc_sum)

            vbox.pack_start(name_label, False, False, 0)
            vbox.pack_start(sum_label, False, False, 0)
            hbox.pack_start(vbox, True, True, 0)

            btn.add(hbox)

            def _go(_btn):
                try:
                    if self.on_open_app:
                        self.on_open_app("flatpak", app_id, name)
                    else:
                        self.on_open_category("Flatpak", [name.lower(), app_id.lower()], "flatpak")
                except Exception:
                    pass

            btn.connect("clicked", _go)
            return btn

        apps_loaded = 0
        try:
            with open(flatpak_txt, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if len(parts) < 3:
                        continue

                    app_id = parts[1].strip()
                    name = (parts[2].strip() or app_id)
                    summary = parts[4].strip() if len(parts) >= 5 else ""

                    card = _make_feature_card(app_id, name, summary)
                    self.flatpak_flow.add(card)

                    apps_loaded += 1
                    if apps_loaded >= 100: 
                        break
        except Exception as e:
            print(f"[FLATPAK] Error leyendo flatpak.txt: {e}")

        self.flatpak_flow.show_all()
        return False

    def _load_favorites(self):
        json_path = "/usr/local/essora-store/all_apps.json"
        if not os.path.exists(json_path):
            return False
        try:
            import json
            data = json.loads(open(json_path, "r", encoding="utf-8", errors="replace").read())
        except Exception as e:
            print(f"[FAV] Error: {e}")
            return False
        if not isinstance(data, list):
            return False
        for child in self.fav_flow.get_children():
            self.fav_flow.remove(child)
        theme = Gtk.IconTheme.get_default()
        shown = 0
        for it in data:
            if not isinstance(it, dict):
                continue
            pkg_id = str(it.get("pkg_id") or it.get("app_id") or it.get("id") or "").strip()
            if not pkg_id:
                continue
            name = str(it.get("name") or pkg_id).strip()
            pkg_type = str(it.get("pkg_type") or "flatpak").strip().lower()
            icon_name = str(it.get("icon_name") or "").strip()
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_size_request(110, 88)
            btn.get_style_context().add_class("fav-tile")
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2) 
            v.set_halign(Gtk.Align.CENTER)
            v.set_valign(Gtk.Align.CENTER)
            img = Gtk.Image()
            pix = None
            if icon_name:
                try:
                    info = theme.lookup_icon(icon_name, 36, 0)  
                    if info:
                        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(info.get_filename(), 36, 36, True)
                except Exception:
                    pix = None
            if pix is None:
                fallback = "application-x-executable"
                if pkg_type == "deb":
                    fallback = "package-x-generic"
                elif pkg_type == "flatpak":
                    fallback = "system-software-install"
                img.set_from_icon_name(fallback, Gtk.IconSize.DIALOG)
                img.set_pixel_size(36) 
            else:
                img.set_from_pixbuf(pix)
            lbl = Gtk.Label(label=name)
            lbl.set_max_width_chars(14)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_justify(Gtk.Justification.CENTER)

            font_desc = Pango.font_description_from_string("8")
            lbl.override_font(font_desc)
            v.pack_start(img, False, False, 0)
            v.pack_start(lbl, False, False, 0)
            btn.add(v)
            btn.connect("clicked", self._on_favorite_clicked, pkg_type, pkg_id, name)
            self.fav_flow.add(btn)
            shown += 1
            if shown >= 16:
                break
        self.fav_flow.show_all()
        return False

    def _on_favorite_clicked(self, _btn, pkg_type, pkg_id, name):
        if callable(self.on_open_app):
            self.on_open_app(pkg_type, pkg_id, name)

    def _discover_banners(self, folder):
        try:
            if not os.path.isdir(folder):
                return []
            files = []
            for fn in sorted(os.listdir(folder)):
                low = fn.lower()
                if low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png") or low.endswith(".svg"):
                    files.append(os.path.join(folder, fn))
            return files
        except Exception:
            return []

    def _build_dots(self):
        for c in self.dots_box.get_children():
            self.dots_box.remove(c)
        n = len(self.banner_paths)
        for i in range(n):
            ev = Gtk.EventBox()
            ev.set_visible_window(False)
            lbl = Gtk.Label()
            lbl.set_use_markup(True)
            lbl.set_markup("<span size='large'>●</span>" if i == self.banner_index else "<span size='large'>○</span>")
            ev.add(lbl)
            ev.connect("button-press-event", self._on_dot_click, i)
            self.dots_box.pack_start(ev, False, False, 0)
        self.dots_box.show_all()
        return False

    def _on_dot_click(self, _ev, _event, index):
        try:
            self.banner_index = int(index) % max(1, len(self.banner_paths))
        except Exception:
            self.banner_index = 0
        self._render_current_banner()
        return True

    def _update_dots(self):
        for i, ev in enumerate(self.dots_box.get_children()):
            child = None
            try:
                child = ev.get_children()[0] if hasattr(ev, "get_children") else None
            except Exception:
                child = None
            if isinstance(child, Gtk.Label):
                child.set_markup("<span size='large'>●</span>" if i == self.banner_index else "<span size='large'>○</span>")

    def _on_banner_allocate(self, _widget, allocation):
        if allocation.width and allocation.width != self._last_banner_width:
            self._last_banner_width = allocation.width
            self._render_current_banner()
        return False

    def _render_current_banner(self):
        path = self.banner_paths[self.banner_index]
        if not os.path.exists(path):
            self.banner.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
            self._update_dots()
            return False
        try:
            w = self._last_banner_width or 860
            h = 230
            

            if path.lower().endswith('.svg'):
                pix = GdkPixbuf.Pixbuf.new_from_file_at_size(path, w, h)
                self.banner.set_from_pixbuf(pix)
            else:
  
                pix = GdkPixbuf.Pixbuf.new_from_file(path)
                h = max(1, int(w * (pix.get_height() / max(1, pix.get_width()))))
                h = min(h, 230)
                scaled = pix.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
                self.banner.set_from_pixbuf(scaled)
        except Exception as e:
            print(f"[BANNER] Error: {e}")
            self.banner.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        self._update_dots()
        return False

    def _next_banner(self):
        if not self.banner_paths:
            return True
        self.banner_index = (self.banner_index + 1) % len(self.banner_paths)
        self._render_current_banner()
        return True


class EssoraStoreWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Essora Store")
        self.set_default_size(860, 660)
        self.set_position(Gtk.WindowPosition.CENTER)
        

        try:
            if os.path.exists(WINDOW_ICON):
                self.set_icon_from_file(WINDOW_ICON)
        except Exception as e:
            print(f"[WINDOW] No se pudo cargar el icono: {e}")
        
        self.catalog = CatalogManager()
        self.activity = ActivityManager(self)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        self._build_header()
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.pack_start(self.stack, True, True, 0)
        self.add(root)
        self.page_home = HomePage(self._open_category_from_home, self._open_app_from_home)
        

        self.page_home.search_entry.connect("activate", self._on_search_activate)
        self.page_home.search_button.connect("clicked", lambda *_: self._on_search_activate(self.page_home.search_entry))
        self.search_entry = self.page_home.search_entry  
        
        self.page_flatpak = BackendPage("Flatpak", "flatpak", self.catalog, self.activity)
        self.page_deb = BackendPage("DEB", "deb", self.catalog, self.activity)
        self.page_appimage = BackendPage("AppImage", "appimage", self.catalog, self.activity)
        self.home_scroll = Gtk.ScrolledWindow()
        self.home_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.home_scroll.set_overlay_scrolling(True)
        self.home_scroll.add(self.page_home)
        self.stack.add_named(self.home_scroll, "home")
        self.stack.add_named(self.page_flatpak, "flatpak")
        self.stack.add_named(self.page_deb, "deb")
        self.stack.add_named(self.page_appimage, "appimage")
        self.stack.set_visible_child_name("home")
        GLib.idle_add(self._load_catalog_async)

    def _build_header(self):
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title("Essora Store")
        hb.set_subtitle("")
        self.set_titlebar(hb)

        def _img_from_file(icon_path, fallback_icon_name):
            if icon_path and os.path.exists(icon_path):
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, 18, 18, True)
                    return Gtk.Image.new_from_pixbuf(pix)
                except Exception as e:
                    print(f"[ICON] Error: {e}")
            return Gtk.Image.new_from_icon_name(fallback_icon_name, Gtk.IconSize.BUTTON)

        def create_button_with_icon_and_text(stack_name, icon_path, fallback_icon, label):
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            

            img = _img_from_file(icon_path, fallback_icon)
            box.pack_start(img, False, False, 0)
            

            lbl = Gtk.Label(label=label)
            box.pack_start(lbl, False, False, 0)
            
            btn.add(box)
            btn.connect("clicked", lambda *_: self.stack.set_visible_child_name(stack_name))
            return btn


        hb.pack_start(create_button_with_icon_and_text("home", ICON_HOME, "go-home", tr("Home")))
        hb.pack_start(create_button_with_icon_and_text("flatpak", ICON_FLATPAK, "applications-other", tr("Flatpak")))
        hb.pack_start(create_button_with_icon_and_text("deb", ICON_DEB, "package-x-generic", tr("DEB")))
        hb.pack_start(create_button_with_icon_and_text("appimage", ICON_APPIMAGE, "application-x-executable", tr("AppImage")))


        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu_btn.set_tooltip_text(tr("Menu"))
        

        popover = Gtk.Popover.new(menu_btn)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Opción: Fix Broken Packages
        fix_btn = Gtk.ModelButton()
        fix_btn.set_label(tr("Fix Broken Packages"))
        fix_btn.connect("clicked", self._on_fix_broken_clicked)
        vbox.pack_start(fix_btn, False, False, 0)
        
        # Separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, False, False, 3)

        about_btn = Gtk.ModelButton()
        about_btn.set_label(tr("About"))
        about_btn.connect("clicked", self._on_about_clicked)
        vbox.pack_start(about_btn, False, False, 0)
        
        vbox.show_all()
        popover.add(vbox)
        menu_btn.set_popover(popover)
        
        hb.pack_end(menu_btn)
        

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar apps (DEB / Flatpak / AppImage)…")
        self.search_entry.connect("activate", self._on_search_activate)
        
        self._search_popover = None
        self._search_listbox = None

    def _on_fix_broken_clicked(self, *args):
        script = "/usr/local/essora-store/essora-fix-broken.py"
        if not os.path.exists(script):
            dlg = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Fix Broken tool not found"
            )
            dlg.format_secondary_text(f"Expected at: {script}")
            dlg.run()
            dlg.destroy()
            return
        try:
            env = os.environ.copy()
            for var in ("DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"):
                if var not in env and os.environ.get(var):
                    env[var] = os.environ[var]
            subprocess.Popen(
                ["python3", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                env=env
            )
        except Exception as e:
            dlg = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error launching Fix Broken tool"
            )
            dlg.format_secondary_text(str(e))
            dlg.run()
            dlg.destroy()

    def _on_about_clicked(self, *args):
        about_script = "/usr/local/essora-store/essora_about_dialog.py"
        

        if not os.path.exists(about_script):
            dlg = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=tr("About Script Not Found"),
            )
            dlg.format_secondary_text(
                tr("File not found:\n{script}\n\nMake sure it exists and has execution permissions:\nsudo chmod +x {script}", script=about_script)
            )
            dlg.run()
            dlg.destroy()
            return
        

        if not os.access(about_script, os.X_OK):
            dlg = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text=tr("About script does not have execution permissions"),
            )
            dlg.format_secondary_text(
                tr("Do you want to give it execution permissions?\n\nWill execute: sudo chmod +x {script}", script=about_script)
            )
            response = dlg.run()
            dlg.destroy()
            
            if response == Gtk.ResponseType.OK:
                try:
                    subprocess.run(["pkexec", "chmod", "+x", about_script], check=True)

                    subprocess.Popen([about_script])
                except Exception as e:
                    err_dlg = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text=tr("Error setting permissions"),
                    )
                    err_dlg.format_secondary_text(str(e))
                    err_dlg.run()
                    err_dlg.destroy()
            return
        

        try:
            subprocess.Popen([about_script])
        except Exception as e:
            dlg = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=tr("Error executing About"),
            )
            dlg.format_secondary_text(tr("Could not execute:\n{e}", e=e))
            dlg.run()
            dlg.destroy()
    

    def show_progress_dialog(self, title, operation_type):
        SimpleProgressDialog.show(self, title, operation_type)
        return False
    
    def update_progress_text(self, text):
        SimpleProgressDialog.update_text(text)
        return False
    
    def update_progress_bar(self, fraction):
        SimpleProgressDialog.update_bar(fraction)
        return False
    
    def hide_progress_dialog(self):
        SimpleProgressDialog.hide()
        return False

    def _ensure_search_popover(self):
        if self._search_popover is not None:
            return
        _ensure_search_popover_css()
        pop = Gtk.Popover.new(self.search_entry)
        pop.set_position(Gtk.PositionType.BOTTOM)
        pop.get_style_context().add_class("essora-search-popover")
        frame = Gtk.Frame()
        frame.get_style_context().add_class("essora-search-frame")
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pop.add(frame)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        v.set_margin_top(8)
        v.set_margin_bottom(8)
        v.set_margin_start(10)
        v.set_margin_end(10)
        frame.add(v)
        self._search_info = Gtk.Label(label=tr("Type to search and press Enter."))
        self._search_info.set_xalign(0)
        self._search_info.get_style_context().add_class("dim-label")
        v.pack_start(self._search_info, False, False, 0)
        lb = Gtk.ListBox()
        lb.get_style_context().add_class("essora-search-list")
        lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        lb.connect("row-activated", self._on_search_row_activated)
        sc = Gtk.ScrolledWindow()
        sc.get_style_context().add_class("essora-search-scrolled")
        sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc.set_size_request(480, 320)
        sc.add(lb)
        v.pack_start(sc, True, True, 0)
        self._search_popover = pop
        self._search_listbox = lb
        pop.show_all()

    def _on_search_activate(self, entry):
        q = (entry.get_text() or "").strip()
        self._ensure_search_popover()
        if len(q) < 3:
            self._search_info.set_text(tr("Type 3 or more letters and press Enter."))
            self._set_search_results([])
            self._search_popover.show_all()
            self._search_popover.popup()
            return
        self._search_info.set_text(tr("Results for: {q}", q=q))
        self._run_global_search(q)
        self._search_popover.show_all()
        self._search_popover.popup()

    def _set_search_results(self, apps):
        lb = self._search_listbox
        for child in lb.get_children():
            lb.remove(child)
        if not apps:
            row = Gtk.ListBoxRow()
            row.add(Gtk.Label(label=tr("No results."), xalign=0))
            lb.add(row)
            lb.show_all()
            return
        for app in apps[:60]:
            row = Gtk.ListBoxRow()
            row.app = app
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            h.set_margin_top(6)
            h.set_margin_bottom(6)
            h.set_margin_start(6)
            h.set_margin_end(6)
            img = Gtk.Image()
            if getattr(app, "icon_path", "") and os.path.exists(app.icon_path):
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(app.icon_path, 28, 28, True)
                    img.set_from_pixbuf(pix)
                except Exception:
                    img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                    img.set_pixel_size(28)
            else:
                img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                img.set_pixel_size(28)
            h.pack_start(img, False, False, 0)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name = Gtk.Label(label=app.name or app.app_id, xalign=0)
            name.set_ellipsize(3)
            sub = Gtk.Label(label=f"{app.pkg_type.upper()}  •  {app.app_id}", xalign=0)
            sub.get_style_context().add_class("dim-label")
            v.pack_start(name, False, False, 0)
            v.pack_start(sub, False, False, 0)
            h.pack_start(v, True, True, 0)
            row.add(h)
            lb.add(row)
        lb.show_all()

    def _run_global_search(self, query):
        apps = getattr(self.catalog, "all_apps", []) or []
        if not apps:
            self._set_search_results([])
            self._search_info.set_text(tr("Empty catalog (still loading). Try again in a few seconds."))
            return
        q = query.lower()
        out = []
        for a in apps:
            blob = f"{a.name} {a.app_id} {a.summary} {a.category} {a.pkg_type}".lower()
            if q in blob:
                out.append(a)
        self._set_search_results(out)

    def _on_search_row_activated(self, listbox, row):
        app = getattr(row, "app", None)
        if not app:
            return
        if app.pkg_type == "deb":
            self.stack.set_visible_child_name("deb")
            page = self.page_deb
        elif app.pkg_type == "appimage":
            self.stack.set_visible_child_name("appimage")
            page = self.page_appimage
        else:
            self.stack.set_visible_child_name("flatpak")
            page = self.page_flatpak
        q = (self.search_entry.get_text() or "").strip().lower()
        if q:
            try:
                page.set_filter(label=tr("Search: {q}", q=q), patterns=[q])
            except Exception:
                pass
        try:
            self._search_popover.popdown()
        except Exception:
            pass

    def _load_catalog_async(self):
        def worker():
            self.catalog.load_catalog()
            GLib.idle_add(self._after_catalog_loaded)
        import threading
        threading.Thread(target=worker, daemon=True).start()
        return False

    def _open_category_from_home(self, label, patterns, default_backend):
        name = str(default_backend)
        if name == "deb":
            page = self.page_deb
        elif name == "appimage":
            page = self.page_appimage
        else:
            page = self.page_flatpak
            name = "flatpak"
        try:
            page.set_filter(label=label, patterns=patterns)
        except Exception:
            pass
        self.stack.set_visible_child_name(name)

    def _open_app_from_home(self, pkg_type, pkg_id, name=""):
        pkg_type = (pkg_type or "").strip().lower()
        if pkg_type == "deb":
            page = self.page_deb
            stack_name = "deb"
        elif pkg_type == "appimage":
            page = self.page_appimage
            stack_name = "appimage"
        else:
            page = self.page_flatpak
            stack_name = "flatpak"
        try:
            pats = []
            if name:
                pats.append(str(name).lower())
            if pkg_id:
                pats.append(str(pkg_id).lower())
            page.set_filter(label=name or pkg_id or tr("Search"), patterns=pats)
        except Exception:
            pass
        self.stack.set_visible_child_name(stack_name)

    def _after_catalog_loaded(self):
        self.page_flatpak.set_apps(self.catalog.all_apps)
        self.page_deb.set_apps(self.catalog.all_apps)
        self.page_appimage.set_apps(self.catalog.all_apps)
        self.show_all()
        return False

    def on_activity_done(self, ok: bool, err: str, app):
        if not ok and err:
            dlg = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=tr("Error"),
            )
            dlg.format_secondary_text(err)
            dlg.run()
            dlg.destroy()
        self.page_flatpak.refresh_after_activity()
        self.page_deb.refresh_after_activity()
        self.page_appimage.refresh_after_activity()
        return False


def check_essora_os():
    os_release_paths = ["/usr/lib/os-release", "/etc/os-release"]
    
    for path in os_release_paths:
        if not os.path.exists(path):
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                 
                    if line.startswith('NAME='):

                        value = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if value == "Essora":
                            return True
        except Exception as e:
            print(f"[OS-CHECK] Error reading {path}: {e}")
            continue
    
    return False


class SingleInstance:
    def __init__(self, window=None):
        self.socket_path = "/tmp/essora-store.lock"
        self.socket = None
        self.window = window
        
    def is_already_running(self):
        try:

            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)
            

            client.send(b"SHOW")
            client.close()
            return True
            
        except (socket.error, FileNotFoundError):

            return False
    
    def create_lock(self):
        try:

            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
            

            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.bind(self.socket_path)
            self.socket.listen(1)
            

            import threading
            thread = threading.Thread(target=self._listen_for_show, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[SINGLE-INSTANCE] Error creating lock: {e}")
            return False
    
    def _listen_for_show(self):
        while True:
            try:
                conn, _ = self.socket.accept()
                data = conn.recv(1024)
                
                if data == b"SHOW" and self.window:

                    GLib.idle_add(self._show_window)
                
                conn.close()
                
            except Exception:
                break
    
    def _show_window(self):
        if not self.window:
            return False
        
        try:
            self.window.present()
            self.window.get_window().focus(Gdk.CURRENT_TIME)
            return False
        except Exception:
            return False
    
    def cleanup(self):
        try:
            if self.socket:
                self.socket.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass


def main():

    single_instance = SingleInstance()
    
    if single_instance.is_already_running():
        print("[ESSORA-STORE] Ya hay una instancia corriendo. Trayendo ventana al frente...")
        return 
    
    if not check_essora_os():

        temp_win = Gtk.Window()
        temp_win.set_default_size(1, 1)
        temp_win.set_decorated(False)
        temp_win.show()
        
        dlg = Gtk.MessageDialog(
            transient_for=temp_win,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Essora Store - System Not Compatible"
        )
        dlg.format_secondary_text(
            "Essora Store can only run on Essora Linux."
        )
        dlg.run()
        dlg.destroy()
        temp_win.destroy()
        return
    

    win = EssoraStoreWindow()
    

    single_instance.window = win
    single_instance.create_lock()
    

    def on_destroy(*args):
        single_instance.cleanup()
        Gtk.main_quit()
    
    win.connect("destroy", on_destroy)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
