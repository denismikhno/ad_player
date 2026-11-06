import os

# Расписание
START_HOUR, START_MINUTE = 8, 30
END_HOUR, END_MINUTE = 16, 30
WORKDAYS = [0, 1, 2, 3, 4]  # Пн=0 ... Пт=4

# Пути
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYLIST_FILE = os.path.join(SCRIPT_DIR, "playlist.json")

# Интервал проверки расписания (секунды)
CHECK_INTERVAL = 15
