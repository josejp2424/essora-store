#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Essora Fix Broken Packages
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import os
import sys
import subprocess
import threading
import locale

# i18n — detectar idioma del sistema 
def _detect_lang():
    for var in ("LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES"):
        val = os.environ.get(var, "")
        if val:
            code = val.split("_")[0].split(".")[0].lower()
            if code in ("ar","de","ca","es","fr","it","pt","ja","hu","ru","zh"):
                return code
            break
    try:
        loc = locale.getdefaultlocale()[0] or ""
        code = loc.split("_")[0].lower()
        if code in ("ar","de","ca","es","fr","it","pt","ja","hu","ru","zh"):
            return code
    except Exception:
        pass
    return "en"

TRANSLATIONS = {
    "en": {
        "title":            "Fix Broken Packages",
        "subtitle":         "Essora Store — dpkg & apt repair tool",
        "opt_update":       "apt update before fix",
        "opt_autoremove":   "autoremove after fix",
        "options_label":    "Options:",
        "btn_run":          "▶  Run Repair",
        "btn_clear":        "Clear",
        "btn_close":        "Close",
        "status_ready":     "Ready.",
        "status_running":   "Running...",
        "status_ok":        "✓ Repair completed successfully.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal cleared.",
        "log_header":       "Essora — Fix Broken Packages",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Step 1: dpkg --configure -a",
        "log_step2":        ">>> Step 2: apt-get --fix-broken install",
        "log_step3":        ">>> Step 3: apt-get autoremove",
        "log_exit":         "    exit code: {rc}",
        "log_done":         "  Done. All steps completed successfully.",
        "log_err_dpkg":     "[ERROR] dpkg --configure -a failed (exit {rc}). Aborting.",
        "log_err_apt":      "[ERROR] apt-get --fix-broken install failed (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a failed (exit {rc})",
        "err_apt":          "apt-get --fix-broken failed (exit {rc})",
    },
    "es": {
        "title":            "Reparar Paquetes Rotos",
        "subtitle":         "Essora Store — herramienta de reparación dpkg & apt",
        "opt_update":       "apt update antes de reparar",
        "opt_autoremove":   "autoremove después de reparar",
        "options_label":    "Opciones:",
        "btn_run":          "▶  Iniciar Reparación",
        "btn_clear":        "Limpiar",
        "btn_close":        "Cerrar",
        "status_ready":     "Listo.",
        "status_running":   "Ejecutando...",
        "status_ok":        "✓ Reparación completada correctamente.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal limpiada.",
        "log_header":       "Essora — Reparar Paquetes Rotos",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Paso 1: dpkg --configure -a",
        "log_step2":        ">>> Paso 2: apt-get --fix-broken install",
        "log_step3":        ">>> Paso 3: apt-get autoremove",
        "log_exit":         "    código de salida: {rc}",
        "log_done":         "  Listo. Todos los pasos completados.",
        "log_err_dpkg":     "[ERROR] dpkg --configure -a falló (exit {rc}). Abortando.",
        "log_err_apt":      "[ERROR] apt-get --fix-broken install falló (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a falló (exit {rc})",
        "err_apt":          "apt-get --fix-broken falló (exit {rc})",
    },
    "ar": {
        "title":            "إصلاح الحزم المعطوبة",
        "subtitle":         "Essora Store — أداة إصلاح dpkg و apt",
        "opt_update":       "تحديث apt قبل الإصلاح",
        "opt_autoremove":   "autoremove بعد الإصلاح",
        "options_label":    "خيارات:",
        "btn_run":          "▶  تشغيل الإصلاح",
        "btn_clear":        "مسح",
        "btn_close":        "إغلاق",
        "status_ready":     "جاهز.",
        "status_running":   "جارٍ التنفيذ...",
        "status_ok":        "✓ اكتمل الإصلاح بنجاح.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "تم مسح الطرفية.",
        "log_header":       "Essora — إصلاح الحزم المعطوبة",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> الخطوة 1: dpkg --configure -a",
        "log_step2":        ">>> الخطوة 2: apt-get --fix-broken install",
        "log_step3":        ">>> الخطوة 3: apt-get autoremove",
        "log_exit":         "    كود الخروج: {rc}",
        "log_done":         "  تم. اكتملت جميع الخطوات بنجاح.",
        "log_err_dpkg":     "[خطأ] فشل dpkg --configure -a (exit {rc}). جارٍ الإلغاء.",
        "log_err_apt":      "[خطأ] فشل apt-get --fix-broken install (exit {rc}).",
        "err_dpkg":         "فشل dpkg --configure -a (exit {rc})",
        "err_apt":          "فشل apt-get --fix-broken (exit {rc})",
    },
    "de": {
        "title":            "Beschädigte Pakete reparieren",
        "subtitle":         "Essora Store — dpkg & apt Reparaturwerkzeug",
        "opt_update":       "apt update vor der Reparatur",
        "opt_autoremove":   "autoremove nach der Reparatur",
        "options_label":    "Optionen:",
        "btn_run":          "▶  Reparatur starten",
        "btn_clear":        "Leeren",
        "btn_close":        "Schließen",
        "status_ready":     "Bereit.",
        "status_running":   "Wird ausgeführt...",
        "status_ok":        "✓ Reparatur erfolgreich abgeschlossen.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal geleert.",
        "log_header":       "Essora — Beschädigte Pakete reparieren",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Schritt 1: dpkg --configure -a",
        "log_step2":        ">>> Schritt 2: apt-get --fix-broken install",
        "log_step3":        ">>> Schritt 3: apt-get autoremove",
        "log_exit":         "    Rückgabecode: {rc}",
        "log_done":         "  Fertig. Alle Schritte erfolgreich abgeschlossen.",
        "log_err_dpkg":     "[FEHLER] dpkg --configure -a fehlgeschlagen (exit {rc}). Abbruch.",
        "log_err_apt":      "[FEHLER] apt-get --fix-broken install fehlgeschlagen (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a fehlgeschlagen (exit {rc})",
        "err_apt":          "apt-get --fix-broken fehlgeschlagen (exit {rc})",
    },
    "ca": {
        "title":            "Reparar Paquets Trencats",
        "subtitle":         "Essora Store — eina de reparació dpkg & apt",
        "opt_update":       "apt update abans de reparar",
        "opt_autoremove":   "autoremove després de reparar",
        "options_label":    "Opcions:",
        "btn_run":          "▶  Iniciar Reparació",
        "btn_clear":        "Netejar",
        "btn_close":        "Tancar",
        "status_ready":     "Llest.",
        "status_running":   "Executant...",
        "status_ok":        "✓ Reparació completada correctament.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal netejada.",
        "log_header":       "Essora — Reparar Paquets Trencats",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Pas 1: dpkg --configure -a",
        "log_step2":        ">>> Pas 2: apt-get --fix-broken install",
        "log_step3":        ">>> Pas 3: apt-get autoremove",
        "log_exit":         "    codi de sortida: {rc}",
        "log_done":         "  Fet. Tots els passos completats.",
        "log_err_dpkg":     "[ERROR] dpkg --configure -a ha fallat (exit {rc}). Avortant.",
        "log_err_apt":      "[ERROR] apt-get --fix-broken install ha fallat (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a ha fallat (exit {rc})",
        "err_apt":          "apt-get --fix-broken ha fallat (exit {rc})",
    },
    "fr": {
        "title":            "Réparer les Paquets Cassés",
        "subtitle":         "Essora Store — outil de réparation dpkg & apt",
        "opt_update":       "apt update avant la réparation",
        "opt_autoremove":   "autoremove après la réparation",
        "options_label":    "Options :",
        "btn_run":          "▶  Lancer la Réparation",
        "btn_clear":        "Effacer",
        "btn_close":        "Fermer",
        "status_ready":     "Prêt.",
        "status_running":   "En cours...",
        "status_ok":        "✓ Réparation terminée avec succès.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal effacé.",
        "log_header":       "Essora — Réparer les Paquets Cassés",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Étape 1 : dpkg --configure -a",
        "log_step2":        ">>> Étape 2 : apt-get --fix-broken install",
        "log_step3":        ">>> Étape 3 : apt-get autoremove",
        "log_exit":         "    code de sortie : {rc}",
        "log_done":         "  Terminé. Toutes les étapes complétées.",
        "log_err_dpkg":     "[ERREUR] dpkg --configure -a a échoué (exit {rc}). Abandon.",
        "log_err_apt":      "[ERREUR] apt-get --fix-broken install a échoué (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a a échoué (exit {rc})",
        "err_apt":          "apt-get --fix-broken a échoué (exit {rc})",
    },
    "it": {
        "title":            "Ripara Pacchetti Danneggiati",
        "subtitle":         "Essora Store — strumento di riparazione dpkg & apt",
        "opt_update":       "apt update prima della riparazione",
        "opt_autoremove":   "autoremove dopo la riparazione",
        "options_label":    "Opzioni:",
        "btn_run":          "▶  Avvia Riparazione",
        "btn_clear":        "Pulisci",
        "btn_close":        "Chiudi",
        "status_ready":     "Pronto.",
        "status_running":   "In esecuzione...",
        "status_ok":        "✓ Riparazione completata con successo.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminale pulito.",
        "log_header":       "Essora — Ripara Pacchetti Danneggiati",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Passo 1: dpkg --configure -a",
        "log_step2":        ">>> Passo 2: apt-get --fix-broken install",
        "log_step3":        ">>> Passo 3: apt-get autoremove",
        "log_exit":         "    codice di uscita: {rc}",
        "log_done":         "  Fatto. Tutti i passi completati.",
        "log_err_dpkg":     "[ERRORE] dpkg --configure -a fallito (exit {rc}). Interruzione.",
        "log_err_apt":      "[ERRORE] apt-get --fix-broken install fallito (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a fallito (exit {rc})",
        "err_apt":          "apt-get --fix-broken fallito (exit {rc})",
    },
    "pt": {
        "title":            "Reparar Pacotes Quebrados",
        "subtitle":         "Essora Store — ferramenta de reparação dpkg & apt",
        "opt_update":       "apt update antes de reparar",
        "opt_autoremove":   "autoremove após reparar",
        "options_label":    "Opções:",
        "btn_run":          "▶  Iniciar Reparação",
        "btn_clear":        "Limpar",
        "btn_close":        "Fechar",
        "status_ready":     "Pronto.",
        "status_running":   "Executando...",
        "status_ok":        "✓ Reparação concluída com sucesso.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminal limpo.",
        "log_header":       "Essora — Reparar Pacotes Quebrados",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Passo 1: dpkg --configure -a",
        "log_step2":        ">>> Passo 2: apt-get --fix-broken install",
        "log_step3":        ">>> Passo 3: apt-get autoremove",
        "log_exit":         "    código de saída: {rc}",
        "log_done":         "  Concluído. Todos os passos completados.",
        "log_err_dpkg":     "[ERRO] dpkg --configure -a falhou (exit {rc}). A abortar.",
        "log_err_apt":      "[ERRO] apt-get --fix-broken install falhou (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a falhou (exit {rc})",
        "err_apt":          "apt-get --fix-broken falhou (exit {rc})",
    },
    "ja": {
        "title":            "壊れたパッケージを修復",
        "subtitle":         "Essora Store — dpkg & apt 修復ツール",
        "opt_update":       "修復前に apt update",
        "opt_autoremove":   "修復後に autoremove",
        "options_label":    "オプション:",
        "btn_run":          "▶  修復を実行",
        "btn_clear":        "クリア",
        "btn_close":        "閉じる",
        "status_ready":     "準備完了。",
        "status_running":   "実行中...",
        "status_ok":        "✓ 修復が正常に完了しました。",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "ターミナルをクリアしました。",
        "log_header":       "Essora — 壊れたパッケージを修復",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> ステップ1: dpkg --configure -a",
        "log_step2":        ">>> ステップ2: apt-get --fix-broken install",
        "log_step3":        ">>> ステップ3: apt-get autoremove",
        "log_exit":         "    終了コード: {rc}",
        "log_done":         "  完了。すべてのステップが正常に完了しました。",
        "log_err_dpkg":     "[エラー] dpkg --configure -a 失敗 (exit {rc})。中断します。",
        "log_err_apt":      "[エラー] apt-get --fix-broken install 失敗 (exit {rc})。",
        "err_dpkg":         "dpkg --configure -a 失敗 (exit {rc})",
        "err_apt":          "apt-get --fix-broken 失敗 (exit {rc})",
    },
    "hu": {
        "title":            "Törött Csomagok Javítása",
        "subtitle":         "Essora Store — dpkg & apt javítóeszköz",
        "opt_update":       "apt update javítás előtt",
        "opt_autoremove":   "autoremove javítás után",
        "options_label":    "Beállítások:",
        "btn_run":          "▶  Javítás indítása",
        "btn_clear":        "Törlés",
        "btn_close":        "Bezárás",
        "status_ready":     "Kész.",
        "status_running":   "Futás...",
        "status_ok":        "✓ Javítás sikeresen befejezve.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Terminál törölve.",
        "log_header":       "Essora — Törött Csomagok Javítása",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> 1. lépés: dpkg --configure -a",
        "log_step2":        ">>> 2. lépés: apt-get --fix-broken install",
        "log_step3":        ">>> 3. lépés: apt-get autoremove",
        "log_exit":         "    kilépési kód: {rc}",
        "log_done":         "  Kész. Minden lépés sikeresen befejezve.",
        "log_err_dpkg":     "[HIBA] dpkg --configure -a sikertelen (exit {rc}). Megszakítás.",
        "log_err_apt":      "[HIBA] apt-get --fix-broken install sikertelen (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a sikertelen (exit {rc})",
        "err_apt":          "apt-get --fix-broken sikertelen (exit {rc})",
    },
    "ru": {
        "title":            "Исправление сломанных пакетов",
        "subtitle":         "Essora Store — инструмент восстановления dpkg & apt",
        "opt_update":       "apt update перед исправлением",
        "opt_autoremove":   "autoremove после исправления",
        "options_label":    "Параметры:",
        "btn_run":          "▶  Запустить исправление",
        "btn_clear":        "Очистить",
        "btn_close":        "Закрыть",
        "status_ready":     "Готово.",
        "status_running":   "Выполняется...",
        "status_ok":        "✓ Исправление успешно завершено.",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "Терминал очищен.",
        "log_header":       "Essora — Исправление сломанных пакетов",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> Шаг 1: dpkg --configure -a",
        "log_step2":        ">>> Шаг 2: apt-get --fix-broken install",
        "log_step3":        ">>> Шаг 3: apt-get autoremove",
        "log_exit":         "    код выхода: {rc}",
        "log_done":         "  Готово. Все шаги выполнены успешно.",
        "log_err_dpkg":     "[ОШИБКА] dpkg --configure -a завершился с ошибкой (exit {rc}). Прерывание.",
        "log_err_apt":      "[ОШИБКА] apt-get --fix-broken install завершился с ошибкой (exit {rc}).",
        "err_dpkg":         "dpkg --configure -a завершился с ошибкой (exit {rc})",
        "err_apt":          "apt-get --fix-broken завершился с ошибкой (exit {rc})",
    },
    "zh": {
        "title":            "修复损坏的软件包",
        "subtitle":         "Essora Store — dpkg & apt 修复工具",
        "opt_update":       "修复前运行 apt update",
        "opt_autoremove":   "修复后运行 autoremove",
        "options_label":    "选项：",
        "btn_run":          "▶  开始修复",
        "btn_clear":        "清空",
        "btn_close":        "关闭",
        "status_ready":     "就绪。",
        "status_running":   "正在运行...",
        "status_ok":        "✓ 修复成功完成。",
        "status_fail":      "✗ {msg}",
        "terminal_cleared": "终端已清空。",
        "log_header":       "Essora — 修复损坏的软件包",
        "log_sep":          "========================================",
        "log_update":       ">>> apt-get update",
        "log_step1":        ">>> 步骤1: dpkg --configure -a",
        "log_step2":        ">>> 步骤2: apt-get --fix-broken install",
        "log_step3":        ">>> 步骤3: apt-get autoremove",
        "log_exit":         "    退出代码: {rc}",
        "log_done":         "  完成。所有步骤已成功完成。",
        "log_err_dpkg":     "[错误] dpkg --configure -a 失败 (exit {rc})。正在中止。",
        "log_err_apt":      "[错误] apt-get --fix-broken install 失败 (exit {rc})。",
        "err_dpkg":         "dpkg --configure -a 失败 (exit {rc})",
        "err_apt":          "apt-get --fix-broken 失败 (exit {rc})",
    },
}

