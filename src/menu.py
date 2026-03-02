"""
Модуль интерактивного меню.
"""

import logging
from typing import Tuple, Dict, List, Optional

from .yandex_client import YandexClient

logger = logging.getLogger(__name__)


class Menu:
    """Класс для отображения интерактивного меню."""

    SEPARATOR = '=' * 60
    DASH = '-' * 60

    @staticmethod
    def show_header():
        """Показать заголовок."""
        print('\n' + Menu.SEPARATOR)
        print('       ЭКСПОРТ БИБЛИОТЕКИ ЯНДЕКС.МУЗЫКИ')
        print(Menu.SEPARATOR)

    @staticmethod
    def show_main_menu() -> str:
        """Показать главное меню."""
        print('\n' + Menu.DASH)
        print('ГЛАВНОЕ МЕНЮ:')
        print(Menu.DASH)
        print('  [1] Экспорт "Мне нравится" (треки)')
        print('  [2] Экспорт плейлистов')
        print('  [3] Настройки / Информация')
        print('  [0] Выход')
        print(Menu.DASH)

        while True:
            choice = input('Ваш выбор (0-3): ').strip()

            if choice in ('0', '1', '2', '3'):
                return choice
            else:
                logger.warning(f'Пользователь ввёл неверный выбор: {choice}')
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def show_likes_menu() -> str:
        """Показать меню экспорта лайкнутых треков."""
        print('\n' + Menu.DASH)
        print('ЭКСПОРТ "МНЕ НРАВИТСЯ":')
        print(Menu.DASH)
        print('  [1] Экспортировать все треки')
        print('  [2] Экспортировать только доступные треки')
        print('  [3] Экспортировать только недоступные треки')
        print('  [4] Показать список треков')
        print('  [0] Назад')
        print(Menu.DASH)

        while True:
            choice = input('Ваш выбор (0-4): ').strip()

            if choice in ('0', '1', '2', '3', '4'):
                return choice
            else:
                logger.warning(f'Пользователь ввёл неверный выбор: {choice}')
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def show_playlists_menu() -> str:
        """Показать меню экспорта плейлистов."""
        print('\n' + Menu.DASH)
        print('ЭКСПОРТ ПЕЙЛИСТОВ:')
        print(Menu.DASH)
        print('  [1] Экспортировать все плейлисты')
        print('  [2] Выбрать плейлисты для экспорта')
        print('  [3] Показать список плейлистов')
        print('  [0] Назад')
        print(Menu.DASH)

        while True:
            choice = input('Ваш выбор (0-3): ').strip()

            if choice in ('0', '1', '2', '3'):
                return choice
            else:
                logger.warning(f'Пользователь ввёл неверный выбор: {choice}')
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def show_settings_menu(config) -> str:
        """Показать меню настроек."""
        print('\n' + Menu.DASH)
        print('НАСТРОЙКИ:')
        print(Menu.DASH)
        print(f'  Текущий формат: {config.default_format}')
        print(f'  Текущее имя файла: {config.default_filename}')
        print(Menu.DASH)
        print('  [1] Изменить формат по умолчанию')
        print('  [2] Изменить имя файла по умолчанию')
        print('  [3] Как получить токен?')
        print('  [0] Назад')
        print(Menu.DASH)

        while True:
            choice = input('Ваш выбор (0-3): ').strip()

            if choice in ('0', '1', '2', '3'):
                return choice
            else:
                logger.warning(f'Пользователь ввёл неверный выбор: {choice}')
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def show_token_help():
        """Показать инструкцию по получению токена."""
        print('\n' + Menu.SEPARATOR)
        print('КАК ПОЛУЧИТЬ ТОКЕН ЯНДЕКС.МУЗЫКИ:')
        print(Menu.SEPARATOR)
        print('\nСПОСОБ 1: Через DevTools браузера')
        print('1. Откройте https://music.yandex.ru в браузере')
        print('2. Нажмите F12 (откроется панель разработчика)')
        print('3. Перейдите на вкладку "Network" (Сеть)')
        print('4. Обновите страницу (F5)')
        print('5. В списке запросов найдите запрос к API')
        print('6. В заголовках запроса найдите "Authorization"')
        print('7. Скопируйте значение после "OAuth " (без пробела)')
        print('\nСПОСОБ 2: Через OAuth Яндекс (быстрее)')
        print('1. (Опционально) Откройте DevTools в браузере и на вкладке Network')
        print('   включите троттлинг (замедление сети)')
        print('2. Перейдите по ссылке:')
        print('   https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d')
        print('3. Авторизуйтесь при необходимости и предоставьте доступ')
        print('4. Браузер перенаправит на адрес вида:')
        print('   https://music.yandex.ru/#access_token=AQAAAAAYc***&token_type=bearer&expires_in=...')
        print('5. Редирект произойдёт быстро — нужно успеть скопировать ссылку')
        print('6. Ваш токен — это значение после "access_token=" (до "&")')
        print('\n' + Menu.SEPARATOR)

    @staticmethod
    def get_token(saved_token: str = '') -> Tuple[Optional[str], bool]:
        """Получение токена от пользователя."""
        Menu.show_header()

        if saved_token:
            print('\n[OK] Токен найден в конфигурации')
            print('  [1] Использовать сохранённый токен')
            print('  [2] Ввести новый токен')
            print('  [3] Как получить токен?')
            print(Menu.DASH)

            choice = input('Ваш выбор (1-3): ').strip()

            if choice == '2' or choice == '3':
                if choice == '3':
                    Menu.show_token_help()
                    logger.info('Пользователь выбрал: показать инструкцию по токену')

                token = input('\nВведите OAuth-токен Яндекс.Музыки: ').strip()
                if not token:
                    print('[ERROR] Токен не введён!')
                    logger.warning('Пользователь не ввёл токен')
                    return None, False
                logger.info('Пользователь ввёл новый токен')
                return token, False

            logger.info('Пользователь выбрал: использовать сохранённый токен')
            return saved_token, False

        else:
            print('\nДля получения токена:')
            print('  1. Откройте https://music.yandex.ru в браузере')
            print('  2. Нажмите F12 → вкладка Network (Сеть)')
            print('  3. Обновите страницу')
            print('  4. Найдите запрос к API')
            print('  5. Скопируйте значение заголовка Authorization')
            print('     (без слова "OAuth " в начале)')
            print(Menu.DASH)

            token = input('\nВведите OAuth-токен Яндекс.Музыки: ').strip()

            if not token:
                print('[ERROR] Токен не введён!')
                logger.warning('Пользователь не ввёл токен')
                return None, False

            save = input('\nСохранить токен в config.json? (y/n): ').strip().lower()
            if save == 'y' or save == 'д':
                logger.info('Пользователь выбрал: сохранить токен в config.json')
                return token, True

            logger.info('Пользователь ввёл токен (без сохранения)')
            return token, False

    @staticmethod
    def select_playlists_for_export(client: YandexClient) -> List[int]:
        """Выбор конкретных плейлистов для экспорта."""
        print('\n' + Menu.DASH)
        logger.info('Загрузка списка плейлистов...')

        try:
            playlists = client.get_playlists_preview()

            if not playlists:
                print('\n[EMPTY] У вас пока нет плейлистов')
                return []

            print(f'\nPLAYLISTS ({len(playlists)} шт.):')
            print(Menu.DASH)
            print(f'{"#":<3} {"Название":<35} {"Треков":<8}')
            print(Menu.DASH)

            for i, pl in enumerate(playlists, 1):
                title = pl['title'][:33] + '..' if len(pl['title']) > 35 else pl['title']
                print(f'{i:<3} {title:<35} {pl["track_count"]:<8}')

            print(Menu.DASH)
            print('\nВведите номера плейлистов для экспорта (через пробел):')
            print('(например: 1 3 5 или 0 для выбора всех)')

            while True:
                selection = input('Ваш выбор: ').strip()

                if selection == '0':
                    logger.info('Пользователь выбрал: все плейлисты')
                    return list(range(1, len(playlists) + 1))

                try:
                    indices = [int(x) for x in selection.split()]
                    invalid = [x for x in indices if x < 1 or x > len(playlists)]

                    if invalid:
                        print(f'❌ Неверные номера: {invalid}. Попробуйте снова.')
                        continue

                    if not indices:
                        print('❌ Введите хотя бы один номер.')
                        continue

                    logger.info(f'Пользователь выбрал плейлисты: {indices}')
                    return indices

                except ValueError:
                    print('❌ Введите числа, разделённые пробелом.')
                    continue

        except Exception as e:
            logger.error(f'Ошибка при загрузке плейлистов: {str(e)}')
            print('[ERROR] Не удалось загрузить плейлисты')
            return []

    @staticmethod
    def show_likes_preview(client: YandexClient):
        """Показать превью лайкнутых треков."""
        print('\n' + Menu.SEPARATOR)
        logger.info('Загрузка информации о лайкнутых треках...')

        try:
            tracks, ugc_tracks, unavailable_ids = client.get_likes_tracks()
            available_count = len(tracks)
            ugc_count = len(ugc_tracks)
            unavailable_count = len(unavailable_ids)
            total_count = available_count + ugc_count + unavailable_count

            print(f'\n"МНЕ НРАВИТСЯ":')
            print(Menu.DASH)
            print(f'   Всего треков:   {total_count}')
            print(f'   Доступно:       {available_count}')
            print(f'   UGC (ваши):     {ugc_count}')
            print(f'   Недоступно:     {unavailable_count}')
            print(Menu.DASH)

            if unavailable_count > 0:
                print(f'\n⚠️  {unavailable_count} треков недоступны для экспорта')
                print('   (удалены правообладателями)')

        except Exception as e:
            logger.error(f'Ошибка при загрузке лайков: {str(e)}')
            print('[ERROR] Не удалось загрузить данные')

    @staticmethod
    def show_playlists_preview(client: YandexClient):
        """Показать превью плейлистов."""
        print('\n' + Menu.SEPARATOR)
        logger.info('Загрузка списка плейлистов...')

        try:
            playlists = client.get_playlists_preview()

            if not playlists:
                print('\n[EMPTY] У вас пока нет плейлистов')
                return

            print(f'\nPLAYLISTS ({len(playlists)} шт.):')
            print(Menu.DASH)
            print(f'{"#":<3} {"Название":<35} {"Треков":<8}')
            print(Menu.DASH)

            for i, pl in enumerate(playlists, 1):
                title = pl['title'][:33] + '..' if len(pl['title']) > 35 else pl['title']
                print(f'{i:<3} {title:<35} {pl["track_count"]:<8}')

            print(Menu.DASH)

        except Exception as e:
            logger.error(f'Ошибка при загрузке плейлистов: {str(e)}')
            print('[ERROR] Не удалось загрузить плейлисты')

    @staticmethod
    def select_format(default_format: str = 'json') -> str:
        """Выбор формата экспорта."""
        print('\n' + Menu.DASH)
        print('ВЫБЕРИТЕ ФОРМАТ ЭКСПОРТА:')
        print(Menu.DASH)
        print(f'  [1] JSON (рекомендуется) {"[по умолчанию]" if default_format == "json" else ""}')
        print(f'  [2] CSV (табличный формат) {"[по умолчанию]" if default_format == "csv" else ""}')
        print('  [3] Сохранить выбор по умолчанию')
        print(Menu.DASH)

        while True:
            choice = input('Ваш выбор (1-3): ').strip()

            if choice == '1':
                logger.info('Пользователь выбрал: формат JSON')
                return 'json'
            elif choice == '2':
                logger.info('Пользователь выбрал: формат CSV')
                return 'csv'
            elif choice == '3':
                print('\n  [1] JSON')
                print('  [2] CSV')
                fmt_choice = input('  Какой формат сохранить по умолчанию? (1-2): ').strip()
                if fmt_choice == '1':
                    logger.info('Пользователь выбрал: сохранить формат JSON по умолчанию')
                    return 'json'
                else:
                    logger.info('Пользователь выбрал: сохранить формат CSV по умолчанию')
                    return 'csv'
            else:
                logger.warning(f'Пользователь ввёл неверный выбор формата: {choice}')
                print('❌ Неверный выбор. Попробуйте снова.')

    @staticmethod
    def get_filename(default_filename: str = 'yandex_export') -> str:
        """Получение имени файла."""
        print('\n' + Menu.DASH)
        filename = input(f'Имя файла для экспорта (Enter = {default_filename}): ').strip()
        result = filename if filename else default_filename
        logger.info(f'Пользователь ввёл имя файла: {result}')
        return result

    @staticmethod
    def show_export_start():
        """Показать начало экспорта."""
        print('\n' + Menu.SEPARATOR)
        print('НАЧАЛО ЭКСПОРТА')
        print(Menu.SEPARATOR + '\n')

    @staticmethod
    def show_export_complete(files: list):
        """Показать завершение экспорта."""
        print('\n' + Menu.SEPARATOR)
        logger.info('[OK] Экспорт завершён!')
        print(Menu.SEPARATOR)
        print(f'\n[FILES] Файлы сохранены в папке "exports":')

        for file in files:
            print(f'   - {file}')

        print('\n' + Menu.SEPARATOR)
        input('\nНажмите Enter для выхода...')
