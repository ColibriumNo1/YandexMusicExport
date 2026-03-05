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


def export_likes(client: YandexClient, exporter: Exporter, filename: str, output_format: str, token: str = None):
    """Экспорт лайкнутых треков."""
    # Используем гибридный метод: сырой JSON для ID + client.tracks() для данных
    tracks, ugc_tracks, unavailable_ids = client.get_likes_tracks_raw()

    # Экспортируем все треки (доступные + UGC + удалённые) в структуре плейлиста
    all_tracks = tracks + ugc_tracks
    exporter.export_tracks_as_playlist(all_tracks, filename, output_format, unavailable_ids)
    return [f'{filename}_tracks.{output_format}']


def export_playlists(client: YandexClient, exporter: Exporter, selected_indices: list = None, token: str = None):
    """Экспорт плейлистов."""
    playlists = client.get_playlists()
    exported_files = []

    if selected_indices:
        # Фильтруем выбранные плейлисты
        filtered_playlists = [playlists[i - 1] for i in selected_indices if i - 1 < len(playlists)]
        if not filtered_playlists:
            print('\n[INFO] Не выбрано плейлистов для экспорта')
            return []
        # Экспортируем каждый плейлист в отдельный файл
        for playlist in filtered_playlists:
            filename = exporter._sanitize_filename(playlist.title)
            exporter.export_playlists([playlist], filename, 'json', token=token)
            exported_files.append(f'{filename}_playlists.json')
    else:
        # Все плейлисты
        for playlist in playlists:
            filename = exporter._sanitize_filename(playlist.title)
            exporter.export_playlists([playlist], filename, 'json', token=token)
            exported_files.append(f'{filename}_playlists.json')

    return exported_files


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

    # Получаем логин пользователя для структуры папок
    try:
        me = client.client.me
        user_login = me.account.login
        exporter.set_user_login(user_login)
        log_logger.info(f'Логин пользователя: {user_login}')
        print(f'\n[OK] Пользователь: {user_login}')
        print(f'📁 Экспорт в папку: exports/{user_login}/json/')
    except Exception as e:
        log_logger.warning(f'Не удалось получить логин: {str(e)}')
        user_login = None

    # Главный цикл меню
    while True:
        choice = Menu.show_main_menu()

        if choice == '0':
            print('\n👋 Выход из программы...')
            return

        elif choice == '1':
            # Экспорт "Мне нравится"
            # Экспорт всех треков в JSON с фиксированным именем
            Menu.show_export_start()
            exported_files = export_likes(client, exporter, 'likes', 'json', token)

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

                # Выбор плейлистов
                selected_indices = None

                if playlists_choice == '2':
                    # Выбор конкретных плейлистов
                    selected_indices = Menu.select_playlists_for_export(client)
                    if not selected_indices:
                        print('\n[INFO] Экспорт отменён')
                        continue

                # Экспорт в JSON
                Menu.show_export_start()
                exported_files = export_playlists(client, exporter, selected_indices, token)

                if exported_files:
                    Menu.show_export_complete(exported_files)
                else:
                    print('\n[INFO] Экспорт не выполнен')

        elif choice == '3':
            # Настройки
            while True:
                settings_choice = Menu.show_settings_menu()

                if settings_choice == '0':
                    break

                elif settings_choice == '1':
                    # Как получить токен
                    Menu.show_token_help()


if __name__ == '__main__':
    main()
