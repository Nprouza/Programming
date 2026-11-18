"""Harvest — a small, polished calorie tracker built with Python's Tkinter."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import date, datetime
import base64
import json
import mimetypes
import os
import subprocess
import threading
import urllib.error
import urllib.request


BG = "#0b0d0f"
PANEL = "#15181b"
PANEL_2 = "#1d2125"
TEXT = "#f1f3f5"
MUTED = "#929aa3"
ORANGE = "#b9c2ca"
GREEN = "#d7dde3"
DEEP_GREEN = "#20262b"
LINE = "#30363b"


class RoundedFrame(tk.Frame):
    """A frame with a smooth-looking rounded border on Tkinter canvases."""

    def __init__(self, master, radius=18, fill=PANEL, border=LINE, padx=0, pady=0, **kwargs):
        super().__init__(master, bg=BG, highlightthickness=0, **kwargs)
        self.radius = radius
        self.fill = fill
        self.border = border
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.content = tk.Frame(self.canvas, bg=fill, padx=padx, pady=pady, highlightthickness=0)
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", self._redraw)

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, fill, outline):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=24,
                                          fill=fill, outline=outline, width=1)

    def _redraw(self, event):
        self.canvas.delete("shape")
        radius = min(self.radius, event.width // 3, event.height // 3)
        shape = self._rounded_rectangle(1, 1, event.width - 2, event.height - 2,
                                         radius, self.fill, self.border)
        self.canvas.addtag_withtag("shape", shape)
        self.canvas.lower("shape")
        self.canvas.coords(self.window, 1, 1)
        self.canvas.itemconfigure(self.window, width=max(2, event.width - 2),
                                  height=max(2, event.height - 2))


class CalorieTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Harvest · Daily food journal")
        self.root.geometry("1180x820")
        self.root.minsize(900, 680)
        self.root.configure(bg=BG)
        self.entries = [
            {"name": "Avocado toast", "detail": "2 slices · 8:15 AM", "meal": "Breakfast", "calories": 340, "icon": "🥑"},
            {"name": "Greek yogurt bowl", "detail": "Berries & honey · 8:30 AM", "meal": "Breakfast", "calories": 280, "icon": "🍓"},
            {"name": "Chicken grain bowl", "detail": "Brown rice · 12:40 PM", "meal": "Lunch", "calories": 520, "icon": "🥗"},
        ]
        self.goal = 2200
        self.photo_path = None
        self.photo_estimate = None
        self._style()
        self._build()
        self._refresh()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Harvest.Horizontal.TProgressbar", troughcolor=LINE, background=GREEN,
                        bordercolor=LINE, lightcolor=GREEN, darkcolor=GREEN, thickness=12)
        style.configure("Harvest.TCombobox", fieldbackground=PANEL_2, background=PANEL_2,
                        foreground=TEXT, arrowcolor=GREEN, bordercolor=LINE, padding=8)

    def _label(self, parent, text, size=12, color=TEXT, weight="normal", **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")), fg=color,
                        font=("Avenir Next", size, weight), **kwargs)

    def _build(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True, padx=36, pady=23)
        header = tk.Frame(shell, bg=BG)
        header.pack(fill="x", pady=(0, 25))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self._label(brand, "✳", 24, ORANGE, "bold").pack(side="left", padx=(0, 8))
        self._label(brand, "harvest", 22, DEEP_GREEN, "bold").pack(side="left")
        self._label(header, "FOOD JOURNAL", 9, MUTED, "bold").pack(side="left", padx=16, pady=(8, 0))
        date_badge = tk.Label(header, text="  " + date.today().strftime("%A  ·  %B %d") + "  ",
                              bg=PANEL, fg=TEXT, font=("Avenir Next", 10, "bold"), padx=10, pady=7)
        date_badge.pack(side="right", pady=(2, 0))

        title = tk.Frame(shell, bg=BG)
        title.pack(fill="x", pady=(0, 20))
        self._label(title, "A good day starts with good choices.", 25, TEXT, "bold").pack(anchor="w")
        self._label(title, "Your food, your pace. Keep track of what feels good.", 11, MUTED).pack(anchor="w", pady=(4, 0))

        cards = tk.Frame(shell, bg=BG)
        cards.pack(fill="x", pady=(0, 18))
        cards.grid_columnconfigure(0, weight=7, uniform="summary")
        cards.grid_columnconfigure(1, weight=3, uniform="summary")
        self.cal_card = RoundedFrame(cards, radius=22, fill=DEEP_GREEN, border=LINE, padx=25, pady=20)
        self.cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        copy = tk.Frame(self.cal_card.content, bg=DEEP_GREEN)
        copy.pack(side="left", fill="both", expand=True)
        self._label(copy, "TODAY’S CALORIE BUDGET", 9, MUTED, "bold", bg=DEEP_GREEN).pack(anchor="w")
        value_line = tk.Frame(copy, bg=DEEP_GREEN)
        value_line.pack(anchor="w", pady=(5, 0))
        self.cal_value = self._label(value_line, "", 39, TEXT, "bold", bg=DEEP_GREEN)
        self.cal_value.pack(side="left")
        self._label(value_line, " kcal left", 12, MUTED, bg=DEEP_GREEN).pack(side="left", padx=(7, 0), pady=(16, 0))
        self.cal_note = self._label(copy, "", 10, MUTED, bg=DEEP_GREEN)
        self.cal_note.pack(anchor="w", pady=(2, 13))
        self.progress = ttk.Progressbar(copy, style="Harvest.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x", pady=(0, 7))
        progress_legend = tk.Frame(copy, bg=DEEP_GREEN)
        progress_legend.pack(fill="x")
        self.progress_note = self._label(progress_legend, "", 9, MUTED, "bold", bg=DEEP_GREEN)
        self.progress_note.pack(side="left")
        self._label(progress_legend, f"Daily goal  ·  {self.goal:,} kcal", 9, MUTED, bg=DEEP_GREEN).pack(side="right")
        ring = tk.Canvas(self.cal_card.content, width=112, height=112, bg=DEEP_GREEN, highlightthickness=0)
        ring.pack(side="right", padx=(20, 2))
        ring.create_oval(9, 9, 103, 103, outline=LINE, width=8)
        self.ring_arc = ring.create_arc(9, 9, 103, 103, start=90, extent=-100,
                                        style="arc", outline=ORANGE, width=8)
        self.ring_text = ring.create_text(56, 52, text="0%", fill=TEXT,
                                          font=("Segoe UI", 17, "bold"))
        ring.create_text(56, 72, text="EATEN", fill=MUTED, font=("Segoe UI", 7, "bold"))
        self.cal_ring = ring

        water = RoundedFrame(cards, radius=18, fill=PANEL, border=LINE, padx=19, pady=18)
        water.grid(row=0, column=1, sticky="nsew")
        water_head = tk.Frame(water.content, bg=PANEL)
        water_head.pack(fill="x")
        self._label(water_head, "WATER", 9, MUTED, "bold").pack(side="left")
        self._label(water_head, "💧", 16, GREEN).pack(side="right")
        self.water_count = 5
        self.water_value = self._label(water.content, str(self.water_count), 31, TEXT, "bold")
        self.water_value.pack(anchor="w", pady=(7, 0))
        self._label(water.content, "glasses today", 10, MUTED).pack(anchor="w")
        self.water_bar = self._mini_bar(water.content, 62, ORANGE)
        tk.Button(water.content, text="＋  Add water", command=self._add_water, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, activeforeground=TEXT, relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2").pack(anchor="w", pady=(3, 0))

        body = tk.Frame(shell, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)
        log = RoundedFrame(body, radius=18, fill=PANEL, border=LINE, padx=22, pady=20)
        log.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        top = tk.Frame(log.content, bg=PANEL)
        top.pack(fill="x", pady=(0, 12))
        self._label(top, "Today’s meals", 16, TEXT, "bold").pack(side="left")
        self.count_label = self._label(top, "", 10, MUTED)
        self.count_label.pack(side="right", pady=4)
        self.entries_frame = tk.Frame(log.content, bg=PANEL)
        self.entries_frame.pack(fill="both", expand=True)

        add = RoundedFrame(body, radius=18, fill=PANEL, border=LINE, padx=20, pady=20)
        add.grid(row=0, column=1, sticky="nsew")
        self._label(add.content, "Add a meal", 16, TEXT, "bold").pack(anchor="w")
        self._label(add.content, "Take a photo for a quick calorie estimate.", 10, MUTED, wraplength=280, justify="left").pack(anchor="w", pady=(4, 14))
        self.photo_status = tk.Label(add.content, text="📷\n\nYour meal goes here", bg=PANEL_2,
                                     fg=MUTED, font=("Segoe UI", 10), justify="center", height=6,
                                     relief="flat", wraplength=260, highlightthickness=1, highlightbackground=LINE)
        self.photo_status.pack(fill="x", pady=(0, 12))
        photo_buttons = tk.Frame(add.content, bg=PANEL)
        photo_buttons.pack(fill="x", pady=(0, 12))
        tk.Button(photo_buttons, text="Browse photos", command=self._choose_photo, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, activeforeground=TEXT, relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=9, pady=7, cursor="hand2").pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(photo_buttons, text="Take photo", command=self._take_photo, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, activeforeground=TEXT, relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=9, pady=7, cursor="hand2").pack(side="left", expand=True, fill="x", padx=(4, 0))
        self.analyze_button = tk.Button(add.content, text="✦  Analyze my meal", command=self._analyze_photo, bg=TEXT, fg=BG,
                  activebackground=ORANGE, activeforeground=BG, relief="flat", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=10, pady=9, cursor="hand2", state="disabled")
        self.analyze_button.pack(fill="x")
        self.result_frame = tk.Frame(add.content, bg=PANEL_2, padx=12, pady=10)
        self.result_frame.pack(fill="x", pady=(12, 0))
        self.result_title = self._label(self.result_frame, "", 11, TEXT, "bold", wraplength=260, justify="left", bg=PANEL_2)
        self.result_title.pack(anchor="w")
        self.result_detail = self._label(self.result_frame, "", 9, MUTED, wraplength=260, justify="left", bg=PANEL_2)
        self.result_detail.pack(anchor="w", pady=(3, 8))
        self.meal_var = tk.StringVar(value="Snack")
        self._label(add.content, "MEAL", 9, MUTED, "bold").pack(anchor="w", pady=(9, 5))
        meal = ttk.Combobox(add.content, textvariable=self.meal_var, values=["Breakfast", "Lunch", "Dinner", "Snack"],
                            state="readonly", style="Harvest.TCombobox", font=("Avenir Next", 10))
        meal.pack(fill="x", ipady=4, pady=(0, 10))
        self.add_photo_button = tk.Button(add.content, text="＋  Add estimated meal", command=self._add_estimated_food, bg=ORANGE, fg=BG,
                  activebackground=TEXT, activeforeground=BG, relief="flat", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=10, pady=9, cursor="hand2", state="disabled")
        self.add_photo_button.pack(fill="x")
        self._label(add.content, "Estimates are approximate. Portion size and hidden ingredients can change the actual calories.",
                    8, MUTED, wraplength=300, justify="left").pack(anchor="w", pady=(10, 0))
        self._label(shell, "Made for mindful meals  ·  ✳", 9, MUTED).pack(anchor="center", pady=(12, 0))

    def _card(self, parent, col):
        frame = tk.Frame(parent, bg=PANEL, padx=18, pady=16, highlightthickness=1, highlightbackground=LINE)
        frame.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 8 if col < 2 else 0))
        return frame

    def _mini_bar(self, parent, value, color):
        bar = tk.Canvas(parent, height=5, bg=LINE, highlightthickness=0)
        bar.pack(fill="x", pady=(14, 8))
        bar.bind("<Configure>", lambda event: (bar.delete("all"), bar.create_rectangle(0, 0, event.width * value / 100, 5, fill=color, width=0)))
        return bar

    @staticmethod
    def _update_mini_bar(bar, value, color):
        width = bar.winfo_width()
        bar.delete("all")
        if width > 1:
            bar.create_rectangle(0, 0, width * min(100, max(0, value)) / 100, 5, fill=color, width=0)

    def _entry(self, parent, variable, hint):
        entry = tk.Entry(parent, textvariable=variable, bg=PANEL_2, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, font=("Avenir Next", 10))
        entry.insert(0, hint)
        entry.config(fg=MUTED)
        entry.bind("<FocusIn>", lambda _e: self._clear_hint(entry, hint))
        entry.bind("<FocusOut>", lambda _e: self._restore_hint(entry, variable, hint))
        entry._hint = hint
        return entry

    @staticmethod
    def _clear_hint(entry, hint):
        if entry.get() == hint:
            entry.delete(0, "end")
            entry.config(fg=TEXT)

    @staticmethod
    def _restore_hint(entry, variable, hint):
        if not variable.get():
            entry.insert(0, hint)
            entry.config(fg=MUTED)

    def _refresh(self):
        total = sum(item["calories"] for item in self.entries)
        remaining = self.goal - total
        progress_percent = min(100, max(0, total / self.goal * 100))
        self.cal_value.config(text=f"{max(0, remaining):,}")
        self.cal_note.config(text=f"kcal remaining · {total:,} eaten")
        self.progress["value"] = progress_percent
        self.cal_ring.itemconfigure(self.ring_arc, extent=-3.6 * progress_percent)
        self.cal_ring.itemconfigure(self.ring_text, text=f"{round(progress_percent)}%")
        self.progress_note.config(text=f"{remaining:,} kcal left" if remaining >= 0 else f"{abs(remaining):,} kcal over goal")
        self.count_label.config(text=f"{len(self.entries)} items logged")
        for child in self.entries_frame.winfo_children():
            child.destroy()
        if not self.entries:
            self._label(self.entries_frame, "Nothing logged yet. Add your first bite →", 11, MUTED).pack(anchor="w", pady=14)
        meal_order = ["Breakfast", "Lunch", "Dinner", "Snack"]
        for meal_name in meal_order:
            group = [(i, item) for i, item in enumerate(self.entries) if item.get("meal", "Snack") == meal_name]
            if not group:
                continue
            subtotal = sum(item["calories"] for _, item in group)
            heading = tk.Frame(self.entries_frame, bg=PANEL)
            heading.pack(fill="x", pady=(12, 3))
            self._label(heading, meal_name, 11, GREEN, "bold").pack(side="left")
            self._label(heading, f"{subtotal} kcal", 9, MUTED, "bold").pack(side="right")
            for index, item in group:
                row = tk.Frame(self.entries_frame, bg=PANEL)
                row.pack(fill="x", pady=6)
                self._label(row, item["icon"], 17, TEXT).pack(side="left", padx=(0, 10))
                words = tk.Frame(row, bg=PANEL)
                words.pack(side="left", fill="x", expand=True)
                self._label(words, item["name"], 10, TEXT, "bold").pack(anchor="w")
                self._label(words, item["detail"], 9, MUTED).pack(anchor="w", pady=(2, 0))
                self._label(row, f"{item['calories']} kcal", 9, TEXT, "bold").pack(side="right", padx=(5, 6))
                tk.Button(row, text="×", command=lambda i=index: self._remove(i), bg=PANEL, fg=MUTED,
                          activebackground=PANEL, activeforeground=ORANGE, relief="flat", bd=0,
                          font=("Avenir Next", 14), cursor="hand2").pack(side="right")
                tk.Frame(self.entries_frame, bg=LINE, height=1).pack(fill="x", pady=(1, 1))

    def _choose_photo(self):
        path = filedialog.askopenfilename(title="Choose a food photo", filetypes=[
            ("Food photos", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")])
        if path:
            self._set_photo(path)

    def _take_photo(self):
        try:
            import cv2
        except ImportError:
            messagebox.showinfo("Camera setup", "Camera capture needs OpenCV. Install it with:\n\npython3 -m pip install opencv-python\n\nOr use Choose photo to select a picture from your device.")
            return
        # macOS needs AVFoundation; try a few device indexes for external webcams.
        is_macos = __import__("sys").platform == "darwin"
        backend = cv2.CAP_AVFOUNDATION if is_macos else cv2.CAP_ANY
        camera = None
        for camera_index in range(3):
            candidate = cv2.VideoCapture(camera_index, backend)
            if candidate.isOpened():
                camera = candidate
                break
            candidate.release()
        if camera is None:
            self._show_camera_help(is_macos)
            return
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera_window = tk.Toplevel(self.root)
        camera_window.title("Take a food photo · Harvest")
        camera_window.configure(bg=BG)
        camera_window.resizable(False, False)
        camera_window.transient(self.root)
        camera_window.grab_set()
        preview = tk.Label(camera_window, text="Starting camera…", bg=PANEL_2, fg=MUTED,
                           font=("Avenir Next", 12), width=64, height=28)
        preview.pack(padx=18, pady=(18, 10))
        actions = tk.Frame(camera_window, bg=BG)
        actions.pack(fill="x", padx=18, pady=(0, 18))
        capture_button = tk.Button(actions, text="Capture photo", bg=ORANGE, fg="#ffffff",
                                    activebackground="#ff9d60", relief="flat", bd=0,
                                    font=("Avenir Next", 10, "bold"), padx=16, pady=9,
                                    state="disabled")
        capture_button.pack(side="right")
        tk.Button(actions, text="Cancel", command=camera_window.destroy, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, relief="flat", bd=0, font=("Avenir Next", 10),
                  padx=14, pady=9).pack(side="right", padx=(0, 8))
        state = {"frame": None, "photo": None, "after_id": None, "failed_reads": 0}

        def close_camera():
            if state["after_id"]:
                try:
                    camera_window.after_cancel(state["after_id"])
                except tk.TclError:
                    pass
            camera.release()
            if camera_window.winfo_exists():
                camera_window.destroy()

        def save_capture():
            frame = state["frame"]
            if frame is None:
                return
            path = os.path.join(os.path.expanduser("~"), f"harvest-food-{datetime.now():%Y%m%d-%H%M%S}.jpg")
            if cv2.imwrite(path, frame):
                close_camera()
                self._set_photo(path)
            else:
                messagebox.showerror("Couldn't save photo", "Try again, or choose an existing picture.", parent=camera_window)

        capture_button.config(command=save_capture)

        def update_preview():
            if not camera_window.winfo_exists():
                camera.release()
                return
            ok, frame = camera.read()
            if ok:
                state["frame"] = frame.copy()
                state["failed_reads"] = 0
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width = rgb.shape[:2]
                ppm = f"P6 {width} {height} 255 ".encode("ascii") + rgb.tobytes()
                ppm_data = base64.b64encode(ppm).decode("ascii")
                state["photo"] = tk.PhotoImage(data=ppm_data)
                preview.config(image=state["photo"], text="", width=width, height=height)
                capture_button.config(state="normal")
            else:
                state["failed_reads"] += 1
                if state["failed_reads"] >= 150:
                    preview.config(image="", text="No video feed. Check camera permissions in\nSystem Settings → Privacy & Security → Camera,\nthen restart the app.", width=64, height=8)
                    capture_button.config(state="disabled")
                    camera.release()
                    return
            state["after_id"] = camera_window.after(30, update_preview)

        camera_window.protocol("WM_DELETE_WINDOW", close_camera)
        update_preview()

    def _show_camera_help(self, is_macos):
        window = tk.Toplevel(self.root)
        window.title("Camera access · Harvest")
        window.configure(bg=PANEL)
        window.resizable(False, False)
        window.transient(self.root)
        window.grab_set()
        self._label(window, "Camera access is turned off", 16, TEXT, "bold", bg=PANEL).pack(
            anchor="w", padx=22, pady=(20, 6))
        if is_macos:
            explanation = ("macOS is blocking Harvest from opening your camera. Turn camera access back on "
                           "for the app that launches Python (likely Visual Studio Code), then close and reopen Harvest.")
        else:
            explanation = "Check your device's camera privacy settings, then close and reopen Harvest."
        self._label(window, explanation, 10, MUTED, bg=PANEL, wraplength=370,
                    justify="left").pack(anchor="w", padx=22, pady=(0, 16))
        buttons = tk.Frame(window, bg=PANEL)
        buttons.pack(fill="x", padx=22, pady=(0, 20))
        if is_macos:
            tk.Button(buttons, text="Open Camera Settings", command=self._open_camera_settings,
                      bg=DEEP_GREEN, fg="#ffffff", activebackground=GREEN, activeforeground="#ffffff",
                      relief="flat", bd=0, font=("Avenir Next", 10, "bold"), padx=12, pady=8,
                      cursor="hand2").pack(side="left")
        tk.Button(buttons, text="Choose a photo instead", command=lambda: (window.destroy(), self._choose_photo()),
                  bg=PANEL_2, fg=TEXT, activebackground=LINE, activeforeground=TEXT,
                  relief="flat", bd=0, font=("Avenir Next", 9, "bold"), padx=11, pady=8,
                  cursor="hand2").pack(side="right")

    @staticmethod
    def _open_camera_settings():
        try:
            subprocess.Popen(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"])
        except OSError:
            messagebox.showinfo("Camera settings", "Open System Settings → Privacy & Security → Camera and allow access for Visual Studio Code.")

    def _set_photo(self, path):
        self.photo_path = path
        self.photo_estimate = None
        self.photo_status.config(text=f"✓  Photo ready\n{os.path.basename(path)}", fg=GREEN)
        self.analyze_button.config(state="normal", text="✦  Estimate calories")
        self.add_photo_button.config(state="disabled")
        self.result_title.config(text="")
        self.result_detail.config(text="")

    def _analyze_photo(self):
        if not self.photo_path:
            return
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            messagebox.showinfo("Connect calorie estimates", "Photo estimates use the OpenAI API. Set an API key in your terminal before launching the app:\n\nexport OPENAI_API_KEY='your-api-key'\npython3 app.py\n\nYour API account may incur usage charges.")
            return
        self.analyze_button.config(state="disabled", text="Analyzing photo…")
        self.result_title.config(text="Looking at your meal…")
        self.result_detail.config(text="Estimating ingredients and a typical serving size.")
        threading.Thread(target=self._estimate_photo_worker, args=(self.photo_path, api_key), daemon=True).start()

    def _estimate_photo_worker(self, path, api_key):
        try:
            mime = mimetypes.guess_type(path)[0] or "image/jpeg"
            with open(path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("ascii")
            payload = {
                "model": "gpt-4o-mini",
                "input": [{"role": "user", "content": [
                    {"type": "input_text", "text": (
                        "Estimate the food shown in this photo for a calorie tracking app. "
                        "Identify visible foods and infer a typical portion, but do not claim exact accuracy. "
                        "Return JSON only with keys food_name (short name), calories (integer estimate for the pictured serving), "
                        "portion (brief serving description), and notes (short uncertainty or assumptions). "
                        "If this does not appear to be food, return food_name as Not food and calories as 0."
                    )},
                    {"type": "input_image", "image_url": f"data:{mime};base64,{image_data}", "detail": "auto"},
                ]}],
                "text": {"format": {"type": "json_object"}},
                "max_output_tokens": 180,
            }
            request = urllib.request.Request("https://api.openai.com/v1/responses",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=90) as response:
                response_json = json.loads(response.read().decode("utf-8"))
            text = "".join(block.get("text", "") for item in response_json.get("output", [])
                           if item.get("type") == "message" for block in item.get("content", [])
                           if block.get("type") == "output_text")
            estimate = json.loads(text)
            name = str(estimate.get("food_name", "Meal")).strip()[:80]
            calories = int(estimate.get("calories", 0))
            portion = str(estimate.get("portion", "Typical serving")).strip()[:160]
            notes = str(estimate.get("notes", "")).strip()[:200]
            if not name or calories < 0 or calories > 5000:
                raise ValueError("The photo did not produce a usable estimate.")
            self.root.after(0, lambda: self._show_estimate({"name": name, "calories": calories,
                                                            "portion": portion, "notes": notes}))
        except urllib.error.HTTPError as error:
            reason = error.read().decode("utf-8", "replace")[:300]
            self.root.after(0, lambda msg=reason: self._estimate_error(f"API request failed: {msg}"))
        except Exception as error:
            self.root.after(0, lambda msg=str(error): self._estimate_error(msg))

    def _show_estimate(self, estimate):
        self.photo_estimate = estimate
        if estimate["calories"] == 0:
            self.result_title.config(text="No food detected")
            self.result_detail.config(text="Try another photo with the food clearly visible.")
            self.add_photo_button.config(state="disabled")
        else:
            self.result_title.config(text=f"{estimate['name']} · ~{estimate['calories']} kcal")
            self.result_detail.config(text=f"{estimate['portion']}\n{estimate['notes']}")
            self.add_photo_button.config(state="normal")
        self.analyze_button.config(state="normal", text="↻  Recalculate")

    def _estimate_error(self, message):
        self.analyze_button.config(state="normal", text="↻  Try again")
        self.result_title.config(text="Couldn’t estimate this photo")
        self.result_detail.config(text=message[:240])

    def _add_estimated_food(self):
        if not self.photo_estimate or self.photo_estimate["calories"] <= 0:
            return
        estimate = self.photo_estimate
        icon = {"Breakfast": "🍳", "Lunch": "🥗", "Dinner": "🍲", "Snack": "🍊"}[self.meal_var.get()]
        self.entries.append({"name": estimate["name"], "detail": f"{estimate['portion']} · photo estimate",
                             "meal": self.meal_var.get(), "calories": estimate["calories"], "icon": icon})
        self.photo_path = None
        self.photo_estimate = None
        self.photo_status.config(text="📷\n\nTake a photo of your food\nor choose one from your device", fg=MUTED)
        self.result_title.config(text="")
        self.result_detail.config(text="")
        self.analyze_button.config(state="disabled", text="✦  Estimate calories")
        self.add_photo_button.config(state="disabled")
        self._refresh()

    def _add_food(self):
        name, raw = self.name_var.get().strip(), self.cal_var.get().strip()
        if name in ("", "e.g. Apple & peanut butter") or raw in ("", "e.g. 250"):
            messagebox.showinfo("Add food", "Enter a food name and its calories first.")
            return
        try:
            calories = int(raw)
            if calories <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Check calories", "Calories must be a positive whole number.")
            return
        meal = self.meal_var.get()
        icon = {"Breakfast": "🍳", "Lunch": "🥗", "Dinner": "🍲", "Snack": "🍊"}[meal]
        self.entries.append({"name": name, "detail": f"Added just now", "meal": meal, "calories": calories, "icon": icon})
        self.name_var.set("")
        self.cal_var.set("")
        self._refresh()

    def _quick_add(self, name, calories):
        self.entries.append({"name": name, "detail": "Quick add · just now", "meal": "Snack", "calories": calories, "icon": "✳"})
        self._refresh()

    def _remove(self, index):
        del self.entries[index]
        self._refresh()

    def _add_water(self):
        self.water_count = min(8, self.water_count + 1)
        self.water_value.config(text=str(self.water_count))
        self._update_mini_bar(self.water_bar, self.water_count / 8 * 100, ORANGE)


if __name__ == "__main__":
    app = tk.Tk()
    CalorieTracker(app)
    app.mainloop()
