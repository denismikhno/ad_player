import json
import os
from datetime import datetime, date
import config

# Глобальные кэши
_holidays_cache = set()       # Множество нерабочих дней (праздники, выходные)
_short_days_cache = set()     # Множество сокращенных дней (предпраздничные)

def load_calendar_from_file():
    """Загружает данные из файла calendar.json в папке программы."""
    global _holidays_cache, _short_days_cache
    
    calendar_file = os.path.join(config.SCRIPT_DIR, "calendar.json")
    
    if not os.path.exists(calendar_file):
        print(f"[Календарь] Файл {calendar_file} не найден. Работаем без учета праздников.")
        return None  # <-- Возвращаем None, если файла нет

    try:
        with open(calendar_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        holidays = set()
        short_days = set()
        year = data.get("year")  # <-- Берем год из файла
        
        # ... (цикл парсинга остается без изменений) ...
        
        _holidays_cache = holidays
        _short_days_cache = short_days
        print(f"[Календарь] Успешно загружен файл на {year} год. Выходных: {len(holidays)}, Сокращенных: {len(short_days)}")
        return year  # <-- Возвращаем год при успехе
        
    except Exception as e:
        print(f"[Календарь] Ошибка чтения файла {calendar_file}: {e}")
        return None

def is_work_time(now: datetime) -> bool:
    """Проверяет, нужно ли сейчас показывать рекламу."""
    # 1. Проверка дня недели (Пн-Пт)
    if now.weekday() not in config.WORKDAYS:
        return False
        
    # 2. Проверка на праздник/выходной (если календарь загружен)
    if now.date() in _holidays_cache:
        return False
        
    # 3. Проверка времени с учетом сокращенных дней
    end_hour = config.END_HOUR
    end_minute = config.END_MINUTE
    
    # Если сегодня сокращенный день, вычитаем 1 час из времени окончания
    if now.date() in _short_days_cache:
        end_minutes_total = end_hour * 60 + end_minute - 60
        if end_minutes_total < 0:
            end_minutes_total = 0 
            
        end_hour = end_minutes_total // 60
        end_minute = end_minutes_total % 60
        
    start = now.replace(hour=config.START_HOUR, minute=config.START_MINUTE, second=0, microsecond=0)
    end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    return start <= now < end