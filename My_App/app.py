"""Harvest: a small desktop daily calorie log, launched directly from Python."""

from contextlib import closing
from datetime import date, datetime
import base64
import json
import mimetypes
import os
import subprocess
import threading
import urllib.error
import urllib.request


BG = "#f4f5ef"
PANEL = "#ffffff"
PANEL_2 = "#f0f5ed"
TEXT = "#20352a"
MUTED = "#77877a"
ORANGE = "#e77b36"
GREEN = "#477b50"
DEEP_GREEN = "#204a33"
LINE = "#e5ebe2"


class CalorieTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Harvest · Daily calorie log")
        self.root.geometry("1020x800")
        self.root.minsize(800, 680)
        self.root.configure(bg=BG)
        self.name_var = tk.StringVar()
        self.calories_var = tk.StringVar()
        self.meal_var = tk.StringVar(value="Snack")
        self.goal = read_goal()
        self.goal_var = tk.StringVar(value=str(self.goal))
        self.goal_section_open = False
        self._style()
        self._build()
        self.refresh()
        self.name_entry.focus_set()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Harvest.Horizontal.TProgressbar", troughcolor=LINE, background=ACCENT,
                        bordercolor=LINE, lightcolor=ACCENT, darkcolor=ACCENT, thickness=8)
        style.configure("Harvest.TCombobox", fieldbackground=FIELD, background=FIELD,
                        foreground=TEXT, arrowcolor=ACCENT, bordercolor=LINE, padding=8)
        style.map("Harvest.TCombobox", fieldbackground=[("readonly", FIELD)],
                  foreground=[("readonly", TEXT)])
        style.configure("Harvest.TSpinbox", fieldbackground=FIELD, background=FIELD,
                        foreground=TEXT, arrowcolor=ACCENT, bordercolor=LINE, padding=6)
        style.configure("Harvest.Vertical.TScrollbar", background="#3a3a40",
                        troughcolor=PANEL, bordercolor=PANEL, lightcolor="#3a3a40",
                        darkcolor="#3a3a40", width=9, arrowsize=0, relief="flat")
        style.map("Harvest.Vertical.TScrollbar", background=[("active", "#5a5a62")])

    @staticmethod
    def label(parent, text, size=11, color=TEXT, weight="normal", **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")), fg=color,
                        font=("Avenir Next", size, weight), **kwargs)

    def _build(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True, padx=32, pady=24)

        header = tk.Frame(shell, bg=BG)
        header.pack(fill="x", pady=(0, 25))
        self.label(header, "harvest", 21, TEXT, "bold").pack(side="left")
        self.label(header, "DAILY CALORIE LOG", 9, MUTED).pack(side="left", padx=13, pady=(6, 0))
        self.label(header, date.today().strftime("%A, %B %d"), 10, MUTED).pack(side="right", pady=(5, 0))

        self.label(shell, "Today", 27, TEXT, "bold").pack(anchor="w")
        self.label(shell, "A simple log of what you’ve eaten.", 11, MUTED).pack(anchor="w", pady=(3, 18))

        cards = tk.Frame(shell, bg=BG)
        cards.pack(fill="x", pady=(0, 18))
        cards.grid_columnconfigure(0, weight=7, uniform="summary")
        cards.grid_columnconfigure(1, weight=3, uniform="summary")
        self.cal_card = tk.Frame(cards, bg=DEEP_GREEN, padx=25, pady=20)
        self.cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        copy = tk.Frame(self.cal_card, bg=DEEP_GREEN)
        copy.pack(side="left", fill="both", expand=True)
        self._label(copy, "TODAY’S CALORIE BUDGET", 9, "#c1d7c3", "bold", bg=DEEP_GREEN).pack(anchor="w")
        value_line = tk.Frame(copy, bg=DEEP_GREEN)
        value_line.pack(anchor="w", pady=(5, 0))
        self.cal_value = self._label(value_line, "", 39, "#ffffff", "bold", bg=DEEP_GREEN)
        self.cal_value.pack(side="left")
        self._label(value_line, " kcal left", 12, "#d7e6d8", bg=DEEP_GREEN).pack(side="left", padx=(7, 0), pady=(16, 0))
        self.cal_note = self._label(copy, "", 10, "#d7e6d8", bg=DEEP_GREEN)
        self.cal_note.pack(anchor="w", pady=(2, 13))
        self.progress = ttk.Progressbar(copy, style="Harvest.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x", pady=(0, 7))
        progress_legend = tk.Frame(copy, bg=DEEP_GREEN)
        progress_legend.pack(fill="x")
        self.progress_note = self._label(progress_legend, "", 9, "#c1d7c3", "bold", bg=DEEP_GREEN)
        self.progress_note.pack(side="left")
        self._label(progress_legend, f"Daily goal  ·  {self.goal:,} kcal", 9, "#c1d7c3", bg=DEEP_GREEN).pack(side="right")
        ring = tk.Canvas(self.cal_card, width=112, height=112, bg=DEEP_GREEN, highlightthickness=0)
        ring.pack(side="right", padx=(20, 2))
        ring.create_oval(9, 9, 103, 103, outline="#42694e", width=8)
        self.ring_arc = ring.create_arc(9, 9, 103, 103, start=90, extent=-100,
                                        style="arc", outline=ORANGE, width=8)
        self.ring_text = ring.create_text(56, 52, text="0%", fill="#ffffff",
                                          font=("Avenir Next", 17, "bold"))
        ring.create_text(56, 72, text="EATEN", fill="#c1d7c3", font=("Avenir Next", 7, "bold"))
        self.cal_ring = ring

        water = tk.Frame(cards, bg=PANEL, padx=19, pady=18)
        water.grid(row=0, column=1, sticky="nsew")
        water_head = tk.Frame(water, bg=PANEL)
        water_head.pack(fill="x")
        self._label(water_head, "WATER", 9, MUTED, "bold").pack(side="left")
        self._label(water_head, "💧", 16, GREEN).pack(side="right")
        self.water_count = 5
        self.water_value = self._label(water, str(self.water_count), 31, TEXT, "bold")
        self.water_value.pack(anchor="w", pady=(7, 0))
        self._label(water, "glasses today", 10, MUTED).pack(anchor="w")
        self.water_bar = self._mini_bar(water, 62, ORANGE)
        tk.Button(water, text="＋  Add water", command=self._add_water, bg=PANEL_2, fg=DEEP_GREEN,
                  activebackground=LINE, activeforeground=DEEP_GREEN, relief="flat", bd=0,
                  font=("Avenir Next", 9, "bold"), padx=10, pady=6, cursor="hand2").pack(anchor="w", pady=(3, 0))

        body = tk.Frame(shell, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)
        log = tk.Frame(body, bg=PANEL, padx=22, pady=20, highlightthickness=1, highlightbackground=LINE)
        log.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        top = tk.Frame(log, bg=PANEL)
        top.pack(fill="x", pady=(0, 12))
        self._label(top, "Today’s meals", 16, TEXT, "bold").pack(side="left")
        self.count_label = self._label(top, "", 10, MUTED)
        self.count_label.pack(side="right", pady=4)
        self.entries_frame = tk.Frame(log, bg=PANEL)
        self.entries_frame.pack(fill="both", expand=True)

        add = tk.Frame(body, bg=PANEL, padx=20, pady=20, highlightthickness=1, highlightbackground=LINE)
        add.grid(row=0, column=1, sticky="nsew")
        self._label(add, "Add a meal", 16, TEXT, "bold").pack(anchor="w")
        self._label(add, "Take a photo for a quick calorie estimate.", 10, MUTED, wraplength=280, justify="left").pack(anchor="w", pady=(4, 14))
        self.photo_status = tk.Label(add, text="📷\n\nYour meal goes here", bg=PANEL_2,
                                     fg=MUTED, font=("Avenir Next", 10), justify="center", height=6,
                                     relief="flat", wraplength=260, highlightthickness=1, highlightbackground=LINE)
        self.photo_status.pack(fill="x", pady=(0, 12))
        photo_buttons = tk.Frame(add, bg=PANEL)
        photo_buttons.pack(fill="x", pady=(0, 12))
        tk.Button(photo_buttons, text="Browse photos", command=self._choose_photo, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, activeforeground=TEXT, relief="flat", bd=0,
                  font=("Avenir Next", 9, "bold"), padx=9, pady=7, cursor="hand2").pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(photo_buttons, text="Take photo", command=self._take_photo, bg=PANEL_2, fg=TEXT,
                  activebackground=LINE, activeforeground=TEXT, relief="flat", bd=0,
                  font=("Avenir Next", 9, "bold"), padx=9, pady=7, cursor="hand2").pack(side="left", expand=True, fill="x", padx=(4, 0))
        self.analyze_button = tk.Button(add, text="✦  Analyze my meal", command=self._analyze_photo, bg=DEEP_GREEN, fg="#ffffff",
                  activebackground="#37683a", activeforeground="#ffffff", relief="flat", bd=0,
                  font=("Avenir Next", 10, "bold"), padx=10, pady=9, cursor="hand2", state="disabled")
        self.analyze_button.pack(fill="x")
        self.result_frame = tk.Frame(add, bg=PANEL_2, padx=12, pady=10)
        self.result_frame.pack(fill="x", pady=(12, 0))
        self.result_title = self._label(self.result_frame, "", 11, DEEP_GREEN, "bold", wraplength=260, justify="left", bg=PANEL_2)
        self.result_title.pack(anchor="w")
        self.result_detail = self._label(self.result_frame, "", 9, MUTED, wraplength=260, justify="left", bg=PANEL_2)
        self.result_detail.pack(anchor="w", pady=(3, 8))
        self.meal_var = tk.StringVar(value="Snack")
        self._label(add, "MEAL", 9, MUTED, "bold").pack(anchor="w", pady=(9, 5))
        meal = ttk.Combobox(add, textvariable=self.meal_var, values=["Breakfast", "Lunch", "Dinner", "Snack"],
                            state="readonly", style="Harvest.TCombobox", font=("Avenir Next", 10))
        meal.pack(fill="x", ipady=4, pady=(0, 10))
        self.add_photo_button = tk.Button(add, text="＋  Add estimated meal", command=self._add_estimated_food, bg=ORANGE, fg="#ffffff",
                  activebackground="#ff9d60", activeforeground="#20150f", relief="flat", bd=0,
                  font=("Avenir Next", 10, "bold"), padx=10, pady=9, cursor="hand2", state="disabled")
        self.add_photo_button.pack(fill="x")
        self._label(add, "Estimates are approximate. Portion size and hidden ingredients can change the actual calories.",
                    8, MUTED, wraplength=300, justify="left").pack(anchor="w", pady=(10, 0))
        self._label(shell, "Made for mindful meals  ·  ✳", 9, MUTED).pack(anchor="center", pady=(12, 0))

    def _field_label(self, parent, text):
        self.label(parent, text, 9, MUTED, "bold").pack(anchor="w", pady=(0, 6))

    def _entry(self, parent, variable, placeholder):
        entry = tk.Entry(parent, textvariable=variable, bg=FIELD, fg=TEXT,
                         insertbackground=TEXT, relief="flat", bd=0,
                         font=("Avenir Next", 10))
        entry.insert(0, placeholder)
        entry.config(fg=MUTED)
        entry.bind("<FocusIn>", lambda _event: self._clear_placeholder(entry, placeholder))
        entry.bind("<FocusOut>", lambda _event: self._restore_placeholder(entry, variable, placeholder))
        entry.placeholder = placeholder
        return entry

    @staticmethod
    def _clear_placeholder(entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=TEXT)

    @staticmethod
    def _restore_placeholder(entry, variable, placeholder):
        if not variable.get():
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def refresh(self):
        entries = read_today()
        total = sum(item["calories"] for item in entries)
        remaining = self.goal - total
        percent = min(100, round(total / self.goal * 100))
        self.total_label.config(text=f"{total:,} kcal")
        self.remaining_label.config(text=f"{max(0, remaining):,}" if remaining >= 0 else f"{abs(remaining):,}")
        self.progress["value"] = percent
        self.percent_label.config(text=(f"{percent}% of daily goal" if remaining >= 0 else f"{abs(remaining):,} kcal over goal"))
        self.goal_label.config(text=f"Daily goal · {self.goal:,} kcal")
        self._update_goal_section_button()
        self.count_label.config(text=f"{len(entries)} {('item' if len(entries) == 1 else 'items')}")

        for child in self.entries_frame.winfo_children():
            child.destroy()
        if not entries:
            self.label(self.entries_frame, "Nothing logged yet.\nAdd your first food →", 11, MUTED,
                       justify="left").pack(anchor="w", pady=18)
            return
        for meal_name in ("Breakfast", "Lunch", "Dinner", "Snack"):
            group = [item for item in entries if item["meal"] == meal_name]
            if not group:
                continue
            header = tk.Frame(self.entries_frame, bg=PANEL)
            header.pack(fill="x", pady=(13, 4))
            self.label(header, meal_name, 10, MUTED, "bold").pack(side="left")
            subtotal = sum(item["calories"] for item in group)
            self.label(header, f"{subtotal:,} kcal", 9, MUTED).pack(side="right")
            for item in group:
                row = tk.Frame(self.entries_frame, bg=PANEL)
                row.pack(fill="x", pady=7)
                badge = tk.Label(row, text=meal_name[0], bg=FIELD, fg=MUTED,
                                 font=("Avenir Next", 9, "bold"), width=3, height=2)
                badge.pack(side="left", padx=(0, 10))
                name = tk.Frame(row, bg=PANEL)
                name.pack(side="left", fill="x", expand=True)
                self.label(name, item["name"], 10, TEXT, "bold", anchor="w").pack(fill="x")
                self.label(name, item.get("created_at", "")[-8:-3], 9, MUTED, anchor="w").pack(fill="x", pady=(2, 0))
                self.label(row, f"{item['calories']:,} kcal", 9, TEXT, "bold").pack(side="right", padx=(5, 5))
                tk.Button(row, text="×", command=lambda entry_id=item["id"]: self.remove_food(entry_id),
                          bg=PANEL, fg=MUTED, activebackground=PANEL, activeforeground=TEXT,
                          relief="flat", bd=0, font=("Avenir Next", 14), cursor="hand2").pack(side="right")
                tk.Frame(self.entries_frame, bg=LINE, height=1).pack(fill="x")

    def save_goal(self):
        try:
            goal = int(self.goal_var.get())
            if not 500 <= goal <= 10000:
                raise ValueError
        except ValueError:
            self.goal_status.config(text="Choose a whole number from 500 to 10,000 kcal.", fg=TEXT)
            self.goal_status.pack(anchor="w", pady=(8, 0))
            return
        self.goal = goal
        write_goal(goal)
        self.goal_status.config(text="Daily goal saved.", fg=MUTED)
        self.goal_status.pack(anchor="w", pady=(8, 0))
        self.refresh()

    def _toggle_goal_editor(self):
        self.goal_section_open = not self.goal_section_open
        if self.goal_section_open:
            self.goal_hint.pack(anchor="w", pady=(4, 10))
            self.goal_controls.pack(fill="x")
        else:
            self.goal_hint.pack_forget()
            self.goal_controls.pack_forget()
            self.goal_status.pack_forget()
        self._update_goal_section_button()

    def _update_goal_section_button(self):
        indicator = "−" if self.goal_section_open else "+"
        self.goal_section_button.config(
            text=f"Daily calorie goal  ·  {self.goal:,} kcal     {indicator}")

    def add_food(self):
        name = self.name_var.get().strip()
        if name == self.name_entry.placeholder:
            name = ""
        raw_calories = self.calories_var.get().strip()
        if not name:
            self.status_label.config(text="Enter a food name.", fg=TEXT)
            self.name_entry.focus_set()
            return
        try:
            calories = int(raw_calories)
            if not 1 <= calories <= 5000:
                raise ValueError
        except ValueError:
            self.status_label.config(text="Enter a whole number from 1 to 5,000 calories.", fg=TEXT)
            return
        with closing(sqlite3.connect(DATABASE)) as db:
            db.execute("""INSERT INTO food_entries
                (client_id, day, name, meal, calories, portion, created_at)
                VALUES ('desktop-user', ?, ?, ?, ?, '', ?)""",
                (date.today().isoformat(), name[:80], self.meal_var.get(), calories,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.commit()
        self.name_var.set("")
        self.calories_var.set("")
        self.status_label.config(text="Added to today’s log.", fg=MUTED)
        self._restore_placeholder(self.name_entry, self.name_var, self.name_entry.placeholder)
        self.refresh()
        self.name_entry.focus_set()

    def remove_food(self, entry_id):
        with closing(sqlite3.connect(DATABASE)) as db:
            db.execute("DELETE FROM food_entries WHERE id=? AND day=?",
                       (entry_id, date.today().isoformat()))
            db.commit()
        self.refresh()


def main():
    setup_database()
    root = tk.Tk()
    HarvestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
