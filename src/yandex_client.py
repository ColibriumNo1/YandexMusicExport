"""
Клиент для работы с Яндекс.Музыкой.
"""

import logging
import requests
from yandex_music import Client

logger = logging.getLogger(__name__)


class YandexClient:
    """Обёртка над клиентом Яндекс.Музыки."""
    
    def __init__(self, token: str):
        self.token = token
        self.client = None
    
    def init(self) -> bool:
        """Инициализация клиента."""
        try:
            self.client = Client(self.token)
            self.client.init()
            logger.info('Клиент Яндекс.Музыки инициализирован')
            return True
        except Exception as e:
            logger.error(f'Ошибка инициализации клиента: {str(e)}')
            return False

    def get_likes_tracks_raw(self) -> tuple:
        """Получение лайкнутых треков через API (ID + полные данные).
        
        Returns:
            tuple: (tracks, ugc_tracks, unavailable_ids)
        """
        try:
            # Получаем UID пользователя через client.me
            uid = self.client.me.account.uid
            
            # Правильный endpoint: /users/{uid}/likes/tracks
            url = f'https://api.music.yandex.net/users/{uid}/likes/tracks'
            
            headers = {
                'Authorization': f'OAuth {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Ответ содержит result.library.tracks
            if data.get('result') and data['result'].get('library') and 'tracks' in data['result']['library']:
                liked_tracks = data['result']['library']['tracks']
                logger.info(f'Получено {len(liked_tracks)} ID лайкнутых треков через API')
                
                # Разделяем на доступные (с album_id) и недоступные (без album_id)
                available_ids = []
                ugc_ids = []
                
                for track in liked_tracks:
                    track_id = track.get('id')
                    album_id = track.get('albumId')
                    
                    if album_id:
                        available_ids.append(f'{track_id}:{album_id}')
                    else:
                        # UGC или удалённые треки
                        ugc_ids.append(track_id)
                
                # Получаем полные данные о доступных треках через client.tracks()
                tracks = []
                if available_ids:
                    # Разбиваем на чанки по 500 (ограничение API)
                    chunk_size = 500
                    for i in range(0, len(available_ids), chunk_size):
                        chunk = available_ids[i:i + chunk_size]
                        chunk_tracks = self.client.tracks(chunk)
                        tracks.extend(chunk_tracks)
                    logger.info(f'Получено {len(tracks)} доступных треков')
                
                # Получаем UGC треки напрямую через API (чтобы обойти ошибку Artist)
                ugc_tracks = []
                invalid_ids = []
                
                if ugc_ids:
                    logger.info(f'Запрос {len(ugc_ids)} UGC треков через API...')
                    # Запрашиваем пачкой по 500
                    chunk_size = 500
                    for i in range(0, len(ugc_ids), chunk_size):
                        chunk = ugc_ids[i:i + chunk_size]
                        
                        url = 'https://api.music.yandex.net/tracks'
                        headers = {'Authorization': f'OAuth {self.token}'}
                        params = {'track-ids': ','.join(chunk)}
                        
                        response = requests.post(url, headers=headers, params=params, timeout=30)
                        if response.status_code == 200:
                            result = response.json()
                            if 'result' in result:
                                result_data = result['result']
                                track_list = result_data if isinstance(result_data, list) else [result_data]
                                
                                for track in track_list:
                                    if track and track.get('title'):
                                        ugc_tracks.append(track)
                                    else:
                                        invalid_ids.append(track.get('id', 'unknown'))
                        else:
                            logger.error(f'Ошибка получения UGC треков: {response.status_code}')
                
                logger.info(f'Загружено пользователем (UGC): {len(ugc_tracks)}')
                if invalid_ids:
                    logger.warning(f'Недоступно треков (удалены): {len(invalid_ids)}')
                
                return tracks, ugc_tracks, invalid_ids
            else:
                logger.warning('Нет лайкнутых треков в ответе API')
                return [], [], []
                
        except Exception as e:
            logger.error(f'Ошибка получения лайкнутых треков через API: {str(e)}')
            return [], [], []

    def get_likes_tracks(self):
        """Получение лайкнутых треков."""
        try:
            likes = self.client.users_likes_tracks()

            # Разделяем треки на доступные и недоступные
            available_ids = []
            unavailable_ids = []

            for track in likes.tracks:
                if track.album_id:
                    available_ids.append(f'{track.id}:{track.album_id}')
                else:
                    # Треки без album_id (UGC или удалённые)
                    unavailable_ids.append(track.id)
            
            # Получаем данные о доступных треках
            tracks = self.client.tracks(available_ids) if available_ids else []
            
            # Получаем данные о треках без album_id (UGC)
            # UGC треки запрашиваем по одному
            ugc_tracks = []
            invalid_ugc_ids = []
            
            if unavailable_ids:
                logger.info(f'Запрос {len(unavailable_ids)} UGC треков...')
                for track_id in unavailable_ids:
                    try:
                        result = self.client.tracks(track_id)
                        if result and len(result) > 0 and result[0] and result[0].title:
                            ugc_tracks.append(result[0])
                        else:
                            invalid_ugc_ids.append(track_id)
                    except Exception as e:
                        logger.debug(f'Трек {track_id}: {str(e)}')
                        invalid_ugc_ids.append(track_id)

            # Логируем статистику
            total = len(likes.tracks)
            available = len(tracks)
            ugc_count = len(ugc_tracks)
            invalid_count = len(invalid_ugc_ids)

            logger.info(f'Получено {available} лайкнутых треков из {total}')
            if ugc_count > 0:
                logger.info(f'Загружено пользователем (UGC): {ugc_count}')
            if invalid_count > 0:
                logger.warning(f'Недоступно треков (удалены): {invalid_count} ({invalid_count/total*100:.1f}%)')

            return tracks, ugc_tracks, invalid_ugc_ids
        except Exception as e:
            logger.error(f'Ошибка получения лайкнутых треков: {str(e)}')
            return [], [], []
    
    def get_playlists(self):
        """Получение плейлистов."""
        try:
            playlists = self.client.users_playlists_list()
            logger.info(f'Получено {len(playlists)} плейлистов')
            return playlists
        except Exception as e:
            logger.error(f'Ошибка получения плейлистов: {str(e)}')
            return []
    
    def get_likes_albums(self):
        """Получение лайкнутых альбомов."""
        try:
            likes = self.client.users_likes_albums()
            albums = [like.album for like in likes]
            logger.info(f'Получено {len(albums)} лайкнутых альбомов')
            return albums
        except Exception as e:
            logger.error(f'Ошибка получения лайкнутых альбомов: {str(e)}')
            return []
    
    def get_likes_artists(self):
        """Получение лайкнутых исполнителей."""
        try:
            likes = self.client.users_likes_artists()
            artists = [like.artist for like in likes]
            logger.info(f'Получено {len(artists)} лайкнутых исполнителей')
            return artists
        except Exception as e:
            logger.error(f'Ошибка получения лайкнутых исполнителей: {str(e)}')
            return []
    
    def get_likes_count(self) -> dict:
        """Получение количества лайкнутых элементов."""
        result = {'tracks': 0, 'albums': 0, 'artists': 0}
        
        try:
            likes_tracks = self.client.users_likes_tracks()
            result['tracks'] = len(likes_tracks.tracks) if likes_tracks else 0
        except:
            pass
        
        try:
            likes_albums = self.client.users_likes_albums()
            result['albums'] = len(likes_albums) if likes_albums else 0
        except:
            pass
        
        try:
            likes_artists = self.client.users_likes_artists()
            result['artists'] = len(likes_artists) if likes_artists else 0
        except:
            pass
        
        return result
    
    def get_playlists_preview(self) -> list:
        """Получение превью плейлистов."""
        result = []
        
        try:
            playlists = self.client.users_playlists_list()
            for playlist in playlists:
                track_count = playlist.track_count
                if not track_count:
                    try:
                        track_count = len(playlist.fetch_tracks())
                    except:
                        track_count = 0
                
                result.append({
                    'title': playlist.title,
                    'kind': playlist.kind,
                    'track_count': track_count
                })
        except Exception as e:
            logger.error(f'Ошибка получения превью плейлистов: {str(e)}')
        
        return result
