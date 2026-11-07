import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from datetime import datetime

import config
import player
from scheduler import is_work_time, load_calendar_from_file
from storage import save_playlist, load_playlist


class AdPlayerApp:
    def __init__(self, root):
        self.root = root
        self.video_playlist = []
        self.manual_override = False
        self.is_paused = False

        self._build_ui()
        self._load_and_refresh()
        self._load_calendar_on_start()
        self._start_scheduler()

    # ---------- ПОСТРОЕНИЕ ИНТЕРФЕЙСА ----------
    def _build_ui(self):
        self.root.title("AD плеер")
        self.root.geometry("750x600")

        tk.Label(self.root, text="Плейлист:",
                 anchor="w").pack(fill="x", padx=10, pady=(10, 0))

        self.listbox = tk.Listbox(self.root, selectmode=tk.EXTENDED, height=10)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Блок настройки времени ---
        time_frame = tk.LabelFrame(self.root, text="Расписание работы", padx=10, pady=5)
        time_frame.pack(fill="x", padx=10, pady=5)
        
        # Начало работы
        tk.Label(time_frame, text="Начало:").pack(side="left")
        self.start_hour_entry = tk.Entry(time_frame, width=3)
        self.start_hour_entry.insert(0,  f"{config.START_HOUR:02d}")
        self.start_hour_entry.pack(side="left")
        tk.Label(time_frame, text=":").pack(side="left")
        self.start_min_entry = tk.Entry(time_frame, width=3)
        self.start_min_entry.insert(0, f"{config.START_MINUTE:02d}")
        self.start_min_entry.pack(side="left")
        
        # Конец работы
        tk.Label(time_frame, text="   Конец:").pack(side="left")
        self.end_hour_entry = tk.Entry(time_frame, width=3)
        self.end_hour_entry.insert(0, f"{config.END_HOUR:02d}")
        self.end_hour_entry.pack(side="left")
        tk.Label(time_frame, text=":").pack(side="left")
        self.end_min_entry = tk.Entry(time_frame, width=3)
        self.end_min_entry.insert(0, f"{config.END_MINUTE:02d}")
        self.end_min_entry.pack(side="left")
        
        tk.Button(time_frame, text="💾 Сохранить время", 
                  command=self._save_time_settings, bg="#e0e0e0").pack(side="left", padx=20)

        # Кнопки управления списком
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="Добавить ролики…",
                  command=self._add_videos).pack(side="left")
        tk.Button(btn_frame, text="Удалить выбранные",
                  command=self._remove_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Очистить всё",
                  command=self._clear_all).pack(side="left")

        # Кнопки управления показом
        show_frame = tk.Frame(self.root)
        show_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(show_frame, text="▶ Запустить сейчас",
                  command=self._manual_start, bg="#c8e6c9").pack(side="left")
        tk.Button(show_frame, text="⏹ Остановить",
                  command=self._manual_stop, bg="#ffcdd2").pack(side="left", padx=5)
        tk.Button(show_frame, text="🔄 Вернуть по расписанию",
                  command=self._reset_to_schedule, bg="#bbdefb").pack(side="left", padx=5)
        tk.Button(show_frame, text="Свернуть",
                  command=self._minimize).pack(side="left", padx=5)

        # Статус
        self.status_label = tk.Label(
            self.root,
            text="Работает расписание",
            anchor="w", fg="gray"
        )
        self.status_label.pack(fill="x", padx=10, pady=10)

    # ---------- СОХРАНЕНИЕ ВРЕМЕНИ В CONFIG.PY ----------
    def _save_time_settings(self):
        try:
            sh = int(self.start_hour_entry.get())
            sm = int(self.start_min_entry.get())
            eh = int(self.end_hour_entry.get())
            em = int(self.end_min_entry.get())
            
            if not (0 <= sh < 24 and 0 <= sm < 60 and 0 <= eh < 24 and 0 <= em < 60):
                raise ValueError("Некорректное время")
                
            config_path = os.path.join(config.SCRIPT_DIR, "config.py")
            with open(config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Флаги, чтобы понять, нашли ли мы нужные строки
            found_start_h, found_start_m = False, False
            found_end_h, found_end_m = False, False
            
            new_lines = []
            for line in lines:
                if line.startswith("START_HOUR"):
                    new_lines.append(f"START_HOUR = {sh}\n")
                    found_start_h = True
                elif line.startswith("START_MINUTE"):
                    new_lines.append(f"START_MINUTE = {sm}\n")
                    found_start_m = True
                elif line.startswith("END_HOUR"):
                    new_lines.append(f"END_HOUR = {eh}\n")
                    found_end_h = True
                elif line.startswith("END_MINUTE"):
                    new_lines.append(f"END_MINUTE = {em}\n")
                    found_end_m = True
                else:
                    new_lines.append(line)
            
            # Если какой-то строки не было в файле, добавляем её принудительно
            if not found_start_h or not found_start_m or not found_end_h or not found_end_m:
                # Ищем место, куда вставить (после строки "# Расписание")
                insert_idx = 0
                for i, line in enumerate(new_lines):
                    if "# Расписание" in line:
                        insert_idx = i + 1
                        break
                
                # Вставляем недостающие строки
                if not found_start_h: new_lines.insert(insert_idx, f"START_HOUR = {sh}\n")
                if not found_start_m: new_lines.insert(insert_idx + 1, f"START_MINUTE = {sm}\n")
                if not found_end_h: new_lines.insert(insert_idx + 2, f"END_HOUR = {eh}\n")
                if not found_end_m: new_lines.insert(insert_idx + 3, f"END_MINUTE = {em}\n")

            with open(config_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            # Обновляем в памяти
            config.START_HOUR = sh
            config.START_MINUTE = sm
            config.END_HOUR = eh
            config.END_MINUTE = em
            
            self.status_label.config(
                text=f"✅ Время сохранено: {sh:02d}:{sm:02d} – {eh:02d}:{em:02d}", 
                fg="blue"
            )
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа!\nЧасы: 0-23\nМинуты: 0-59")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

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
        self.is_paused = False
        player.start_vlc(self.video_playlist)
        self.status_label.config(text="▶ Показ запущен вручную (расписание игнорируется)", fg="black")

    def _manual_stop(self):
        self.manual_override = False
        self.is_paused = True
        player.stop_vlc()
        self.status_label.config(text="⏸ Показ остановлен вручную. Автозапуск приостановлен.", fg="red")

    def _reset_to_schedule(self):
        self.manual_override = False
        self.is_paused = False
        if is_work_time(datetime.now()):
            player.start_vlc(self.video_playlist)
            self.status_label.config(text="▶ Управление возвращено расписанию (сейчас рабочее время)", fg="green")
        else:
            player.stop_vlc()
            self.status_label.config(text="⏹ Управление возвращено расписанию (сейчас нерабочее время)", fg="gray")

    def _minimize(self):
        self.root.iconify()

    # ---------- КАЛЕНДАРЬ И ПЛАНИРОВЩИК ----------
    def _load_calendar_on_start(self):
        loaded_year = load_calendar_from_file()
        
        if loaded_year is None:
            messagebox.showwarning(
                "Календарь не найден", 
                "Файл calendar.json не найден в папке программы.\n\n"
                "Праздничные и сокращенные дни учитываться не будут.\n"
                "Скачайте его по ссылке:\n"
                "https://xmlcalendar.ru\n"
                "и положите рядом с программой."
            )
            self.status_label.config(text="Внимание: Календарь не загружен (работаем без праздников)", fg="red")
        else:
            # Подставляем год в текст
            self.status_label.config(
                text=f"Календарь на {loaded_year} год загружен. Работает расписание.", 
                fg="gray"
            )

    def _start_scheduler(self):
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _scheduler_loop(self):
        while True:
            if not self.is_paused and not self.manual_override:
                if is_work_time(datetime.now()):
                    player.start_vlc(self.video_playlist)
                else:
                    player.stop_vlc()
            time.sleep(config.CHECK_INTERVAL)