"""
Импорт музыки из JSON в Spotify.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


class Importer:
    """Класс для импорта треков из JSON в Spotify."""

    def __init__(self, spotify_client: SpotifyClient):
        """
        Инициализация импортёра.

        Args:
            spotify_client: Клиент Spotify
        """
        self.spotify_client = spotify_client
        self.not_found_tracks = []

    def import_from_json(self, json_file: str, playlist_name: str = None) -> Dict:
        """
        Импорт треков из JSON файла в Spotify.

        Args:
            json_file: Путь к JSON файлу
            playlist_name: Название плейлиста в Spotify (по умолчанию из файла)

        Returns:
            Статистика импорта
        """
        self.not_found_tracks = []

        # Загружаем JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f'Ошибка чтения JSON файла: {str(e)}')
            return {'success': False, 'error': str(e)}

        # Извлекаем треки
        all_tracks = []
        source_name = ''

        for playlist in data:
            if not isinstance(playlist, dict):
                continue

            if not source_name:
                source_name = playlist.get('title', 'Import')

            tracks = playlist.get('tracks', [])
            all_tracks.extend(tracks)

        if not all_tracks:
            logger.warning('Нет треков для импорта')
            return {'success': False, 'error': 'No tracks found'}

        # Используем имя из файла или переданное
        if not playlist_name:
            playlist_name = f'{source_name} (from Yandex Music)'

        logger.info(f'Импортируем {len(all_tracks)} треков в плейлист "{playlist_name}"')

        # Ищем треки в Spotify
        spotify_tracks = []
        total = len(all_tracks)

        print(f'\n🔍 Поиск треков в Spotify...')

        for i, track in enumerate(all_tracks, 1):
            if not isinstance(track, dict):
                continue

            title = track.get('title', '')
            artists = track.get('artists', '')
            album = track.get('album', '')

            if not title or title == 'Unknown':
                continue

            print(f'[{i}/{total}] Ищем: {artists} - {title}')

            # Поиск трека
            spotify_uri = self.spotify_client.search_track(title, artists, album)

            if spotify_uri:
                spotify_tracks.append(spotify_uri)
                print(f'  ✅ Найден')
            else:
                self.not_found_tracks.append({
                    'title': title,
                    'artists': artists,
                    'album': album
                })
                print(f'  ❌ Не найден')

            # Небольшая задержка
            import time
            time.sleep(0.05)

        # Создаём плейлист
        if not spotify_tracks:
            print('\n❌ Не найдено ни одного трека')
            return {'success': False, 'error': 'No tracks found in Spotify'}

        print(f'\n📝 Создание плейлиста "{playlist_name}"...')

        try:
            playlist_id = self.spotify_client.create_playlist(
                name=playlist_name,
                description=f'Импортировано из Яндекс Музыки. Найдено: {len(spotify_tracks)}/{total} треков'
            )

            # Добавляем треки
            self.spotify_client.add_tracks_to_playlist(playlist_id, spotify_tracks)

            # Статистика
            stats = {
                'success': True,
                'playlist_name': playlist_name,
                'playlist_id': playlist_id,
                'total_tracks': total,
                'found_tracks': len(spotify_tracks),
                'not_found_tracks': len(self.not_found_tracks)
            }

            self._print_stats(stats)
            self._save_not_found_tracks(json_file)

            return stats

        except Exception as e:
            logger.error(f'Ошибка создания плейлиста: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _print_stats(self, stats: Dict):
        """Вывод статистики импорта."""
        print('\n' + '=' * 60)
        print('🎉 Импорт завершён!')
        print('=' * 60)
        print(f'📊 Статистика:')
        print(f'   • Плейлист: {stats["playlist_name"]}')
        print(f'   • Всего треков в источнике: {stats["total_tracks"]}')
        print(f'   • Найдено в Spotify: {stats["found_tracks"]}')
        print(f'   • Не найдено: {stats["not_found_tracks"]}')

        if stats['total_tracks'] > 0:
            success_rate = (stats['found_tracks'] / stats['total_tracks']) * 100
            print(f'   • Успешно: {success_rate:.1f}%')

        print('=' * 60)

    def _save_not_found_tracks(self, json_file: str):
        """Сохранение списка ненайденных треков."""
        if not self.not_found_tracks:
            return

        try:
            # Создаём имя файла на основе исходного
            json_path = Path(json_file)
            not_found_file = json_path.parent / f'{json_path.stem}_not_found.json'

            with open(not_found_file, 'w', encoding='utf-8') as f:
                json.dump(self.not_found_tracks, f, ensure_ascii=False, indent=2)

            print(f'📄 Список ненайденных треков сохранён: {not_found_file.name}')

        except Exception as e:
            logger.error(f'Ошибка сохранения списка ненайденных треков: {str(e)}')

    def import_likes_from_exporter(self, exporter_dir: str, playlist_name: str = None):
        """
        Импорт лайкнутых треков из экспорта Yandex Music Export.

        Args:
            exporter_dir: Путь к папке с экспортом exports/{login}/json/
            playlist_name: Название плейлиста (по умолчанию "Мне нравится")
        """
        # Ищем файл likes_tracks.json
        exports_path = Path(exporter_dir)
        json_files = list(exports_path.glob('**/likes_tracks.json'))

        if not json_files:
            logger.error(f'Файл likes_tracks.json не найден в {exports_path}')
            print(f'\n❌ Файл likes_tracks.json не найден')
            print(f'   Путь: {exports_path}')
            return None

        json_file = json_files[0]
        logger.info(f'Найден файл экспорта: {json_file}')

        if not playlist_name:
            playlist_name = 'Мне нравится'

        return self.import_from_json(str(json_file), playlist_name)

    def import_playlist_from_exporter(self, exporter_dir: str, playlist_title: str):
        """
        Импорт конкретного плейлиста из экспорта Yandex Music Export.

        Args:
            exporter_dir: Путь к папке с экспортом
            playlist_title: Название плейлиста для поиска
        """
        exports_path = Path(exporter_dir)
        json_files = list(exports_path.glob('**/*_playlists.json'))

        if not json_files:
            logger.error(f'Файлы *_playlists.json не найдены в {exports_path}')
            print(f'\n❌ Файлы плейлистов не найдены')
            return None

        # Ищем плейлист с matching названием
        target_file = None

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for playlist in data:
                    if isinstance(playlist, dict) and playlist.get('title') == playlist_title:
                        target_file = str(json_file)
                        break

            except Exception:
                continue

        if not target_file:
            print(f'\n❌ Плейлист "{playlist_title}" не найден в экспорте')
            return None

        return self.import_from_json(target_file, playlist_title)
