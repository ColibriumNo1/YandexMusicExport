"""
Модуль экспорта данных из Яндекс.Музыки.
"""

import json
import csv
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class Exporter:
    """Класс для экспорта данных в различные форматы."""

    def __init__(self, output_dir: str = 'exports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_tracks(self, tracks, filename: str, format: str = 'json', unavailable_tracks: list = None, unavailable_only: bool = False):
        """Экспорт треков.

        Args:
            tracks: Список доступных треков (объекты Track или dict из API)
            filename: Имя файла
            format: Формат файла (json/csv)
            unavailable_tracks: Список недоступных треков (ID)
            unavailable_only: Если True, экспортировать только недоступные треки
        """
        data = []
        position = 1

        if unavailable_only:
            # Экспорт только недоступных треков
            if unavailable_tracks:
                for ut_id in unavailable_tracks:
                    data.append({
                        'position': position,
                        'type': 'track',
                        'id': ut_id,
                        'title': 'Unknown',
                        'artists': 'Unknown',
                        'album': 'Unknown',
                        'year': None,
                        'duration_ms': None,
                        'availability_reason': 'deleted'
                    })
                    position += 1
            logger.info(f'Подготовлено {len(data)} недоступных треков для экспорта')
            self._save(data, filename, format)
            return len(data)

        # Экспорт доступных треков
        for track in tracks:
            if track is None:
                continue

            # Обрабатываем как dict (сырой JSON) так и объект Track
            if isinstance(track, dict):
                # Сырой JSON из API
                track_id = track.get('id') or track.get('realId')
                title = track.get('title', 'Unknown') or 'Unknown'
                
                # Артисты
                artists_str = 'Unknown'
                artists = track.get('artists', [])
                if artists:
                    artist_names = [
                        a.get('name') for a in artists 
                        if isinstance(a, dict) and a.get('name')
                    ]
                    if artist_names:
                        artists_str = ', '.join(artist_names)
                
                # Альбом
                album_str = 'Unknown'
                year = None
                albums = track.get('albums', [])
                if albums and isinstance(albums[0], dict):
                    album_str = albums[0].get('title', 'Unknown')
                    year = albums[0].get('year')
                
                # Дополнительные поля
                duration_ms = track.get('durationMs') or track.get('duration_ms')
                isrc = track.get('isrc')
                source = 'UGC' if track.get('trackSource') == 'UGC' else 'catalog'
                filename_orig = track.get('filename')
                storage_dir = track.get('storageDir')
                user_info = track.get('userInfo', {})
                uploaded_by = None
                if user_info:
                    uploaded_by = user_info.get('login') or user_info.get('displayName')
                
            else:
                # Объект Track из библиотеки
                track_id = str(track.id) if hasattr(track, 'id') else None
                title = track.title or 'Unknown'
                
                # Артисты
                artists_str = 'Unknown'
                try:
                    if track.artists:
                        artist_names = []
                        for artist in track.artists:
                            if artist and hasattr(artist, 'name'):
                                artist_names.append(artist.name)
                        if artist_names:
                            artists_str = ', '.join(artist_names)
                except:
                    pass
                
                # Альбом
                album_str = 'Unknown'
                year = None
                try:
                    if track.albums:
                        album = track.albums[0]
                        if album and hasattr(album, 'title'):
                            album_str = album.title
                        if album and hasattr(album, 'year'):
                            year = album.year
                except:
                    pass
                
                # Дополнительные поля
                duration_ms = track.duration_ms if hasattr(track, 'duration_ms') else None
                isrc = track.isrc if hasattr(track, 'isrc') else None
                source = 'catalog'
                filename_orig = None
                storage_dir = None
                uploaded_by = None

            # Формируем запись
            track_data = {
                'position': position,
                'type': 'track',
                'id': track_id,
                'title': title,
                'artists': artists_str,
                'album': album_str,
                'year': year,
                'duration_ms': duration_ms
            }
            
            # Добавляем дополнительные поля только если они есть
            if isrc:
                track_data['isrc'] = isrc
            if source == 'UGC':
                track_data['source'] = source
            if filename_orig:
                track_data['filename'] = filename_orig
            if storage_dir:
                track_data['storage_dir'] = storage_dir
            if uploaded_by:
                track_data['uploaded_by'] = uploaded_by

            data.append(track_data)
            position += 1

        # Добавляем недоступные треки (удалённые) отдельным списком
        if unavailable_tracks:
            for ut_id in unavailable_tracks:
                data.append({
                    'position': position,
                    'type': 'track',
                    'id': ut_id,
                    'title': 'Unknown',
                    'artists': 'Unknown',
                    'album': 'Unknown',
                    'year': None,
                    'duration_ms': None,
                    'availability_reason': 'deleted'
                })
                position += 1

        logger.info(f'Подготовлено {len(data)} треков для экспорта')
        self._save(data, f'{filename}_tracks', format)
        return len(data)

    def export_tracks_as_playlist(self, tracks, filename: str, format: str = 'json', unavailable_ids: list = None, unavailable_only: bool = False):
        """Экспорт треков в структуре плейлиста (с вложенностью tracks).

        Args:
            tracks: Список треков (объекты Track или dict из API)
            filename: Имя файла
            format: Формат файла (json/csv)
            unavailable_ids: Список недоступных треков (ID)
            unavailable_only: Если True, экспортировать только недоступные треки
        """
        # Создаём структуру плейлиста
        playlist_data = {
            'type': 'playlist',
            'title': 'Мне нравится',
            'kind': 'likes',
            'track_count': 0,
            'tracks': []
        }
        
        position = 1
        
        if unavailable_only:
            # Только недоступные треки
            if unavailable_ids:
                for ut_id in unavailable_ids:
                    playlist_data['tracks'].append({
                        'position': position,
                        'type': 'track',
                        'id': ut_id,
                        'title': 'Unknown',
                        'artists': 'Unknown',
                        'album': 'Unknown',
                        'year': None,
                        'duration_ms': None,
                        'availability_reason': 'deleted'
                    })
                    position += 1
            playlist_data['track_count'] = len(playlist_data['tracks'])
            logger.info(f'Подготовлено {len(playlist_data["tracks"])} недоступных треков для экспорта')
            self._save([playlist_data], f'{filename}_tracks', format)
            return len(playlist_data['tracks'])
        
        # Экспорт доступных треков
        for track in tracks:
            if track is None:
                continue
            
            if isinstance(track, dict):
                track_info = self._extract_track_info_full(track, position)
            else:
                # Конвертируем объект Track в dict
                track_dict = {}
                if hasattr(track, 'to_dict'):
                    try:
                        track_dict = track.to_dict()
                    except:
                        pass
                
                # Извлекаем поля
                track_info = {
                    'position': position,
                    'type': 'track',
                    'id': str(track.id) if hasattr(track, 'id') else None,
                    'title': track.title or 'Unknown',
                    'artists': 'Unknown',
                    'album': 'Unknown',
                    'year': None,
                    'duration_ms': track.duration_ms if hasattr(track, 'duration_ms') else None
                }
                
                # Артисты
                try:
                    if track.artists:
                        artist_names = [a.name for a in track.artists if hasattr(a, 'name') and a.name]
                        if artist_names:
                            track_info['artists'] = ', '.join(artist_names)
                except:
                    pass
                
                # Альбом
                try:
                    if track.albums:
                        album = track.albums[0]
                        if hasattr(album, 'title'):
                            track_info['album'] = album.title
                        if hasattr(album, 'year'):
                            track_info['year'] = album.year
                except:
                    pass
                
                # Дополнительные поля
                if hasattr(track, 'isrc') and track.isrc:
                    track_info['isrc'] = track.isrc
            
            playlist_data['tracks'].append(track_info)
            position += 1
        
        # Добавляем удалённые треки
        if unavailable_ids:
            for ut_id in unavailable_ids:
                playlist_data['tracks'].append({
                    'position': position,
                    'type': 'track',
                    'id': ut_id,
                    'title': 'Unknown',
                    'artists': 'Unknown',
                    'album': 'Unknown',
                    'year': None,
                    'duration_ms': None,
                    'availability_reason': 'deleted'
                })
                position += 1
        
        playlist_data['track_count'] = len(playlist_data['tracks'])
        logger.info(f'Подготовлено {playlist_data["track_count"]} треков для экспорта')
        self._save([playlist_data], f'{filename}_tracks', format)
        return playlist_data['track_count']

    def export_tracks_raw(self, tracks_raw: list, filename: str, format: str = 'json'):
        """Экспорт лайкнутых треков из сырых данных API.

        Args:
            tracks_raw: Список треков из сырого JSON API
            filename: Имя файла
            format: Формат файла (json/csv)
        """
        data = []
        position = 1
        available_count = 0
        unavailable_count = 0

        for track_data in tracks_raw:
            # Получаем сам трек из обёртки
            track = track_data.get('track', {}) if isinstance(track_data, dict) else {}
            
            if not track:
                continue

            # Проверяем доступность
            is_available = track.get('available', True)
            availability_reason = None
            
            if not is_available:
                availability_reason = 'not_available'
                unavailable_count += 1
            else:
                available_count += 1

            # Извлекаем информацию о треке
            track_info = self._extract_track_info(track)
            
            # Добавляем дополнительные поля
            data.append({
                'position': position,
                'type': 'track',
                'title': track_info['title'],
                'artists': track_info['artists'],
                'album': track_info['album'],
                'year': track.get('year') or (track.get('albums', [{}])[0].get('year') if track.get('albums') else None),
                'duration_ms': track.get('duration_ms'),
                'explicit': track.get('explicit'),
                'available': is_available,
                'availability_reason': availability_reason
            })
            position += 1

        logger.info(f'Подготовлено {len(data)} треков для экспорта (доступно: {available_count}, недоступно: {unavailable_count})')
        self._save(data, f'{filename}_tracks', format)
        return len(data)

    def _get_playlist_tracks_raw(self, playlist, token: str) -> list:
        """Получение треков плейлиста напрямую через API (сырой JSON)."""
        try:
            owner_uid = playlist.owner.uid
            kind = playlist.kind
            
            url = f'https://api.music.yandex.net/users/{owner_uid}/playlists/{kind}'
            
            headers = {
                'Authorization': f'OAuth {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result') and 'tracks' in data['result']:
                logger.debug(f'Плейлист "{playlist.title}": получено {len(data["result"]["tracks"])} треков через API')
                return data['result']['tracks']
            else:
                logger.warning(f'Плейлист "{playlist.title}": нет треков в ответе API')
                return []
                
        except Exception as e:
            logger.error(f'Ошибка получения треков плейлиста через API: {str(e)}')
            return []

    def _extract_track_info(self, track: dict) -> dict:
        """Извлечение информации о треке из сырых данных API (базовая версия)."""
        if not track:
            return None
        
        # Название
        title = track.get('title', 'Unknown') or 'Unknown'
        
        # Артисты
        artists_str = 'Unknown'
        artists = track.get('artists', [])
        if artists:
            artist_names = [
                a.get('name') for a in artists 
                if isinstance(a, dict) and a.get('name')
            ]
            if artist_names:
                artists_str = ', '.join(artist_names)
        
        # Альбом
        album_str = 'Unknown'
        albums = track.get('albums', [])
        if albums and isinstance(albums[0], dict):
            album_str = albums[0].get('title', 'Unknown')
        
        return {
            'title': title,
            'artists': artists_str,
            'album': album_str
        }

    def _extract_track_info_full(self, track: dict, position: int = None) -> dict:
        """Извлечение полной информации о треке из сырых данных API."""
        if not track:
            return None
        
        # ID
        track_id = track.get('id') or track.get('realId')
        
        # Название
        title = track.get('title', 'Unknown') or 'Unknown'
        
        # Артисты
        artists_str = 'Unknown'
        artists = track.get('artists', [])
        if artists:
            artist_names = [
                a.get('name') for a in artists 
                if isinstance(a, dict) and a.get('name')
            ]
            if artist_names:
                artists_str = ', '.join(artist_names)
        
        # Альбом и год
        album_str = 'Unknown'
        year = None
        albums = track.get('albums', [])
        if albums and isinstance(albums[0], dict):
            album_str = albums[0].get('title', 'Unknown')
            year = albums[0].get('year')
        
        # Длительность
        duration_ms = track.get('durationMs') or track.get('duration_ms')
        
        # Формируем базовую структуру
        track_data = {
            'position': position,
            'type': 'track',
            'id': track_id,
            'title': title,
            'artists': artists_str,
            'album': album_str,
            'year': year,
            'duration_ms': duration_ms
        }
        
        # Добавляем дополнительные поля только если они есть
        isrc = track.get('isrc')
        if isrc:
            track_data['isrc'] = isrc
        
        source = track.get('trackSource')
        if source == 'UGC':
            track_data['source'] = 'UGC'
            
            filename_orig = track.get('filename')
            if filename_orig:
                track_data['filename'] = filename_orig
            
            storage_dir = track.get('storageDir')
            if storage_dir:
                track_data['storage_dir'] = storage_dir
            
            # Информация о загрузившем пользователе
            user_info = track.get('userInfo', {})
            if user_info:
                uploaded_by = user_info.get('login') or user_info.get('displayName')
                if uploaded_by:
                    track_data['uploaded_by'] = uploaded_by
        
        return track_data

    def export_playlists(self, playlists, filename: str, format: str = 'json', token: str = None):
        """Экспорт плейлистов."""
        if not token:
            logger.error('Экспорт плейлистов требует токен для прямого доступа к API')
            return 0
        
        data = []

        for playlist in playlists:
            playlist_data = {
                'type': 'playlist',
                'title': playlist.title,
                'kind': playlist.kind,
                'track_count': playlist.track_count,
                'tracks': []
            }
            
            # Получаем треки напрямую через API
            tracks_raw = self._get_playlist_tracks_raw(playlist, token)
            
            # Обрабатываем каждый трек с полными данными
            position = 1
            for track_entry in tracks_raw:
                track = track_entry.get('track', {}) if isinstance(track_entry, dict) else {}
                
                if not track:
                    continue
                
                track_info = self._extract_track_info_full(track, position)
                if track_info:
                    playlist_data['tracks'].append(track_info)
                    position += 1
            
            data.append(playlist_data)
            logger.info(f'Плейлист "{playlist.title}": {len(playlist_data["tracks"])} треков')

        self._save(data, f'{filename}_playlists', format)
        return len(data)
    
    def export_albums(self, albums, filename: str, format: str = 'json'):
        """Экспорт альбомов."""
        data = []
        
        for album in albums:
            data.append({
                'type': 'album',
                'title': album.title,
                'artists': ', '.join([artist.name for artist in album.artists]),
                'year': album.year,
                'track_count': len(album.volumes) if album.volumes else 0,
                'genre': album.genre if hasattr(album, 'genre') else None
            })
        
        logger.info(f'Подготовлено {len(data)} альбомов для экспорта')
        self._save(data, f'{filename}_albums', format)
        return len(data)
    
    def export_artists(self, artists, filename: str, format: str = 'json'):
        """Экспорт исполнителей."""
        data = []
        
        for artist in artists:
            data.append({
                'type': 'artist',
                'name': artist.name,
                'genres': ', '.join(artist.genres) if artist.genres else None
            })
        
        logger.info(f'Подготовлено {len(data)} исполнителей для экспорта')
        self._save(data, f'{filename}_artists', format)
        return len(data)
    
    def _save(self, data: List[Dict], filename: str, format: str):
        """Сохранение данных в файл."""
        filepath = self.output_dir / f'{filename}.{format}'
        
        if format == 'json':
            self._save_json(data, filepath)
        elif format == 'csv':
            self._save_csv(data, filepath)
    
    def _save_json(self, data: List[Dict], filepath: Path):
        """Сохранение в JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f'Данные сохранены в {filepath}')
    
    def _save_csv(self, data: List[Dict], filepath: Path):
        """Сохранение в CSV."""
        if not data:
            logger.warning('Нет данных для сохранения в CSV')
            return
        
        fieldnames = list(data[0].keys())
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f'Данные сохранены в {filepath}')
