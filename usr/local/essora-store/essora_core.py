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
import json
import os
import pty
import re
import select
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from translations import tr
except Exception:
    def tr(t, **kwargs): 
        try:
            return t.format(**kwargs) if kwargs else t
        except:
            return t

BASE_DIR = Path(__file__).resolve().parent

# Data sources
FLATPAK_TXT   = Path("/usr/local/essora-store/flatpak.txt")
DEB_JSON      = Path("/usr/local/essora-store/deb-store.json")
APPIMAGE_JSON = Path("/usr/local/essora-store/appimage-store.json")

# Icons
GENERIC_DEB_ICON = Path("/usr/local/essora-store/icons/app_debian.png")
GENERIC_APPIMAGE_ICON = Path("/usr/local/essora-store/icons/app_appimage.png")
GENERIC_FLATPAK_ICON = Path("/usr/local/essora-store/icons/app_flatpak.png")
ICON_CACHE_JSON = Path("/usr/local/essora-store/icon-cache.json")

# AppImage 
APPIMAGE_ROOT = Path("/opt/appimage")
DESKTOP_DIR   = Path("/usr/share/applications")
APPIMAGE_ARCHIVE_URL = "https://archive.org/download/appimage"

@dataclass
class Application:
    app_id: str
    name: str
    summary: str
    category: str
    pkg_type: str
    icon_path: str = ""
    remote: str = ""
    installed: bool = False
    download_url: str = ""

    installed_version: str = ""
    available_version: str = ""
    update_available: bool = False


def parse_apt_progress(line):
    """Extract progress percentage from apt-get output with APT::Status-Fd"""

    if line.startswith("pmstatus:"):
        parts = line.split(":")
        if len(parts) >= 3:
            try:
                percent = float(parts[2])
                return percent / 100.0
            except (ValueError, IndexError):
                pass
    

    match = re.search(r'\[(\d+)%\]', line)
    if match:
        return int(match.group(1)) / 100.0
    

    match = re.search(r'(\d+)%', line)
    if match:
        return int(match.group(1)) / 100.0
    
    return None


def parse_flatpak_progress(line):
    """Extract flatpak progress"""

    match = re.search(r'(\d+)/(\d+)', line)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        if total > 0:
            return current / total
    

    match = re.search(r'(\d+)%', line)
    if match:
        return int(match.group(1)) / 100.0
    
    return None


