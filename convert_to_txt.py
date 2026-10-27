#!/usr/bin/env python3
"""
Конвертация экспорта из JSON в TXT формат.
Формат: "Исполнитель - Название трека"
"""

import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_json_to_txt(json_file: Path, txt_file: Path):
    """Конвертация одного JSON файла в TXT."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lines = []

        # Обрабатываем структуру плейлиста
        for playlist in data:
            if not isinstance(playlist, dict):
                continue

            tracks = playlist.get('tracks', [])
            for track in tracks:
                if not isinstance(track, dict):
                    continue

                artists = track.get('artists', 'Unknown')
                title = track.get('title', 'Unknown')

                # Пропускаем треки без названия
                if title == 'Unknown' or not title:
                    continue

                lines.append(f'{artists} - {title}')

        # Сохраняем TXT
        txt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            if lines:
                f.write('\n')

        logger.info(f'Конвертировано {len(lines)} треков: {json_file.name} → {txt_file.name}')
        return len(lines)

    except Exception as e:
        logger.error(f'Ошибка конвертации {json_file}: {str(e)}')
        return 0


def convert_directory(json_dir: Path, txt_dir: Path):
    """Конвертация всех JSON файлов в директории."""
    if not json_dir.exists():
        logger.error(f'Папка не найдена: {json_dir}')
        return

    # Создаём папку txt
    txt_dir.mkdir(exist_ok=True)

    total_tracks = 0
    converted_files = 0

    # Находим все JSON файлы
    json_files = list(json_dir.glob('*.json'))

    if not json_files:
        logger.warning(f'Нет JSON файлов в папке {json_dir}')
        return

    logger.info(f'Найдено {len(json_files)} JSON файлов')

    for json_file in json_files:
        txt_file = txt_dir / f'{json_file.stem}.txt'
        tracks_count = convert_json_to_txt(json_file, txt_file)
        total_tracks += tracks_count
        if tracks_count > 0:
            converted_files += 1

    logger.info(f'Готово! Конвертировано {converted_files} файлов, {total_tracks} треков')
    logger.info(f'Файлы сохранены в: {txt_dir}')


def main():
    """Основная функция."""
    print('\n' + '=' * 60)
    print('       КОНВЕРТАЦИЯ JSON → TXT')
    print('=' * 60 + '\n')

    # Путь к папке exports
    exports_dir = Path(__file__).parent / 'exports'

    if not exports_dir.exists():
        print('[ERROR] Папка exports не найдена')
        return

    # Находим папки пользователей
    user_dirs = [d for d in exports_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not user_dirs:
        print('[ERROR] Нет папок пользователей в exports/')
        return

    print(f'Найдено пользователей: {len(user_dirs)}\n')

    for user_dir in user_dirs:
        json_dir = user_dir / 'json'

        if not json_dir.exists():
            logger.warning(f'Нет папки json у пользователя {user_dir.name}')
            continue

        txt_dir = user_dir / 'txt'

        print(f'\n[{user_dir.name}]')
        convert_directory(json_dir, txt_dir)

    print('\n' + '=' * 60)
    print('Конвертация завершена!')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
