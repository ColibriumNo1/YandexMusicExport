#!/usr/bin/env python3
"""
Простой экспорт библиотеки из Яндекс.Музыки в JSON/CSV.
Интерактивная версия с меню.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.yandex_client import YandexClient
from src.exporter import Exporter
from src.menu import Menu

# Создаём папку для логов
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Создаём имя файла лога с датой и временем
log_filename = log_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Настраиваем логирование вручную для полного контроля
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Общий уровень - DEBUG

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Обработчик для файла (DEBUG и выше)
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Обработчик для консоли (только INFO и выше)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Фильтр для блокировки DEBUG в консоли
class NoDebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.INFO

console_handler.addFilter(NoDebugFilter())
logger.addHandler(console_handler)

# Отключаем логирование библиотеки yandex-music (слишком многословная)
logging.getLogger('yandex_music').setLevel(logging.WARNING)

log_logger = logging.getLogger(__name__)
log_logger.info(f'Логирование включено. Файл лога: {log_filename}')


def export_likes(client: YandexClient, exporter: Exporter, filename: str, output_format: str, export_type: str, token: str = None):
    """Экспорт лайкнутых треков."""
    # Используем гибридный метод: сырой JSON для ID + client.tracks() для данных
    tracks, ugc_tracks, unavailable_ids = client.get_likes_tracks_raw()

    if export_type == 'all':
        # Экспортируем все треки (доступные + UGC) в структуре плейлиста
        all_tracks = tracks + ugc_tracks
        exporter.export_tracks_as_playlist(all_tracks, filename, output_format, unavailable_ids)
        return [f'{filename}_tracks.{output_format}']

    elif export_type == 'available':
        # Только доступные
        if not tracks:
            print('\n[INFO] Нет доступных треков для экспорта')
            return []
        exporter.export_tracks_as_playlist(tracks, filename, output_format, unavailable_ids)
        return [f'{filename}_tracks_available.{output_format}']

    elif export_type == 'unavailable':
        # Только недоступные (UGC + удалённые)
        if not ugc_tracks and not unavailable_ids:
            print('\n[INFO] Нет недоступных треков для экспорта')
            return []
        # Экспортируем UGC треки и ID удалённых
        exporter.export_tracks_as_playlist(ugc_tracks, filename, output_format, unavailable_ids, unavailable_only=True)
        return [f'{filename}_tracks_unavailable.{output_format}']

    return []


def export_playlists(client: YandexClient, exporter: Exporter, filename: str, output_format: str, export_type: str, selected_indices: list = None, token: str = None):
    """Экспорт плейлистов."""
    playlists = client.get_playlists()

    if export_type == 'selected' and selected_indices:
        # Фильтруем выбранные плейлисты
        filtered_playlists = [playlists[i - 1] for i in selected_indices if i - 1 < len(playlists)]
        if not filtered_playlists:
            print('\n[INFO] Не выбрано плейлистов для экспорта')
            return []
        exporter.export_playlists(filtered_playlists, filename, output_format, token=token)
        return [f'{filename}_playlists.{output_format}']
    else:
        # Все плейлисты
        exporter.export_playlists(playlists, filename, output_format, token=token)
        return [f'{filename}_playlists.{output_format}']


def main():
    """Основная функция с интерактивным меню."""
    # Загрузка конфигурации
    config = Config()

    # Получение токена
    token_result = Menu.get_token(config.token)

    if isinstance(token_result, tuple):
        token, save = token_result
        if save:
            config.token = token
    else:
        token = token_result

    if not token:
        return

    # Инициализация клиента
    print('\n' + Menu.SEPARATOR)
    log_logger.info('Инициализация клиента Яндекс.Музыки...')

    client = YandexClient(token)

    if not client.init():
        print('\n[ERROR] Не удалось подключиться к Яндекс.Музыке.')
        print('Проверьте правильность токена.')
        return

    log_logger.info('[OK] Подключение успешно!')

    # Инициализация экспортера
    exporter = Exporter()

    # Главный цикл меню
    while True:
        choice = Menu.show_main_menu()

        if choice == '0':
            print('\n👋 Выход из программы...')
            return

        elif choice == '1':
            # Экспорт "Мне нравится"
            while True:
                likes_choice = Menu.show_likes_menu()

                if likes_choice == '0':
                    break

                elif likes_choice == '4':
                    # Показать список треков
                    Menu.show_likes_preview(client)
                    continue

                # Выбор формата и имени файла
                output_format = Menu.select_format(config.default_format)
                filename = Menu.get_filename(config.default_filename)

                # Определение типа экспорта
                export_type_map = {
                    '1': 'all',
                    '2': 'available',
                    '3': 'unavailable'
                }
                export_type = export_type_map.get(likes_choice, 'all')

                # Экспорт
                Menu.show_export_start()
                exported_files = export_likes(client, exporter, filename, output_format, export_type, token)

                if exported_files:
                    Menu.show_export_complete(exported_files)
                else:
                    print('\n[INFO] Экспорт не выполнен')

        elif choice == '2':
            # Экспорт плейлистов
            while True:
                playlists_choice = Menu.show_playlists_menu()

                if playlists_choice == '0':
                    break

                elif playlists_choice == '3':
                    # Показать список плейлистов
                    Menu.show_playlists_preview(client)
                    continue

                # Выбор формата и имени файла
                output_format = Menu.select_format(config.default_format)
                filename = Menu.get_filename(config.default_filename)

                # Выбор плейлистов
                selected_indices = None
                export_type = 'all'

                if playlists_choice == '2':
                    # Выбор конкретных плейлистов
                    selected_indices = Menu.select_playlists_for_export(client)
                    if not selected_indices:
                        print('\n[INFO] Экспорт отменён')
                        continue
                    export_type = 'selected'

                # Экспорт
                Menu.show_export_start()
                exported_files = export_playlists(client, exporter, filename, output_format, export_type, selected_indices, token)

                if exported_files:
                    Menu.show_export_complete(exported_files)
                else:
                    print('\n[INFO] Экспорт не выполнен')

        elif choice == '3':
            # Настройки
            while True:
                settings_choice = Menu.show_settings_menu(config)

                if settings_choice == '0':
                    break

                elif settings_choice == '1':
                    # Изменить формат по умолчанию
                    new_format = Menu.select_format(config.default_format)
                    config.set('export.default_format', new_format)
                    print(f'\n[OK] Формат по умолчанию изменён на {new_format}')
                    log_logger.info('Формат по умолчанию изменён: %s', new_format)

                elif settings_choice == '2':
                    # Изменить имя файла по умолчанию
                    print('\n' + Menu.DASH)
                    new_filename = input(f'Новое имя файла (Enter = {config.default_filename}): ').strip()
                    if new_filename:
                        config.set('export.default_filename', new_filename)
                        print(f'\n[OK] Имя файла по умолчанию изменено на {new_filename}')
                        log_logger.info('Имя файла по умолчанию изменено: %s', new_filename)

                elif settings_choice == '3':
                    # Как получить токен
                    Menu.show_token_help()


if __name__ == '__main__':
    main()
