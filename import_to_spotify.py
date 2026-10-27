#!/usr/bin/env python3
"""
Импорт музыки из JSON в Spotify.
Интерактивный CLI для импорта плейлистов из Яндекс.Музыки в Spotify.
"""

import logging
import sys
from pathlib import Path

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.spotify_client import SpotifyClient
from src.importer import Importer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImportMenu:
    """Интерактивное меню для импорта в Spotify."""

    SEPARATOR = '=' * 60
    DASH = '-' * 60

    @staticmethod
    def show_header():
        """Показать заголовок."""
        print('\n' + ImportMenu.SEPARATOR)
        print('       ИМПОРТ В SPOTIFY')
        print(ImportMenu.SEPARATOR)

    @staticmethod
    def get_spotify_credentials(config: Config):
        """Получение учётных данных Spotify."""
        ImportMenu.show_header()

        # Проверяем сохранённые данные
        saved_id = config.spotify_client_id
        saved_secret = config.spotify_client_secret

        if saved_id and saved_secret:
            print('\n[OK] Учётные данные Spotify найдены в конфигурации')
            print('  [1] Использовать сохранённые')
            print('  [2] Ввести новые')
            print(ImportMenu.DASH)

            choice = input('Ваш выбор (1-2): ').strip()

            if choice == '1':
                return saved_id, saved_secret

        print('\nДля работы со Spotify необходимо создать приложение:')
        print('1. Перейдите на https://developer.spotify.com/dashboard')
        print('2. Нажмите "Create an App"')
        print('3. Заполните название и описание')
        print('4. В настройках добавьте Redirect URI:')
        print('   http://127.0.0.1:8888/callback')
        print('5. Скопируйте Client ID и Client Secret')
        print(ImportMenu.DASH)

        client_id = input('\nClient ID: ').strip()
        if not client_id:
            print('[ERROR] Client ID не введён!')
            return None, None

        client_secret = input('Client Secret: ').strip()
        if not client_secret:
            print('[ERROR] Client Secret не введён!')
            return None, None

        # Спрашиваем о сохранении
        save = input('\nСохранить в config.json? (y/n): ').strip().lower()
        if save == 'y' or save == 'д':
            config.spotify_client_id = client_id
            config.spotify_client_secret = client_secret
            print('[OK] Учётные данные сохранены')

        return client_id, client_secret

    @staticmethod
    def show_main_menu() -> str:
        """Показать главное меню."""
        print('\n' + ImportMenu.DASH)
        print('ВЫБЕРИТЕ ТИП ИМПОРТА:')
        print(ImportMenu.DASH)
        print('  [1] Импорт "Мне нравится" (из экспорта)')
        print('  [2] Импорт плейлиста (из экспорта)')
        print('  [3] Импорт из JSON файла')
        print('  [0] Выход')
        print(ImportMenu.DASH)

        while True:
            choice = input('Ваш выбор (0-3): ').strip()

            if choice in ('0', '1', '2', '3'):
                return choice
            else:
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def get_json_file_path() -> str:
        """Получение пути к JSON файлу."""
        print('\n' + ImportMenu.DASH)
        print('Укажите путь к JSON файлу экспорта:')
        print('(или оставьте пустым для поиска в exports/)')
        print(ImportMenu.DASH)

        path = input('Путь к файлу: ').strip()

        if not path:
            # Ищем в exports/
            exports_dir = Path(__file__).parent / 'exports'
            if exports_dir.exists():
                json_files = list(exports_dir.glob('**/*.json'))
                if json_files:
                    print(f'\nНайдено JSON файлов: {len(json_files)}')
                    for i, f in enumerate(json_files[:10], 1):
                        print(f'  [{i}] {f.relative_to(exports_dir)}')
                    if len(json_files) > 10:
                        print(f'  ... и ещё {len(json_files) - 10}')

                    choice = input('\nВыберите файл (номер): ').strip()
                    if choice.isdigit() and int(choice) <= len(json_files):
                        return str(json_files[int(choice) - 1])

            print('[ERROR] Файл не выбран')
            return ''

        if not Path(path).exists():
            print(f'[ERROR] Файл не найден: {path}')
            return ''

        return path

    @staticmethod
    def get_playlist_name() -> str:
        """Получение названия плейлиста."""
        print('\n' + ImportMenu.DASH)
        name = input('Название плейлиста в Spotify (Enter = как в источнике): ').strip()
        return name if name else None

    @staticmethod
    def show_export_path():
        """Показать путь к экспорту."""
        exports_dir = Path(__file__).parent / 'exports'
        print(f'\n📁 Папка экспорта: {exports_dir}')

        if exports_dir.exists():
            user_dirs = [d for d in exports_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            if user_dirs:
                print(f'Найдено пользователей: {len(user_dirs)}')
                for user_dir in user_dirs:
                    json_dir = user_dir / 'json'
                    if json_dir.exists():
                        json_files = list(json_dir.glob('*.json'))
                        print(f'  • {user_dir.name}: {len(json_files)} файлов')

    @staticmethod
    def show_import_complete(stats: dict):
        """Показать завершение импорта."""
        if not stats.get('success'):
            print(f'\n❌ Импорт не выполнен: {stats.get("error", "Неизвестная ошибка")}')
            return

        print('\n' + ImportMenu.SEPARATOR)
        print('🎉 ИМПОРТ ЗАВЕРШЁН!')
        print(ImportMenu.SEPARATOR)
        print(f'\n✅ Плейлист создан: {stats["playlist_name"]}')
        print(f'📊 Статистика:')
        print(f'   • Всего треков: {stats["total_tracks"]}')
        print(f'   • Найдено: {stats["found_tracks"]}')
        print(f'   • Не найдено: {stats["not_found_tracks"]}')

        if stats['total_tracks'] > 0:
            rate = (stats['found_tracks'] / stats['total_tracks']) * 100
            print(f'   • Успех: {rate:.1f}%')

        print(ImportMenu.SEPARATOR)
        input('\nНажмите Enter для выхода...')


def import_likes(spotify_client: SpotifyClient, exporter_dir: str = None):
    """Импорт лайкнутых треков."""
    if not exporter_dir:
        exporter_dir = str(Path(__file__).parent / 'exports')

    importer = Importer(spotify_client)
    return importer.import_likes_from_exporter(exporter_dir)


def import_playlist(spotify_client: SpotifyClient, exporter_dir: str = None):
    """Импорт плейлиста."""
    if not exporter_dir:
        exporter_dir = str(Path(__file__).parent / 'exports')

    # Показываем доступные плейлисты
    ImportMenu.show_export_path()

    playlist_name = ImportMenu.get_playlist_name()

    if not playlist_name:
        print('\n[ERROR] Название плейлиста не указано')
        return

    importer = Importer(spotify_client)
    return importer.import_playlist_from_exporter(exporter_dir, playlist_name)


def import_from_json(spotify_client: SpotifyClient):
    """Импорт из JSON файла."""
    json_file = ImportMenu.get_json_file_path()

    if not json_file:
        return

    playlist_name = ImportMenu.get_playlist_name()

    importer = Importer(spotify_client)
    return importer.import_from_json(json_file, playlist_name)


def main():
    """Основная функция."""
    # Загрузка конфигурации
    config = Config()

    # Получение учётных данных Spotify
    credentials = ImportMenu.get_spotify_credentials(config)

    if not credentials[0] or not credentials[1]:
        return

    client_id, client_secret = credentials

    # Инициализация клиента Spotify
    print('\n' + ImportMenu.SEPARATOR)
    logger.info('Инициализация клиента Spotify...')

    spotify_client = SpotifyClient(client_id, client_secret)

    if not spotify_client.init():
        print('\n[ERROR] Не удалось подключиться к Spotify')
        print('Проверьте правильность Client ID и Client Secret')
        return

    logger.info('[OK] Подключение успешно!')

    # Главный цикл меню
    while True:
        choice = ImportMenu.show_main_menu()

        if choice == '0':
            print('\n👋 Выход из программы...')
            return

        elif choice == '1':
            # Импорт "Мне нравится"
            stats = import_likes(spotify_client)
            if stats:
                ImportMenu.show_import_complete(stats)

        elif choice == '2':
            # Импорт плейлиста
            stats = import_playlist(spotify_client)
            if stats:
                ImportMenu.show_import_complete(stats)

        elif choice == '3':
            # Импорт из JSON
            stats = import_from_json(spotify_client)
            if stats:
                ImportMenu.show_import_complete(stats)


if __name__ == '__main__':
    main()
