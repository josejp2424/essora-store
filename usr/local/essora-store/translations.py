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



import os
import json
import locale

class TranslationManager:
    """Manages translations for Essora Store.
    
    Primary language: English (hardcoded in the code)
    Translations directory: /usr/local/essora-store/lang/
    Falls back to English if translation not found.
    """
    
    def __init__(self, lang_dir="/usr/local/essora-store/lang"):
        self.lang_dir = lang_dir
        self.translations = {}
        self.current_lang = self._detect_system_language()
        self._load_translations()
    
    def _detect_system_language(self):
        """Detect system language, return language code (e.g., 'es', 'pt', 'fr')."""
        try:
            lang = locale.getdefaultlocale()[0]
            if lang:

                return lang.split('_')[0].lower()
        except Exception:
            pass
        return 'en'  
    
    def _load_translations(self):
        """Load translation file for current language."""
        if self.current_lang == 'en':

            return
        
        lang_file = os.path.join(self.lang_dir, f"{self.current_lang}.json")
        if not os.path.exists(lang_file):

            self.current_lang = 'en'
            return
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"[LANG] Error loading translation file {lang_file}: {e}")
            self.current_lang = 'en'
            self.translations = {}
    
    def get(self, key, **kwargs):
        """Get translated string for key, with optional formatting."""

        if self.current_lang != 'en' and key in self.translations:
            text = self.translations[key]
        else:

            text = key
        

        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        
        return text
    
    def set_language(self, lang_code):
        """Manually set language."""
        self.current_lang = lang_code.lower()
        self._load_translations()



_translation_manager = None

def init_translations(lang_dir="/usr/local/essora-store/lang"):
    """Initialize translation manager."""
    global _translation_manager
    _translation_manager = TranslationManager(lang_dir)
    return _translation_manager

def tr(text, **kwargs):
    """Translation function. Returns translated text or original if not found."""
    global _translation_manager
    if _translation_manager is None:
        init_translations()
    return _translation_manager.get(text, **kwargs)

def get_translation_manager():
    """Get the global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        init_translations()
    return _translation_manager
