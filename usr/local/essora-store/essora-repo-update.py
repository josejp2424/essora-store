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
from gi.repository import Gtk, GLib
import subprocess
import locale
import os
import sys
import socket
import urllib.request
import urllib.error
import threading
import signal
import time

# Translations dictionary
TRANSLATIONS = {
    'en': {
        'title': 'Please wait',
        'message': 'Updating repositories...',
        'message_no_internet': 'No internet connection, launching Essora Store...',
        'message_icons': 'Updating icon cache...'
    },
    'es': {
        'title': 'Aguarde',
        'message': 'Actualizando repositorios...',
        'message_no_internet': 'Sin conexión a internet, iniciando Essora Store...',
        'message_icons': 'Actualizando caché de iconos...'
    },
    'de': {
        'title': 'Bitte warten',
        'message': 'Repositories werden aktualisiert...',
        'message_no_internet': 'Keine Internetverbindung, Essora Store wird gestartet...',
        'message_icons': 'Icon-Cache wird aktualisiert...'
    },
    'ar': {
        'title': 'يرجى الانتظار',
        'message': 'جارٍ تحديث المستودعات...',
        'message_no_internet': 'لا يوجد اتصال بالإنترنت، جارٍ تشغيل Essora Store...',
        'message_icons': 'جارٍ تحديث ذاكرة التخزين المؤقت للأيقونات...'
    },
    'ca': {
        'title': 'Si us plau, espereu',
        'message': 'Actualitzant repositoris...',
        'message_no_internet': 'Sense connexió a Internet, iniciant Essora Store...',
        'message_icons': 'Actualitzant caché d\'icones...'
    },
    'fr': {
        'title': 'Veuillez patienter',
        'message': 'Mise à jour des dépôts...',
        'message_no_internet': 'Pas de connexion Internet, lancement de Essora Store...',
        'message_icons': 'Mise à jour du cache d\'icônes...'
    },
    'it': {
        'title': 'Attendere prego',
        'message': 'Aggiornamento repository...',
        'message_no_internet': 'Nessuna connessione Internet, avvio di Essora Store...',
        'message_icons': 'Aggiornamento cache icone...'
    },
    'pt': {
        'title': 'Aguarde',
        'message': 'Atualizando repositórios...',
        'message_no_internet': 'Sem conexão com a Internet, iniciando Essora Store...',
        'message_icons': 'Atualizando cache de ícones...'
    },
    'ja': {
        'title': 'お待ちください',
        'message': 'リポジトリを更新中...',
        'message_no_internet': 'インターネット接続がありません、Essora Storeを起動します...',
        'message_icons': 'アイコンキャッシュを更新中...'
    },
    'hu': {
        'title': 'Kérem, várjon',
        'message': 'Tárolók frissítése...',
        'message_no_internet': 'Nincs internetkapcsolat, Essora Store indítása...',
        'message_icons': 'Ikon gyorsítótár frissítése...'
    },
    'ru': {
        'title': 'Пожалуйста, подождите',
        'message': 'Обновление репозиториев...',
        'message_no_internet': 'Нет подключения к Интернету, запуск Essora Store...',
        'message_icons': 'Обновление кэша иконок...'
    },
    'zh': {
        'title': '请稍候',
        'message': '正在更新存储库...',
        'message_no_internet': '无互联网连接，正在启动Essora Store...',
        'message_icons': '正在更新图标缓存...'
    }
}

def check_internet_connection(timeout=3):
    """
    Check if there is an active internet connection
    Returns: True if internet is available, False otherwise
    """
    try:
        host = "8.8.8.8"
        port = 53
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        pass
    
    try:
        urllib.request.urlopen('http://www.google.com', timeout=timeout)
        return True
    except urllib.error.URLError:
        pass
    
    return False

def get_system_language():
    """Get system language code"""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang:
            lang_code = lang.split('_')[0].lower()

            if lang_code in TRANSLATIONS:
                return lang_code

            if lang.startswith('zh'):
                return 'zh'
    except:
        pass
    return 'en'  

class RepoUpdaterWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        
        self.lang = get_system_language()
        self.texts = TRANSLATIONS[self.lang]
        self.has_internet = check_internet_connection()
        self.store_process = None
        self.processes = []
        
        self.set_title(self.texts['title'])
        self.set_decorated(False)  
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(400, 180)
        self.set_resizable(False)
        self.set_keep_above(True)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        vbox.set_margin_top(30)
        vbox.set_margin_bottom(30)
        vbox.set_margin_start(30)
        vbox.set_margin_end(30)
        
        self.label = Gtk.Label()
        
        if self.has_internet:
            self.label.set_markup(f"<span size='14000' weight='bold'>{self.texts['message']}</span>")
        else:
            self.label.set_markup(f"<span size='14000' weight='bold'>{self.texts['message_no_internet']}</span>")
        
        self.label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(self.label, True, True, 0)
        
        self.icon_label = Gtk.Label()
        self.icon_label.set_markup(f"<span size='12000'>{self.texts['message_icons']}</span>")
        self.icon_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(self.icon_label, False, False, 0)
        
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.start()
        vbox.pack_start(self.spinner, False, False, 0)
        
        self.add(vbox)
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.connect('destroy', self.on_destroy)
        
        GLib.timeout_add(500, self.start_process)
    
    def signal_handler(self, sig, frame):
        """Manejar señales del sistema"""
        print(f"Received signal {sig}, cleaning up...")
        GLib.idle_add(self.cleanup_and_exit)
    
    def on_destroy(self, widget):
        """Manejador cuando se destruye la ventana"""
        self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Limpiar procesos y salir"""
        for proc in self.processes:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except:
                    pass
        
        if self.store_process and self.store_process.poll() is None:
            os.setpgrp()  
        
        Gtk.main_quit()
        return False
    
    def start_process(self):
        """Start the appropriate process based on internet availability"""
        GLib.idle_add(self.run_appropriate_commands)
        return False
    
    def run_icon_script(self):
        """Execute the icons script"""
        try:
            GLib.idle_add(self.update_icon_message, True)
            
            result = subprocess.run(
                ['/usr/local/essora-store/icons.sh'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                print("Icon cache updated successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"Error updating icon cache: {result.stderr}")
                
        except Exception as e:
            print(f"Error during icon script: {e}", file=sys.stderr)
        finally:
            GLib.idle_add(self.update_icon_message, False)
    
    def update_icon_message(self, is_running):
        """Update the icon message in the UI"""
        if is_running:
            self.icon_label.set_markup(f"<span size='12000' foreground='blue'>{self.texts['message_icons']}</span>")
        else:
            self.icon_label.set_markup(f"<span size='12000' foreground='green'>✓ {self.texts['message_icons']}</span>")
        return False
    
    def run_appropriate_commands(self):
        """Execute commands based on internet connection"""
        if self.has_internet:
            t = threading.Thread(target=self._run_updates_thread, daemon=True)
            t.start()
        else:
            GLib.timeout_add(500, self.launch_essora_store)
        return False

    def _run_updates_thread(self):
        """Corre los 3 scripts + icons en background sin congelar la GUI"""
        try:
            self.processes = []

            proc1 = subprocess.Popen(['/usr/local/essora-store/appimage'],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
            self.processes.append(proc1)

            proc2 = subprocess.Popen(['/usr/local/essora-store/essora-deb-db'],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
            self.processes.append(proc2)

            proc3 = subprocess.Popen(['/usr/local/essora-store/gen-flatpak-db'],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
            self.processes.append(proc3)

            icon_thread = threading.Thread(target=self.run_icon_script, daemon=True)
            icon_thread.start()

            timeouts = [180, 60, 60]
            for proc, timeout in zip(self.processes, timeouts):
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    print(f"Process {proc.pid} timed out, killing")
                    proc.kill()

            icon_thread.join(timeout=10)

        except Exception as e:
            print(f"Error during updates: {e}", file=sys.stderr)

        GLib.idle_add(lambda: GLib.timeout_add(500, self.launch_essora_store))
    
    def launch_essora_store(self):
        """Launch Essora Store and close this window"""
        try:
            self.store_process = subprocess.Popen(
                ['/usr/local/essora-store/essora-store.py'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  
                close_fds=True,  
                env=os.environ.copy() 
            )
            
            print(f"Essora Store launched with PID: {self.store_process.pid}")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error launching Essora Store: {e}", file=sys.stderr)
        
        self.destroy()
        return False

def main():
    window = RepoUpdaterWindow()
    window.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
