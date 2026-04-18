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


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import os

try:
    from translations import tr
except Exception:
    def tr(t, **kwargs):
        try:
            return t.format(**kwargs) if kwargs else t
        except Exception:
            return t


class EssoraAboutDialog:
    def __init__(self):
        self.version = "3.7-1"
        self.author = "josejp2424"
        self.license_type = "GPL-3.0-or-later"
        self.icon_path = "/usr/local/essora-store/essora-store.png"

        self.create_dialog()

    def create_dialog(self):
        """Create the About dialog"""
        self.dialog = Gtk.Dialog(
            title=tr("About Essora Store"),
            modal=True
        )
        self.dialog.set_default_size(500, 580)
        self.dialog.set_border_width(0)
        

        self.dialog.set_position(Gtk.WindowPosition.CENTER)
        
       
        if os.path.exists(self.icon_path):
            try:
                self.dialog.set_icon_from_file(self.icon_path)
            except Exception as e:
                print(f"Could not set dialog icon: {e}")

        content_area = self.dialog.get_content_area()

        self.create_content(content_area)

        self.dialog.add_button(tr("Close"), Gtk.ResponseType.CLOSE)

    def create_content(self, parent):
        """Create dialog content"""

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        parent.pack_start(scrolled, True, True, 0)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scrolled.add(main_box)

        banner_path = "/usr/local/essora-store/essora-store.png"
        if os.path.exists(banner_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(banner_path, 120, 120)
                banner_image = Gtk.Image.new_from_pixbuf(pixbuf)
                banner_image.set_halign(Gtk.Align.CENTER)
                banner_image.set_margin_top(10)
                main_box.pack_start(banner_image, False, False, 0)
            except Exception as e:
                print(f"Could not load banner: {e}")
                self.create_fallback_header(main_box)
        else:
            self.create_fallback_header(main_box)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(30)
        content_box.set_margin_end(30)
        main_box.pack_start(content_box, True, True, 0)

        detail_label = Gtk.Label(
            label=tr(
                "Essora Store is a comprehensive package manager that handles Flatpak, DEB, and AppImage packages, providing a unified interface for installing, updating, and managing applications on Essora Linux."
            )
        )
        detail_label.set_line_wrap(True)
        detail_label.set_xalign(0)
        detail_label.set_justify(Gtk.Justification.LEFT)
        content_box.pack_start(detail_label, False, False, 0)

        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(separator1, False, False, 5)

        info_grid = Gtk.Grid()
        info_grid.set_column_spacing(15)
        info_grid.set_row_spacing(10)
        content_box.pack_start(info_grid, False, False, 0)

        version_label = Gtk.Label()
        version_label.set_markup(f"<b>{tr('Version')}:</b>")
        version_label.set_xalign(0)
        info_grid.attach(version_label, 0, 0, 1, 1)

        version_value = Gtk.Label(label=self.version)
        version_value.set_xalign(0)
        info_grid.attach(version_value, 1, 0, 1, 1)

        author_label = Gtk.Label()
        author_label.set_markup(f"<b>{tr('Author')}:</b>")
        author_label.set_xalign(0)
        info_grid.attach(author_label, 0, 1, 1, 1)

        author_value = Gtk.Label(label=self.author)
        author_value.set_xalign(0)
        info_grid.attach(author_value, 1, 1, 1, 1)

        license_label = Gtk.Label()
        license_label.set_markup(f"<b>{tr('License')}:</b>")
        license_label.set_xalign(0)
        info_grid.attach(license_label, 0, 2, 1, 1)

        license_value = Gtk.Label(label=self.license_type)
        license_value.set_xalign(0)
        info_grid.attach(license_value, 1, 2, 1, 1)

        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(separator2, False, False, 5)

        features_label = Gtk.Label()
        features_label.set_markup(f"<b>{tr('Features')}</b>")
        features_label.set_xalign(0)
        content_box.pack_start(features_label, False, False, 5)

        features_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        features_box.set_margin_start(10)
        content_box.pack_start(features_box, False, False, 0)

        features = [
            tr("• Flatpak package support"),
            tr("• DEB package management"),
            tr("• AppImage integration"),
            tr("• Unified interface for all package types"),
            tr("• Easy to use and intuitive"),
        ]

        for feature in features:
            feature_label = Gtk.Label(label=feature)
            feature_label.set_xalign(0)
            features_box.pack_start(feature_label, False, False, 0)

        separator3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(separator3, False, False, 10)

        copyright_label = Gtk.Label()
        copyright_label.set_markup(f"<small>{tr('Essora Team')}</small>")
        copyright_label.set_halign(Gtk.Align.CENTER)
        content_box.pack_start(copyright_label, False, False, 0)

    def create_fallback_header(self, parent):
        """Create basic header if no banner"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(20)
        header_box.set_margin_bottom(20)

        if os.path.exists(self.icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(self.icon_path, 120, 120)
                icon_image = Gtk.Image.new_from_pixbuf(pixbuf)
                icon_image.set_halign(Gtk.Align.CENTER)
                header_box.pack_start(icon_image, False, False, 0)
            except Exception as e:
                print(f"Could not load icon: {e}")

        app_name_label = Gtk.Label()
        app_name_label.set_markup(f"<span size='xx-large' weight='bold'>{tr('Essora Store')}</span>")
        app_name_label.set_halign(Gtk.Align.CENTER)
        header_box.pack_start(app_name_label, False, False, 0)

        parent.pack_start(header_box, False, False, 0)

    def show(self):
        """Show the dialog"""
        self.dialog.show_all()
        self.dialog.run()
        self.dialog.destroy()


def show_about_dialog():
    """Helper function to show the About dialog"""
    about = EssoraAboutDialog()
    about.show()


if __name__ == "__main__":
    about = EssoraAboutDialog()
    about.show()
