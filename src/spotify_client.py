"""
Клиент для работы с Spotify API.
"""

import logging
import time
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Обёртка над клиентом Spotify."""

    REDIRECT_URI = 'http://127.0.0.1:8888/callback'
    SCOPE = 'playlist-modify-public playlist-modify-private user-library-modify user-follow-modify ugc-image-upload'
    BATCH_SIZE = 100  # Максимальное количество треков за один запрос

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        """
        Инициализация клиента Spotify.

        Args:
            client_id: Client ID приложения Spotify
            client_secret: Client Secret приложения Spotify
            redirect_uri: URI для перенаправления (по умолчанию 127.0.0.1:8888)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or self.REDIRECT_URI
        self.client = None
        self.user_id = None

    def init(self) -> bool:
        """
        Инициализация клиента Spotify.

        Returns:
            True если успешно, иначе False
        """
        try:
            self.client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.SCOPE
            ))

            # Получаем ID пользователя
            user = self.client.current_user()
            self.user_id = user['id']

            logger.info(f'Spotify клиент инициализирован (пользователь: {self.user_id})')
            return True

        except Exception as e:
            logger.error(f'Ошибка инициализации Spotify клиента: {str(e)}')
            return False

    def get_user_playlists(self) -> List[Dict]:
        """
        Получение списка плейлистов пользователя.

        Returns:
            Список плейлистов
        """
        try:
            playlists = []
            results = self.client.current_user_playlists(limit=50)

            for playlist in results['items']:
                playlists.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'tracks_count': playlist['tracks']['total']
                })

            # Получаем остальные плейлисты если есть
            while results['next']:
                results = self.client.next(results)
                for playlist in results['items']:
                    playlists.append({
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'tracks_count': playlist['tracks']['total']
                    })

            logger.info(f'Получено {len(playlists)} плейлистов')
            return playlists

        except Exception as e:
            logger.error(f'Ошибка получения плейлистов: {str(e)}')
            return []

    def create_playlist(self, name: str, description: str = '') -> str:
        """
        Создание плейлиста.

        Args:
            name: Название плейлиста
            description: Описание

        Returns:
            ID созданного плейлиста
        """
        try:
            playlist = self.client.user_playlist_create(
                user=self.user_id,
                name=name,
                public=True,
                description=description
            )

            logger.info(f'Создан плейлист: {name} (ID: {playlist["id"]})')
            return playlist['id']

        except Exception as e:
            logger.error(f'Ошибка создания плейлиста: {str(e)}')
            raise

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]):
        """
        Добавление треков в плейлист.

        Args:
            playlist_id: ID плейлиста
            track_uris: Список URI треков
        """
        try:
            # Добавляем треки порциями
            for i in range(0, len(track_uris), self.BATCH_SIZE):
                batch = track_uris[i:i + self.BATCH_SIZE]
                self.client.playlist_add_items(playlist_id, batch)
                logger.info(f'Добавлено {len(batch)} треков в плейлист {playlist_id}')
                time.sleep(0.1)  # Задержка для избежания rate limiting

        except Exception as e:
            logger.error(f'Ошибка добавления треков: {str(e)}')
            raise

    def search_track(self, title: str, artist: str, album: str = '') -> Optional[str]:
        """
        Поиск трека в Spotify.

        Args:
            title: Название трека
            artist: Исполнитель
            album: Альбом (опционально)

        Returns:
            URI трека или None если не найден
        """
        try:
            # Различные варианты поисковых запросов
            search_queries = [
                f'track:"{title}" artist:"{artist}"',
                f'"{title}" "{artist}"',
                f'{title} {artist}'
            ]

            # Добавляем поиск по альбому если указан
            if album:
                search_queries.insert(1, f'track:"{title}" artist:"{artist}" album:"{album}"')

            for query in search_queries:
                results = self.client.search(q=query, type='track', limit=10)

                if results['tracks']['items']:
                    # Ищем наилучшее совпадение
                    best_match = self._find_best_match(title, artist, results['tracks']['items'])

                    if best_match:
                        return best_match['uri']

            return None

        except Exception as e:
            logger.debug(f'Ошибка поиска трека "{title}" - "{artist}": {str(e)}')
            return None

    def _find_best_match(self, target_title: str, target_artist: str,
                         candidates: List[Dict]) -> Optional[Dict]:
        """
        Поиск наилучшего совпадения среди кандидатов.

        Args:
            target_title: Целевое название трека
            target_artist: Целевой исполнитель
            candidates: Список кандидатов из Spotify

        Returns:
            Наиболее подходящий трек или None
        """
        best_score = 0
        best_match = None

        target_title_lower = target_title.lower()
        target_artist_lower = target_artist.lower()

        for track in candidates:
            # Сравниваем название
            title_similarity = SequenceMatcher(
                None, target_title_lower, track['name'].lower()
            ).ratio()

            # Сравниваем исполнителя
            track_artists = [a['name'].lower() for a in track['artists']]
            artist_similarity = max([
                SequenceMatcher(None, target_artist_lower, artist).ratio()
                for artist in track_artists
            ], default=0)

            # Общий скор (название важнее)
            total_score = title_similarity * 0.7 + artist_similarity * 0.3

            # Минимальный порог совпадения
            if total_score > best_score and total_score > 0.6:
                best_score = total_score
                best_match = track

        return best_match

    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """
        Получение треков из плейлиста.

        Args:
            playlist_id: ID плейлиста

        Returns:
            Список URI треков
        """
        try:
            track_uris = []
            results = self.client.playlist_items(playlist_id)

            for item in results['items']:
                if item['track'] and item['track']['uri']:
                    track_uris.append(item['track']['uri'])

            # Получаем остальные треки если есть
            while results['next']:
                results = self.client.next(results)
                for item in results['items']:
                    if item['track'] and item['track']['uri']:
                        track_uris.append(item['track']['uri'])

            logger.info(f'Получено {len(track_uris)} треков из плейлиста')
            return track_uris

        except Exception as e:
            logger.error(f'Ошибка получения треков из плейлиста: {str(e)}')
            return []
