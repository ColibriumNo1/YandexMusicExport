"""
Вспомогательные утилиты.
"""

import logging

logger = logging.getLogger(__name__)


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def truncate_string(s: str, max_length: int = 35) -> str:
    """Обрезать строку до максимальной длины."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 2] + '..'


def format_table_row(columns: list, widths: list) -> str:
    """Форматировать строку таблицы."""
    row = ''
    for col, width in zip(columns, widths):
        row += f'{str(col):<{width}} '
    return row.strip()
