import os
import pathlib
import subprocess
import threading
from datetime import datetime


vlc_process = None
_vlc_lock = threading.Lock()


def start_vlc(video_playlist):
    global vlc_process
    with _vlc_lock:
        if vlc_process is not None and vlc_process.poll() is None:
            return
        if not video_playlist:
            return
        
        # Преобразуем обычные пути в URI (file:///...)
        uris = [pathlib.Path(path).as_uri() for path in video_playlist]
            
        print(f"[{datetime.now():%H:%M:%S}] Старт показа: {uris}")
        
        vlc_process = subprocess.Popen([
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            "--fullscreen",
            "--loop",
            "--no-video-title-show",
            "--no-one-instance",
            *uris  # Передаём уже преобразованные URI
        ])


def stop_vlc():
    """Останавливает VLC (жестко)."""
    global vlc_process
    with _vlc_lock:
        if vlc_process is not None:
            print(f"[{datetime.now():%H:%M:%S}] Стоп показа")
            try:
                # Сначала пробуем мягко
                vlc_process.terminate()
                vlc_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Если не вышло — убиваем
                vlc_process.kill()
            except Exception as e:
                print(f"Ошибка при остановке: {e}")
            
            vlc_process = None
            
        # Дополнительная страховка для Windows:
        # Если VLC все еще работает в фоне, убиваем его через taskkill
        if os.name == 'nt':  # Если ОС - Windows
            try:
                # Флаг /F означает принудительное завершение, /IM - по имени образа
                subprocess.run(["taskkill", "/F", "/IM", "vlc.exe"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            except Exception:
                pass


def is_running():
    return vlc_process is not None and vlc_process.poll() is None