class CatalogManager:
    def __init__(self):
        self.all_apps: List[Application] = []

    def load_catalog(self) -> None:
        apps: List[Application] = []
        apps.extend(self._load_from_flatpak_txt())
        apps.extend(self._load_from_deb_json())
        apps.extend(self._load_from_appimage_json())
        seen = set()
        out: List[Application] = []
        for a in apps:
            key = (a.pkg_type, a.app_id)
            if key in seen:
                continue
            seen.add(key)
            out.append(a)
        self.all_apps = out


    def _load_from_flatpak_txt(self) -> List[Application]:
        if not FLATPAK_TXT.exists():
            return []
        out: List[Application] = []
        icon_cache = {}
        try:
            if ICON_CACHE_JSON.exists():
                icon_cache = json.loads(ICON_CACHE_JSON.read_text(encoding="utf-8", errors="replace"))
                if not isinstance(icon_cache, dict):
                    icon_cache = {}
        except Exception:
            icon_cache = {}
        try:
            with open(FLATPAK_TXT, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if len(parts) < 3:
                        continue
                    
                    
                    estado = parts[0].strip()  
                    app_id = parts[1].strip()
                    name = parts[2].strip() or app_id
                    remote = parts[3].strip() if len(parts) >= 4 else "flathub"
                    summary = parts[4].strip() if len(parts) >= 5 else ""
                    inst_ver = parts[5].strip() if len(parts) >= 6 else ""
                    avail_ver = parts[6].strip() if len(parts) >= 7 else ""
                    has_update = (parts[7].strip() == "1") if len(parts) >= 8 else False
                    

                    installed = (estado == "I")
                    
                    out.append(Application(
                        app_id, name, summary, tr("Flatpak"), "flatpak",
                        icon_path=str(icon_cache.get(app_id, "")) if icon_cache.get(app_id, "") else (str(GENERIC_FLATPAK_ICON) if GENERIC_FLATPAK_ICON.exists() else ""),
                        remote=remote,
                        installed=installed,
                        installed_version=inst_ver,
                        available_version=avail_ver,
                        update_available=has_update
                    ))
        except Exception:
            return []
        return out

    def _load_from_deb_json(self) -> List[Application]:
        """Load DEB packages from pre-generated JSON with complete states"""
        if not DEB_JSON.exists():
            return []
        try:
            data = json.loads(DEB_JSON.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        out: List[Application] = []
        for it in data:
            if not isinstance(it, dict):
                continue
            pkg = str(it.get("package") or it.get("name") or it.get("pkg") or "").strip()
            if not pkg:
                continue
            name = str(it.get("title") or it.get("name_pretty") or pkg).strip()
            summary = str(it.get("description") or it.get("summary") or it.get("desc") or "").strip()
            section = str(it.get("section") or it.get("category") or tr("DEB")).strip()
            

            installed = bool(it.get("installed", False))
            inst_ver = str(it.get("installed_version", "")).strip()
            avail_ver = str(it.get("available_version", "")).strip()
            has_update = bool(it.get("update_available", False))
            
            out.append(Application(pkg, name, summary, section, "deb",
                                   icon_path=str(GENERIC_DEB_ICON) if GENERIC_DEB_ICON.exists() else "",
                                   remote="apt",
                                   installed=installed,
                                   installed_version=inst_ver,
                                   available_version=avail_ver,
                                   update_available=has_update))
        

        manually_installed = self._load_manually_installed_debs()
        out.extend(manually_installed)
        
        return out
    
    def _load_manually_installed_debs(self) -> List[Application]:
        """Load manually installed DEB packages from /var/lib/dpkg/status"""
        dpkg_status = Path("/var/lib/dpkg/status")
        if not dpkg_status.exists():
            return []
        
        out: List[Application] = []
        packages_from_json = set()
        
        if DEB_JSON.exists():
            try:
                data = json.loads(DEB_JSON.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, list):
                    packages_from_json = {
                        str(it.get("package", "")).strip() 
                        for it in data 
                        if isinstance(it, dict)
                    }
            except Exception:
                pass
        
        try:
            current_pkg = {}
            
            with open(dpkg_status, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    

                    if not line:
                        if current_pkg.get("Package") and current_pkg.get("Status", "").endswith("installed"):
                            pkg_name = current_pkg["Package"]
                            

                            if pkg_name not in packages_from_json:
                                name = current_pkg.get("Package", pkg_name)
                                version = current_pkg.get("Version", "")
                                description = current_pkg.get("Description", "")
                                section = current_pkg.get("Section", tr("DEB"))
                                
                                out.append(Application(
                                    pkg_name, 
                                    name, 
                                    description, 
                                    section, 
                                    "deb",
                                    icon_path=str(GENERIC_DEB_ICON) if GENERIC_DEB_ICON.exists() else "",
                                    remote="manual",
                                    installed=True,
                                    installed_version=version,
                                    available_version="",
                                    update_available=False
                                ))
                        
                        current_pkg = {}
                        continue
                    

                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key in ("Package", "Status", "Version", "Description", "Section"):
                            current_pkg[key] = value
        
        except Exception as e:
            print(f"[DEB] Error reading dpkg/status: {e}")
        
        print(f"[DEB] Found {len(out)} manually installed packages")
        return out

    def _load_from_appimage_json(self) -> List[Application]:
        if not APPIMAGE_JSON.exists():
            return []
        try:
            data = json.loads(APPIMAGE_JSON.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        out: List[Application] = []
        for it in data:
            if not isinstance(it, dict):
                continue
            app_id = str(it.get("id") or it.get("app_id") or "").strip()
            if not app_id:
                continue
            name = str(it.get("nombre") or it.get("name") or app_id).strip()
            summary = str(it.get("descripcion") or it.get("description") or "").strip()
            category = str(it.get("categoria") or it.get("category") or tr("AppImage")).strip()
            icon_path = str(it.get("icono") or it.get("icon") or "").strip()
            if not icon_path and GENERIC_APPIMAGE_ICON.exists():
                icon_path = str(GENERIC_APPIMAGE_ICON)
            remote = str(it.get("remoto") or it.get("repo") or "appimage").strip()
            download_url = str(it.get("url") or it.get("download_url") or "").strip()
            out.append(Application(app_id, name, summary, category, "appimage", icon_path, remote, False, download_url))
        return out

    def refresh_installed_flags(self, apps: List[Application]) -> None:
        """Check installed status. For DEB it comes from JSON, only check Flatpak and AppImage"""
        flatpak_ids = self._flatpak_installed_ids() if any(a.pkg_type == "flatpak" for a in apps) else set()

        for a in apps:
            if a.pkg_type == "flatpak":
                a.installed = a.app_id in flatpak_ids
            elif a.pkg_type == "deb":

                pass
            elif a.pkg_type == "appimage":
                a.installed = self._appimage_is_installed(a)

    def _flatpak_installed_ids(self) -> Set[str]:
        try:
            p = subprocess.run(["flatpak", "list", "--app", "--columns=application"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, check=False)
            if p.returncode != 0:
                return set()
            return {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}
        except Exception:
            return set()

    def _deb_installed_ids(self) -> Set[str]:
        try:
            p = subprocess.run(["dpkg-query", "-W", "-f=${Package}\n"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, check=False)
            if p.returncode != 0:
                return set()
            return {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}
        except Exception:
            return set()

    def _appimage_target_path(self, app: Application) -> Path:
        return APPIMAGE_ROOT / app.app_id / f"{app.app_id}.AppImage"

    def _appimage_desktop_path(self, app: Application) -> Path:
        return DESKTOP_DIR / f"{app.app_id}.desktop"

    def _appimage_is_installed(self, app: Application) -> bool:
        return self._appimage_target_path(app).exists() and self._appimage_desktop_path(app).exists()
    def get_deb_upgradable(self) -> List[str]:
        """Returns list of upgradable DEB packages.
        
        OPTIMIZED: Read from deb-store.json instead of running apt list.
        This eliminates lag when opening the updates tab.
        """
        try:
            if not DEB_JSON.exists():
                return []
            
            data = json.loads(DEB_JSON.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, list):
                return []
            

            out: List[str] = []
            for it in data:
                if not isinstance(it, dict):
                    continue
                if it.get("update_available"):
                    pkg = str(it.get("package", "")).strip()
                    if pkg:
                        out.append(pkg)
            
            return out
        except Exception:
            return []

    def get_flatpak_upgradable(self) -> Set[str]:
        try:
            p = subprocess.run(["flatpak", "update", "--app", "--assumeno"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, check=False)
            if p.returncode not in (0, 1, 2):
                return set()
            ids = set()
            for ln in p.stdout.splitlines():
                ln = ln.strip()
                if ln.count(".") >= 2 and " " not in ln and "/" not in ln:
                    ids.add(ln)
            return ids
        except Exception:
            return set()


class ActivityManager:
    """
    Executes install/uninstall/update actions with REAL progress tracking
    Uses APT::Status-Fd for DEB, wget parsing for AppImage, and detects Flatpak phases
    """
    def __init__(self, gui_hooks):
        self.gui = gui_hooks

    def _reload_catalog(self, pkg_type: str):
        """Regenerate catalog files by calling the appropriate scripts.
        
        This ensures the GUI shows up-to-date package information after
        installing, updating, or removing packages.
        """
        if pkg_type == "flatpak":
            try:
                subprocess.run(
                    ["/usr/local/essora-store/gen-flatpak-db"],
                    check=False,
                    timeout=60,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[CATALOG] Flatpak catalog regenerated")
            except Exception as e:
                print(f"[CATALOG] Error regenerating Flatpak catalog: {e}")
        
        elif pkg_type == "deb":
            try:
                subprocess.run(
                    ["/usr/local/essora-store/essora-deb-db"],
                    check=False,
                    timeout=60,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[CATALOG] DEB catalog regenerated")
            except Exception as e:
                print(f"[CATALOG] Error regenerating DEB catalog: {e}")
        
        elif pkg_type == "appimage":
            try:
                subprocess.run(
                    ["/usr/local/essora-store/appimage"],
                    check=False,
                    timeout=60,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[CATALOG] AppImage catalog regenerated")
            except Exception as e:
                print(f"[CATALOG] Error regenerating AppImage catalog: {e}")

    def _run_dpkg_configure(self):
        """Ejecuta dpkg --configure -a antes de cualquier operación DEB.
        #agregado por josejp2424
        Evita el error 'dpkg was interrupted' que bloquea apt-get.
        Usa --force-confold para conservar siempre la configuración instalada
        sin mostrar prompts interactivos.
        """
        from gi.repository import GLib
        GLib.idle_add(self.gui.update_progress_text, tr("Checking dpkg state..."))
        try:
            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"
            result = subprocess.run(
                [
                    "dpkg",
                    "--force-confold",
                    "--force-confdef",
                    "--configure", "-a"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
                env=env
            )
            for line in result.stdout.splitlines():
                if line.strip():
                    GLib.idle_add(self.gui.update_progress_text, line.strip())
        except Exception as e:
            GLib.idle_add(self.gui.update_progress_text, f"[dpkg --configure -a] {e}")

    def _run_deb_pty(self, cmd, env, progress_start=0.0, progress_end=1.0):
        """Ejecuta un comando DEB via PTY para soportar debconf interactivo.
        #agregado por josejp2424
        - Conecta el PTY master al diálogo de progreso para que el usuario
          pueda responder preguntas de debconf (grub, etc.) directamente.
        - Devuelve el exit code del proceso.
        """
        from gi.repository import GLib

        master_fd, slave_fd = pty.openpty()

        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=env,
            start_new_session=True
        )
        os.close(slave_fd)

        # Conectar PTY master al diálogo para input interactivo
        GLib.idle_add(self.gui.enable_pty_input, master_fd)

        current_progress = progress_start

        try:
            while True:
                try:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                except (ValueError, OSError):
                    break

                if r:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        text = data.decode("utf-8", errors="replace")
                        for line in text.splitlines():
                            line = line.strip()
                            if line and not line.startswith("pmstatus:"):
                                GLib.idle_add(self.gui.update_progress_text, line)
                            # parse progress
                            prog = parse_apt_progress(line)
                            if prog is not None:
                                scaled = progress_start + prog * (progress_end - progress_start)
                                current_progress = min(scaled, progress_end - 0.01)
                                GLib.idle_add(self.gui.update_progress_bar, current_progress)
                    except OSError:
                        break

                if proc.poll() is not None:
                    # drain remaining output
                    try:
                        while True:
                            r2, _, _ = select.select([master_fd], [], [], 0.05)
                            if not r2:
                                break
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            text = data.decode("utf-8", errors="replace")
                            for line in text.splitlines():
                                line = line.strip()
                                if line and not line.startswith("pmstatus:"):
                                    GLib.idle_add(self.gui.update_progress_text, line)
                    except OSError:
                        pass
                    break
        finally:
            try:
                os.close(master_fd)
            except OSError:
                pass
            GLib.idle_add(self.gui.disable_pty_input)

        proc.wait()
        return proc.returncode

    def _bg(self, fn, app: Optional[Application] = None):
        def worker():
            ok = True
            err = None
            try:
                fn()
            except Exception as e:
                ok = False
                err = str(e)
            try:
                from gi.repository import GLib
                GLib.idle_add(self.gui.on_activity_done, ok, err, app)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def install(self, app: Application):
        if app.pkg_type == "flatpak":
            self._bg(lambda: self._install_flatpak(app), app)
        elif app.pkg_type == "deb":
            self._bg(lambda: self._install_deb(app), app)
        elif app.pkg_type == "appimage":
            self._bg(lambda: self._install_appimage(app), app)

    def uninstall(self, app: Application):
        if app.pkg_type == "flatpak":
            self._bg(lambda: self._uninstall_flatpak(app), app)
        elif app.pkg_type == "deb":
            self._bg(lambda: self._uninstall_deb(app), app)
        elif app.pkg_type == "appimage":
            self._bg(lambda: self._uninstall_appimage(app), app)

    def reinstall(self, app: Application):
        if app.pkg_type == "flatpak":
            self._bg(lambda: self._reinstall_flatpak(app), app)
        elif app.pkg_type == "deb":
            self._bg(lambda: self._reinstall_deb(app), app)
        elif app.pkg_type == "appimage":
            self._bg(lambda: self._reinstall_appimage(app), app)

    def fix_broken(self):
        """Ejecuta dpkg --configure -a y apt-get --fix-broken install.
        #agregado por josejp2424
        Corre en hilo background igual que install/uninstall, usando el
        diálogo de progreso de la app — sin terminal externo.
        """
        self._bg(lambda: self._fix_broken_worker(), None)

    def _fix_broken_worker(self):
        from gi.repository import GLib

        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        GLib.idle_add(self.gui.show_progress_dialog, tr("Fix Broken Packages"), "deb")
        GLib.idle_add(self.gui.update_progress_bar, 0.0)

        # --- Paso 1: dpkg --configure -a ---
        GLib.idle_add(self.gui.update_progress_text, tr("Step 1: dpkg --configure -a ..."))
        p1 = subprocess.Popen(
            [
                "dpkg",
                "-o", "Dpkg::Options::=--force-confold",
                "-o", "Dpkg::Options::=--force-confdef",
                "--configure", "-a"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        for line in iter(p1.stdout.readline, ''):
            if line.strip():
                GLib.idle_add(self.gui.update_progress_text, line.strip())
        p1.wait()

        GLib.idle_add(self.gui.update_progress_bar, 0.45)

        if p1.returncode != 0:
            GLib.idle_add(self.gui.hide_progress_dialog)
            raise Exception(tr("dpkg --configure -a failed (code {code})", code=p1.returncode))

        # --- Paso 2: apt-get --fix-broken install ---
        GLib.idle_add(self.gui.update_progress_text, tr("Step 2: apt-get --fix-broken install ..."))
        p2 = subprocess.Popen(
            [
                "apt-get", "--fix-broken", "install", "-y",
                "-o", "APT::Status-Fd=1",
                "-o", "Dpkg::Options::=--force-confold",
                "-o", "Dpkg::Options::=--force-confdef",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        for line in iter(p2.stdout.readline, ''):
            if not line:
                continue
            line_stripped = line.strip()
            if not line_stripped.startswith("pmstatus:"):
                GLib.idle_add(self.gui.update_progress_text, line_stripped)
            prog = parse_apt_progress(line)
            if prog is not None:
                scaled = 0.45 + prog * 0.5
                GLib.idle_add(self.gui.update_progress_bar, min(scaled, 0.99))
        p2.wait()

        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        GLib.idle_add(self.gui.hide_progress_dialog)

        if p2.returncode != 0:
            raise Exception(tr("apt-get --fix-broken install failed (code {code})", code=p2.returncode))

        self._reload_catalog("deb")

    def update_all(self, pkg_type: str):
        if pkg_type == "flatpak":
            self._bg(lambda: self._update_all_flatpak(), None)
        elif pkg_type == "deb":
            self._bg(lambda: self._update_all_deb(), None)
    
    def _update_all_flatpak(self):
        """Update all Flatpak packages with progress dialog"""
        from gi.repository import GLib
        
        GLib.idle_add(self.gui.show_progress_dialog, tr("Updating all Flatpak packages"), "flatpak")
        
        cmd = ["flatpak", "update", "-y"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                GLib.idle_add(self.gui.update_progress_text, line.strip())
                prog = parse_flatpak_progress(line)
                if prog is not None:
                    GLib.idle_add(self.gui.update_progress_bar, prog)
        
        process.wait()
        GLib.idle_add(self.gui.hide_progress_dialog)
        
        if process.returncode == 0:
            self._reload_catalog("flatpak")
            GLib.idle_add(self.gui.on_activity_done, tr("All Flatpak packages updated"))
        else:
            GLib.idle_add(self.gui.on_activity_done, tr("Error updating Flatpak packages"))
    
    def _update_all_deb(self):
        from gi.repository import GLib

        # #editado por josejp2424 — usa PTY para soportar debconf interactivo
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        GLib.idle_add(self.gui.show_progress_dialog, tr("Updating all DEB packages"), "deb")
        GLib.idle_add(self.gui.update_progress_text, tr("Updating package lists..."))

        # Step 1: apt-get update (sin PTY, no tiene interacción)
        p1 = subprocess.Popen(
            ["apt-get", "update"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env
        )
        for line in iter(p1.stdout.readline, ''):
            if line.strip():
                GLib.idle_add(self.gui.update_progress_text, line.strip())
        p1.wait()

        if p1.returncode != 0:
            GLib.idle_add(self.gui.hide_progress_dialog)
            GLib.idle_add(self.gui.on_activity_done, tr("Error updating package lists"))
            return

        GLib.idle_add(self.gui.update_progress_text, tr("Upgrading packages..."))
        GLib.idle_add(self.gui.update_progress_bar, 0.1)

        # Step 2: apt-get upgrade via PTY — debconf puede mostrar preguntas
        # El usuario puede responder directamente en el diálogo de progreso
        cmd = [
            "apt-get", "upgrade", "-y",
            "-o", "Dpkg::Options::=--force-confold",
            "-o", "Dpkg::Options::=--force-confdef",
        ]
        rc = self._run_deb_pty(cmd, env, progress_start=0.1, progress_end=1.0)

        GLib.idle_add(self.gui.hide_progress_dialog)

        if rc == 0:
            self._reload_catalog("deb")
            GLib.idle_add(self.gui.on_activity_done, tr("All DEB packages updated"))
        else:
            GLib.idle_add(self.gui.on_activity_done, tr("Error upgrading packages"))

    def update_one(self, pkg_type: str, pkg_id: str):
        """Updates a single package (called from UpdateRow)"""
        pkg_type = (pkg_type or "").strip().lower()
        pkg_id = (pkg_id or "").strip()
        if not pkg_id:
            return
        
        if pkg_type == "deb":
            self._bg(lambda: self._upgrade_deb_package(pkg_id), None)
        elif pkg_type == "flatpak":
            self._bg(lambda: self._update_flatpak_single(pkg_id), None)
        elif pkg_type == "appimage":

            pass

    def _update_flatpak_single(self, app_id: str):
        """Updates a single Flatpak"""
        from gi.repository import GLib
        
        cmd = ["flatpak", "update", "-y", app_id]
        GLib.idle_add(self.gui.show_progress_dialog, tr("Updating {app}", app=app_id), "flatpak")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                GLib.idle_add(self.gui.update_progress_text, line.strip())
                progress = parse_flatpak_progress(line)
                if progress:
                    GLib.idle_add(self.gui.update_progress_bar, progress)
        
        process.wait()
        if process.returncode != 0:
            raise Exception(tr("Error updating Flatpak {app}", app=app_id))
        
        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        


        self._reload_catalog("flatpak")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        
        GLib.idle_add(self.gui.hide_progress_dialog)


    def upgrade_deb_package(self, pkg_name: str):
        """Updates a single DEB package (per-package button in 'Update')."""
        pkg_name = (pkg_name or "").strip()
        if not pkg_name:
            return
        self._bg(lambda: self._upgrade_deb_package(pkg_name), None)

    def _upgrade_deb_package(self, pkg_name: str):
        from gi.repository import GLib

        # #editado por josejp2424 — usa PTY para debconf interactivo
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        self._run_dpkg_configure()

        cmd = [
            "apt-get", "install", "--only-upgrade", "-y",
            "-o", "Dpkg::Options::=--force-confold",
            "-o", "Dpkg::Options::=--force-confdef",
            pkg_name
        ]

        GLib.idle_add(self.gui.show_progress_dialog, tr("Updating {pkg}", pkg=pkg_name), "deb")

        rc = self._run_deb_pty(cmd, env, progress_start=0.0, progress_end=0.99)

        self._reload_catalog("deb")

        if rc != 0:
            GLib.idle_add(self.gui.hide_progress_dialog)
            raise Exception(tr("Error updating DEB '{pkg}' (code {code})", pkg=pkg_name, code=rc))

        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        GLib.idle_add(self.gui.hide_progress_dialog)


    def _install_flatpak(self, app: Application):
        from gi.repository import GLib
        remote = app.remote or "flathub"
        cmd = ["flatpak", "install", "-y", remote, app.app_id]
        
        GLib.idle_add(self.gui.show_progress_dialog, tr("Installing {app}", app=app.name), "flatpak")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        current_progress = 0.0
        in_download_phase = True
        
        for line in iter(process.stdout.readline, ''):
            if line:
                line_stripped = line.strip()
                GLib.idle_add(self.gui.update_progress_text, line_stripped)

                if "Installing" in line or "Deploying" in line:
                    in_download_phase = False

                flatpak_progress = parse_flatpak_progress(line)
                if flatpak_progress is not None:
                    if in_download_phase:

                        current_progress = flatpak_progress * 0.7
                    else:

                        current_progress = 0.7 + flatpak_progress * 0.3
                    GLib.idle_add(self.gui.update_progress_bar, current_progress)
                elif "Downloading" in line or "Receiving" in line:
                    current_progress = min(current_progress + 0.01, 0.69)
                    GLib.idle_add(self.gui.update_progress_bar, current_progress)
                elif "Installing" in line or "Deploying" in line:
                    current_progress = min(0.7 + (current_progress - 0.7) + 0.05, 0.99)
                    GLib.idle_add(self.gui.update_progress_bar, current_progress)
        
        process.wait()
        
        if process.returncode != 0:
            raise Exception(tr("Error installing Flatpak (code {code})", code=process.returncode))
        
        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        



        self._reload_catalog("flatpak")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        
        GLib.idle_add(self.gui.hide_progress_dialog)

    def _uninstall_flatpak(self, app: Application):
        from gi.repository import GLib
        cmd = ["flatpak", "uninstall", "-y", app.app_id]
        
        GLib.idle_add(self.gui.show_progress_dialog, tr("Uninstalling {app}", app=app.name), "flatpak")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        progress = 0.0
        for line in iter(process.stdout.readline, ''):
            if line:
                GLib.idle_add(self.gui.update_progress_text, line.strip())
                progress = min(progress + 0.1, 0.99)
                GLib.idle_add(self.gui.update_progress_bar, progress)
        
        process.wait()
        
        if process.returncode != 0:
            raise Exception(tr("Error uninstalling Flatpak (code {code})", code=process.returncode))
        
        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        



        self._reload_catalog("flatpak")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        
        GLib.idle_add(self.gui.hide_progress_dialog)

 
    def _install_deb(self, app: Application):
        from gi.repository import GLib

        # #editado por josejp2424 — usa PTY para debconf interactivo
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        self._run_dpkg_configure()

        cmd = [
            "apt-get", "install", "-y",
            "-o", "Dpkg::Options::=--force-confold",
            "-o", "Dpkg::Options::=--force-confdef",
            app.app_id
        ]

        GLib.idle_add(self.gui.show_progress_dialog, tr("Installing {app}", app=app.name), "deb")

        rc = self._run_deb_pty(cmd, env, progress_start=0.0, progress_end=0.99)

        if rc != 0:
            raise Exception(tr("Error installing DEB (code {code})", code=rc))

        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        self._reload_catalog("deb")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        GLib.idle_add(self.gui.hide_progress_dialog)

    def _uninstall_deb(self, app: Application):
        from gi.repository import GLib

        # #editado por josejp2424 — usa PTY para debconf interactivo
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        self._run_dpkg_configure()

        cmd = [
            "apt-get", "remove", "-y",
            "-o", "Dpkg::Options::=--force-confold",
            "-o", "Dpkg::Options::=--force-confdef",
            app.app_id
        ]

        GLib.idle_add(self.gui.show_progress_dialog, tr("Uninstalling {app}", app=app.name), "deb")

        rc = self._run_deb_pty(cmd, env, progress_start=0.0, progress_end=0.99)

        if rc != 0:
            raise Exception(tr("Error uninstalling DEB (code {code})", code=rc))

        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        self._reload_catalog("deb")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        GLib.idle_add(self.gui.hide_progress_dialog)


    def _install_appimage(self, app: Application):
        from gi.repository import GLib
        
        if app.download_url:
            url = app.download_url
        else:
            url = f"{APPIMAGE_ARCHIVE_URL}/{app.app_id}.AppImage"

        target_dir = APPIMAGE_ROOT / app.app_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{app.app_id}.AppImage"

        GLib.idle_add(self.gui.show_progress_dialog, tr("Downloading {app}", app=app.name), "appimage")
        GLib.idle_add(self.gui.update_progress_text, tr("URL: {url}", url=url))
        GLib.idle_add(self.gui.update_progress_text, tr("Target: {target}", target=target))
        
        process = subprocess.Popen(
            ["wget", "--progress=bar:force", "-O", str(target), url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                GLib.idle_add(self.gui.update_progress_text, line.strip())
                
           
                if '%' in line:
                    try:

                        percent_match = re.search(r'(\d+)%', line)
                        if percent_match:
                            percent = float(percent_match.group(1))
                       
                            progress = min(percent / 100.0 * 0.9, 0.89)
                            GLib.idle_add(self.gui.update_progress_bar, progress)
                    except:
                        pass
        
        process.wait()
        
        if process.returncode != 0:
            raise Exception(tr("Error downloading AppImage"))

        GLib.idle_add(self.gui.update_progress_bar, 0.90)
        GLib.idle_add(self.gui.update_progress_text, tr("Setting permissions..."))
        os.chmod(target, 0o755)
        
        GLib.idle_add(self.gui.update_progress_bar, 0.95)
        GLib.idle_add(self.gui.update_progress_text, tr("Creating .desktop file..."))
        icon = app.icon_path or (str(GENERIC_APPIMAGE_ICON) if GENERIC_APPIMAGE_ICON.exists() else "")
        desktop_path = DESKTOP_DIR / f"{app.app_id}.desktop"
        

        existing_category = getattr(app, 'category', 'Utility')
        if not existing_category or existing_category == tr("AppImage"):
            existing_category = "Utility"
        

        categories = f"{existing_category};AppImage;"
        
        desktop_content = "\n".join([
            "[Desktop Entry]",
            "Type=Application",
            f"Name={app.name}",
            f"Exec={str(target)}",
            f"Icon={icon}",
            "Terminal=false",
            f"Categories={categories}",
        ]) + "\n"
        
        desktop_path.write_text(desktop_content, encoding="utf-8")
        
        GLib.idle_add(self.gui.update_progress_bar, 1.0)


        self._reload_catalog("appimage")
        GLib.idle_add(self.gui.update_progress_text, tr("✓ Installation completed"))
        

        try:
            subprocess.run(["/usr/local/essora-store/appimage"], check=False, timeout=30)
        except Exception:
            pass
        
        GLib.idle_add(self.gui.hide_progress_dialog)

    def _uninstall_appimage(self, app: Application):
        from gi.repository import GLib
        
        GLib.idle_add(self.gui.show_progress_dialog, tr("Uninstalling {app}", app=app.name), "appimage")
        GLib.idle_add(self.gui.update_progress_bar, 0.3)
        
        d = APPIMAGE_ROOT / app.app_id
        if d.exists():
            GLib.idle_add(self.gui.update_progress_text, tr("Removing {dir}...", dir=d))
            shutil.rmtree(d, ignore_errors=True)
        
        GLib.idle_add(self.gui.update_progress_bar, 0.7)
        
        desktop = DESKTOP_DIR / f"{app.app_id}.desktop"
        if desktop.exists():
            GLib.idle_add(self.gui.update_progress_text, tr("Removing {file}...", file=desktop))
            desktop.unlink()
        
        GLib.idle_add(self.gui.update_progress_bar, 1.0)


        self._reload_catalog("appimage")
        GLib.idle_add(self.gui.update_progress_text, tr("✓ Uninstallation completed"))
        

        try:
            subprocess.run(["/usr/local/essora-store/appimage"], check=False, timeout=30)
        except Exception:
            pass
        
        GLib.idle_add(self.gui.hide_progress_dialog)


    def _reinstall_flatpak(self, app: Application):
        from gi.repository import GLib
        remote = app.remote or "flathub"
        cmd = ["flatpak", "install", "--reinstall", "-y", remote, app.app_id]

        GLib.idle_add(self.gui.show_progress_dialog, tr("Reinstalling {app}", app=app.name), "flatpak")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        current_progress = 0.0
        in_download_phase = True

        for line in iter(process.stdout.readline, ''):
            if not line:
                continue
            line_stripped = line.strip()
            GLib.idle_add(self.gui.update_progress_text, line_stripped)


            if "Installing" in line or "Deploying" in line:
                in_download_phase = False

            flatpak_progress = parse_flatpak_progress(line)
            if flatpak_progress is not None:
                if in_download_phase:
                    current_progress = flatpak_progress * 0.7
                else:
                    current_progress = 0.7 + flatpak_progress * 0.3
                GLib.idle_add(self.gui.update_progress_bar, min(current_progress, 0.99))
            elif "Downloading" in line or "Receiving" in line:
                current_progress = min(current_progress + 0.01, 0.69)
                GLib.idle_add(self.gui.update_progress_bar, current_progress)
            elif "Installing" in line or "Deploying" in line:
                current_progress = min(0.7 + (current_progress - 0.7) + 0.05, 0.99)
                GLib.idle_add(self.gui.update_progress_bar, current_progress)

        process.wait()
        if process.returncode != 0:
            raise Exception(tr("Error reinstalling Flatpak (code {code})", code=process.returncode))

        GLib.idle_add(self.gui.update_progress_bar, 1.0)



        self._reload_catalog("flatpak")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass

        GLib.idle_add(self.gui.hide_progress_dialog)

    def _reinstall_deb(self, app: Application):
        from gi.repository import GLib

        # #editado por josejp2424 — usa PTY para debconf interactivo
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"

        self._run_dpkg_configure()

        cmd = [
            "apt-get", "install", "--reinstall", "-y",
            "-o", "Dpkg::Options::=--force-confold",
            "-o", "Dpkg::Options::=--force-confdef",
            app.app_id
        ]

        GLib.idle_add(self.gui.show_progress_dialog, tr("Reinstalling {app}", app=app.name), "deb")

        rc = self._run_deb_pty(cmd, env, progress_start=0.0, progress_end=0.99)

        if rc != 0:
            raise Exception(tr("Error reinstalling DEB (code {code})", code=rc))

        GLib.idle_add(self.gui.update_progress_bar, 1.0)
        self._reload_catalog("deb")
        try:
            subprocess.run(["/usr/local/bin/fixmenu"], check=False, timeout=5)
        except Exception:
            pass
        GLib.idle_add(self.gui.hide_progress_dialog)

    def _reinstall_appimage(self, app: Application):

        self._uninstall_appimage(app)
        self._install_appimage(app)
