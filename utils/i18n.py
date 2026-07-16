import json
import logging
import sys
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class LocalizationManager:
    """
    Manages application localization by loading translation assets from JSON files.
    """

    def __init__(self, locales_dir: str = "locales", default_lang: str = "en"):
        """
        Initializes the LocalizationManager.

        Args:
            locales_dir (str): The directory containing language JSON files.
            default_lang (str): The default language code to load on startup.
        """
        # Розпізнавання середовища: PyInstaller чи звичайний скрипт
        if getattr(sys, 'frozen', False):
            # Якщо це зкомпільований EXE, шукаємо в папці _internal (куди вказує _MEIPASS)
            base_path = Path(sys._MEIPASS)
        else:
            # Якщо це запуск із сирців, беремо корінь проєкту
            base_path = Path(__file__).resolve().parent.parent
            
        self.locales_dir = base_path / locales_dir
        self.current_lang = default_lang
        self._translations: Dict[str, Dict[str, str]] = {}
        
        self.load_language(default_lang)

    def load_language(self, lang_code: str) -> None:
        """
        Loads the specified language JSON file into memory.

        Args:
            lang_code (str): The language code (e.g., 'en', 'uk').
        """
        if lang_code in self._translations:
            self.current_lang = lang_code
            return

        file_path = self.locales_dir / f"{lang_code}.json"
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._translations[lang_code] = json.load(f)
                self.current_lang = lang_code
            else:
                logger.warning(f"Translation file not found: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load translation {lang_code}: {e}")

    def t(self, key: str) -> str:
        """
        Retrieves the translated string for the given key.

        Args:
            key (str): The localization key.

        Returns:
            str: The translated string, or the original key if not found.
        """
        return self._translations.get(self.current_lang, {}).get(key, key)