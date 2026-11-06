import json
import os
from config import PLAYLIST_FILE


def save_playlist(video_playlist):
    try:
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(video_playlist, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения плейлиста: {e}")


def load_playlist():
    """Возвращает список существующих файлов из сохранённого плейлиста."""
    if not os.path.exists(PLAYLIST_FILE):
        return []
    try:
        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = [p for p in data if os.path.isfile(p)]
        missing = len(data) - len(existing)
        if missing:
            print(f"Пропущено {missing} отсутствующих файлов.")
        return existing
    except Exception as e:
        print(f"Ошибка загрузки плейлиста: {e}")
        return []
    