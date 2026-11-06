import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from datetime import datetime

import config
import player
from scheduler import is_work_time
from storage import save_playlist, load_playlist


class AdPlayerApp:
    def __init__(self, root):
        self.root = root
        self.video_playlist = []
        self.manual_override = False
        self.is_paused = False  # Флаг ручной паузы

        self._build_ui()
        self._load_and_refresh()
        self._start_scheduler()

    # ---------- ПОСТРОЕНИЕ ИНТЕРФЕЙСА ----------
    def _build_ui(self):
        self.root.title("Рекламный плеер — настройка")
        self.root.geometry("700x520")

        tk.Label(self.root, text="Плейлист (ролики проигрываются по кругу):",
                 anchor="w").pack(fill="x", padx=10, pady=(10, 0))

        self.listbox = tk.Listbox(self.root, selectmode=tk.EXTENDED, height=12)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопки управления списком
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10)
        tk.Button(btn_frame, text="Добавить ролики…",
                  command=self._add_videos).pack(side="left", pady=5)
        tk.Button(btn_frame, text="Удалить выбранные",
                  command=self._remove_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Очистить всё",
                  command=self._clear_all).pack(side="left")

        # Кнопки управления показом
        show_frame = tk.Frame(self.root)
        show_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(show_frame, text="▶ Запустить показ сейчас",
                  command=self._manual_start, bg="#c8e6c9").pack(side="left")
        tk.Button(show_frame, text="⏹ Остановить показ",
                  command=self._manual_stop, bg="#ffcdd2").pack(side="left", padx=5)
        tk.Button(show_frame, text="Свернуть",
                  command=self._minimize).pack(side="left", padx=5)

        # Статус
        self.status_label = tk.Label(
            self.root,
            text="Работает расписание: 08:30–16:30, Пн–Пт (кроме праздников)",
            anchor="w", fg="gray"
        )
        self.status_label.pack(fill="x", padx=10, pady=10)

    # ---------- ПЛЕЙЛИСТ ----------
    def _load_and_refresh(self):
        self.video_playlist = load_playlist()
        self._refresh_listbox()

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for path in self.video_playlist:
            self.listbox.insert(tk.END, path)

    def _add_videos(self):
        files = filedialog.askopenfilenames(
            title="Выберите рекламные ролики",
            filetypes=[("Видео", "*.mp4 *.avi *.mkv *.mov *.wmv"), ("Все файлы", "*.*")]
        )
        for f in files:
            if f not in self.video_playlist:
                self.video_playlist.append(f)
        self._refresh_listbox()
        save_playlist(self.video_playlist)

    def _remove_selected(self):
        sel = self.listbox.curselection()
        for idx in reversed(sel):
            del self.video_playlist[idx]
        self._refresh_listbox()
        save_playlist(self.video_playlist)

    def _clear_all(self):
        if messagebox.askyesno("Подтверждение", "Удалить все ролики из списка?"):
            self.video_playlist.clear()
            self._refresh_listbox()
            save_playlist(self.video_playlist)

    # ---------- ПОКАЗ ----------
    def _manual_start(self):
        if not self.video_playlist:
            messagebox.showwarning("Нет роликов", "Сначала добавьте хотя бы один ролик.")
            return
        self.manual_override = True
        self.is_paused = False  # Снимаем паузу при ручном запуске
        player.start_vlc(self.video_playlist)
        self.status_label.config(text="▶ Показ запущен вручную (расписание игнорируется)")

    def _manual_stop(self):
        self.manual_override = False
        self.is_paused = True  # Ставим паузу, чтобы планировщик не включил видео обратно
        player.stop_vlc()
        self.status_label.config(text="⏸ Показ остановлен вручную. Автозапуск приостановлен.")

    def _minimize(self):
        self.root.iconify()

    # ---------- ПЛАНИРОВЩИК ----------
    def _start_scheduler(self):
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _scheduler_loop(self):
        while True:
            # Если стоит пауза или включен ручной режим — планировщик молчит
            if not self.is_paused and not self.manual_override:
                if is_work_time(datetime.now()):
                    player.start_vlc(self.video_playlist)
                else:
                    player.stop_vlc()
            time.sleep(config.CHECK_INTERVAL)
