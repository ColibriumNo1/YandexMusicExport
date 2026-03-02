"""
Модуль управления конфигурацией.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'yandex_token': '',
    'export': {
        'default_format': 'json',
        'default_filename': 'yandex_export',
        'default_type': 'all'
    },
    'display': {
        'show_track_count_preview': True,
        'tracks_per_page': 20
    }
}


class Config:
    """Класс для работы с конфигурацией."""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.config = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self) -> dict:
        """Загрузка конфигурации из файла."""
        if not self.config_path.exists():
            self.save()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            # Объединяем с дефолтным на случай новых полей
            self._merge_config(loaded)
            logger.info(f'Конфигурация загружена из {self.config_path}')
            
        except Exception as e:
            logger.error(f'Ошибка загрузки конфига: {str(e)}')
            self.save()
        
        return self.config
    
    def _merge_config(self, loaded: dict):
        """Рекурсивное объединение конфигов."""
        for key, value in DEFAULT_CONFIG.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded[key], dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in loaded[key]:
                        loaded[key][sub_key] = sub_value
        
        self.config = loaded
    
    def save(self) -> bool:
        """Сохранение конфигурации в файл."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info(f'Конфигурация сохранена в {self.config_path}')
            return True
        except Exception as e:
            logger.error(f'Ошибка сохранения конфига: {str(e)}')
            return False
    
    def get(self, key: str, default=None):
        """Получение значения из конфига."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value) -> bool:
        """Установка значения в конфиге."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return self.save()
    
    @property
    def token(self) -> str:
        """Получение токена."""
        return self.config.get('yandex_token', '')
    
    @token.setter
    def token(self, value: str):
        """Установка токена."""
        self.set('yandex_token', value)
    
    @property
    def default_format(self) -> str:
        """Формат экспорта по умолчанию."""
        return self.get('export.default_format', 'json')
    
    @property
    def default_filename(self) -> str:
        """Имя файла по умолчанию."""
        return self.get('export.default_filename', 'yandex_export')