_LANG = _detect_lang()

def tr(key, **kwargs):
    lang = TRANSLATIONS.get(_LANG, TRANSLATIONS["en"])
    text = lang.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text

MOCHA = {
    "base":    "#1e1e2e",
    "mantle":  "#181825",
    "crust":   "#11111b",
    "surface0":"#313244",
    "surface1":"#45475a",
    "overlay0":"#6c7086",
    "text":    "#cdd6f4",
    "subtext0":"#a6adc8",
    "green":   "#a6e3a1",
    "red":     "#f38ba8",
    "teal":    "#94e2d5",
}

CSS = """
* { font-family: "Noto Sans", "DejaVu Sans", sans-serif; }
window { background-color: #1e1e2e; }
#header {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 0px 16px;
    min-height: 48px;
}
#header-title   { color: #cdd6f4; font-size: 15px; font-weight: bold; }
#header-subtitle{ color: #a6adc8; font-size: 11px; }
#close-btn {
    background: transparent; border: none;
    color: #a6adc8; font-size: 16px;
    padding: 4px 10px; border-radius: 4px;
    min-width: 0; min-height: 0;
}
#close-btn:hover { background-color: #f38ba8; color: #1e1e2e; }
#options-box {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 6px 16px;
}
checkbutton label         { color: #a6adc8; font-size: 12px; }
checkbutton:checked label { color: #cdd6f4; }
#btn-run {
    background-color: #a6e3a1; color: #1e1e2e;
    font-weight: bold; font-size: 13px;
    border: none; border-radius: 6px;
    padding: 8px 24px; min-height: 36px;
}
#btn-run:hover    { background-color: #94e2d5; }
#btn-run:disabled { background-color: #45475a; color: #6c7086; }
#btn-clear, #btn-close {
    background-color: #313244; color: #cdd6f4;
    font-size: 12px; border: none; border-radius: 6px;
    padding: 8px 16px; min-height: 36px;
}
#btn-clear:hover { background-color: #45475a; }
#btn-close:hover { background-color: #f38ba8; color: #1e1e2e; }
#btn-bar    { background-color: #1e1e2e; padding: 10px 16px; }
progressbar trough  { background-color: #313244; border-radius: 4px; min-height: 6px; }
progressbar progress{ background-color: #a6e3a1; border-radius: 4px; min-height: 6px; }
#status-bar { background-color: #181825; border-top: 1px solid #313244; padding: 4px 12px; min-height: 26px; }
#status-label { color: #a6adc8; font-size: 11px; }
"""


class EssoraFixBroken:
    def __init__(self):
        self._running = False
        self._pulse_tag = None
        self._setup_css()
        self._build_window()

    def _setup_css(self):
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_window(self):
        self.win = Gtk.Window()
        self.win.set_default_size(760, 520)
        self.win.set_position(Gtk.WindowPosition.CENTER)
        self.win.set_decorated(False)
        self.win.connect("destroy", Gtk.main_quit)
        self.win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.win.connect("button-press-event", self._on_drag)
        icon_path = "/usr/local/essora-store/essora-store.svg"
        if os.path.exists(icon_path):
            self.win.set_icon_from_file(icon_path)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.add(root)
        root.pack_start(self._build_header(),   False, False, 0)
        root.pack_start(self._build_options(),  False, False, 0)
        root.pack_start(self._build_output(),   True,  True,  0)
        root.pack_start(self._build_progress(), False, False, 0)
        root.pack_start(self._build_buttons(),  False, False, 0)
        root.pack_start(self._build_status(),   False, False, 0)
        self.win.show_all()

    def _build_header(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_name("header")

        # icono en el header
        icon_path = "/usr/local/essora-store/essora-store.svg"
        if os.path.exists(icon_path):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 28, 28)
                img = Gtk.Image.new_from_pixbuf(pb)
                img.set_valign(Gtk.Align.CENTER)
                box.pack_start(img, False, False, 0)
            except Exception:
                pass

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left.set_valign(Gtk.Align.CENTER)

        t = Gtk.Label(label=tr("title"))
        t.set_name("header-title")
        t.set_halign(Gtk.Align.START)

        s = Gtk.Label(label=tr("subtitle"))
        s.set_name("header-subtitle")
        s.set_halign(Gtk.Align.START)

        left.pack_start(t, False, False, 0)
        left.pack_start(s, False, False, 0)
        box.pack_start(left, True, True, 0)

        btn = Gtk.Button(label="✕")
        btn.set_name("close-btn")
        btn.set_valign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda *_: Gtk.main_quit())
        box.pack_end(btn, False, False, 0)
        return box

    def _build_options(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        box.set_name("options-box")
        lbl = Gtk.Label(label=tr("options_label"))
        lbl.set_name("header-subtitle")
        box.pack_start(lbl, False, False, 0)
        self.chk_update = Gtk.CheckButton(label=tr("opt_update"))
        self.chk_update.set_active(False)
        box.pack_start(self.chk_update, False, False, 0)
        self.chk_autoremove = Gtk.CheckButton(label=tr("opt_autoremove"))
        self.chk_autoremove.set_active(False)
        box.pack_start(self.chk_autoremove, False, False, 0)
        return box

    def _build_output(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_margin_top(8)
        scroll.set_margin_bottom(0)
        scroll.set_margin_start(12)
        scroll.set_margin_end(12)
        self.textbuf = Gtk.TextBuffer()
        self.textview = Gtk.TextView(buffer=self.textbuf)
        self.textview.set_name("output-view")
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        bg = Gdk.RGBA(); bg.parse("#11111b")
        fg = Gdk.RGBA(); fg.parse("#cdd6f4")
        self.textview.override_background_color(Gtk.StateFlags.NORMAL, bg)
        self.textview.override_color(Gtk.StateFlags.NORMAL, fg)
        from gi.repository import Pango
        self.textview.override_font(Pango.FontDescription("Monospace 10"))
        scroll.add(self.textview)
        self._scroll = scroll
        return scroll

    def _build_progress(self):
        box = Gtk.Box()
        box.set_margin_start(12); box.set_margin_end(12)
        box.set_margin_top(6);    box.set_margin_bottom(2)
        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)
        box.pack_start(self.progress, True, True, 0)
        return box

    def _build_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_name("btn-bar")
        box.set_halign(Gtk.Align.CENTER)
        self.btn_run = Gtk.Button(label=tr("btn_run"))
        self.btn_run.set_name("btn-run")
        self.btn_run.connect("clicked", self._on_run)
        box.pack_start(self.btn_run, False, False, 0)
        btn_clear = Gtk.Button(label=tr("btn_clear"))
        btn_clear.set_name("btn-clear")
        btn_clear.connect("clicked", self._on_clear)
        box.pack_start(btn_clear, False, False, 0)
        btn_close = Gtk.Button(label=tr("btn_close"))
        btn_close.set_name("btn-close")
        btn_close.connect("clicked", lambda *_: Gtk.main_quit())
        box.pack_start(btn_close, False, False, 0)
        return box

    def _build_status(self):
        box = Gtk.Box()
        box.set_name("status-bar")
        self.status = Gtk.Label(label=tr("status_ready"))
        self.status.set_name("status-label")
        self.status.set_halign(Gtk.Align.START)
        box.pack_start(self.status, True, True, 0)
        return box

    def _on_drag(self, widget, event):
        if event.button == 1 and event.y < 52:
            self.win.begin_move_drag(
                event.button, int(event.x_root), int(event.y_root), event.time)

    def _append(self, text):
        end = self.textbuf.get_end_iter()
        self.textbuf.insert(end, text + "\n")
        adj = self._scroll.get_vadjustment()
        adj.set_value(adj.get_upper())

    def _on_run(self, *_):
        if self._running:
            return
        self._running = True
        self.btn_run.set_sensitive(False)
        self.textbuf.set_text("")
        self.progress.set_fraction(0.0)
        self.status.set_text(tr("status_running"))
        self._pulse_tag = GLib.timeout_add(120, self._pulse)
        threading.Thread(
            target=self._worker,
            args=(self.chk_update.get_active(), self.chk_autoremove.get_active()),
            daemon=True
        ).start()

    def _pulse(self):
        if self._running:
            self.progress.pulse()
            return True
        return False

    def _worker(self, do_update, do_autoremove):
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        dpkg_confold = ["--force-confold", "--force-confdef"]
        apt_confold  = ["-o", "Dpkg::Options::=--force-confold",
                        "-o", "Dpkg::Options::=--force-confdef"]

        def log(msg):
            GLib.idle_add(self._append, msg)

        def run_cmd(cmd):
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env)
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if line:
                    GLib.idle_add(self._append, line)
            proc.wait()
            return proc.returncode

        try:
            log(tr("log_sep"))
            log(tr("log_header"))
            log(tr("log_sep"))
            log("")

            if do_update:
                log(tr("log_update"))
                rc = run_cmd(["apt-get", "update"])
                log(tr("log_exit", rc=rc))
                log("")

            log(tr("log_step1"))
            rc = run_cmd(["dpkg"] + dpkg_confold + ["--configure", "-a"])
            log(tr("log_exit", rc=rc))
            log("")
            if rc != 0:
                log(tr("log_err_dpkg", rc=rc))
                GLib.idle_add(self._finish, False, tr("err_dpkg", rc=rc))
                return

            log(tr("log_step2"))
            rc = run_cmd(["apt-get", "--fix-broken", "install", "-y"] + apt_confold)
            log(tr("log_exit", rc=rc))
            log("")
            if rc != 0:
                log(tr("log_err_apt", rc=rc))
                GLib.idle_add(self._finish, False, tr("err_apt", rc=rc))
                return

            if do_autoremove:
                log(tr("log_step3"))
                rc = run_cmd(["apt-get", "autoremove", "-y"])
                log(tr("log_exit", rc=rc))
                log("")

            log(tr("log_sep"))
            log(tr("log_done"))
            log(tr("log_sep"))
            GLib.idle_add(self._finish, True, None)

        except Exception as e:
            GLib.idle_add(self._finish, False, str(e))

    def _finish(self, ok, error_msg):
        self._running = False
        if self._pulse_tag:
            GLib.source_remove(self._pulse_tag)
            self._pulse_tag = None
        self.progress.set_fraction(1.0 if ok else 0.0)
        self.btn_run.set_sensitive(True)
        if ok:
            self.status.set_text(tr("status_ok"))
        else:
            self.status.set_text(tr("status_fail", msg=error_msg or "Failed — see output above."))

    def _on_clear(self, *_):
        self.textbuf.set_text("")
        self.progress.set_fraction(0.0)
        self.status.set_text(tr("status_ready"))


def main():
    app = EssoraFixBroken()
    Gtk.main()


if __name__ == "__main__":
    main()
