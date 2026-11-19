"""Harvest: a small desktop daily calorie log, launched directly from Python."""

from contextlib import closing
from datetime import date, datetime
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk


DATABASE = Path(__file__).resolve().parent / "harvest.db"
DAILY_GOAL = 2200
BG = "#0d0d0f"
PANEL = "#151518"
FIELD = "#1d1d21"
LINE = "#2b2b30"
TEXT = "#f2f2f3"
MUTED = "#929298"
ACCENT = "#d4d4d8"


def draw_rounded_shape(canvas, width, height, radius, color):
    canvas.delete("rounded-bg")
    if width < 2 or height < 2:
        return
    radius = min(radius, width // 2, height // 2)
    tag = "rounded-bg"
    canvas.create_rectangle(radius, 0, width - radius, height, fill=color, outline="", tags=tag)
    canvas.create_rectangle(0, radius, width, height - radius, fill=color, outline="", tags=tag)
    for x, y in ((0, 0), (width - 2 * radius, 0),
                 (0, height - 2 * radius), (width - 2 * radius, height - 2 * radius)):
        canvas.create_oval(x, y, x + 2 * radius, y + 2 * radius,
                           fill=color, outline="", tags=tag)


class RoundedPanel(tk.Canvas):
    """Canvas-backed rounded panel with a regular Tk frame for its contents."""

    def __init__(self, parent, fill, height=160, radius=18, inset=13, **kwargs):
        super().__init__(parent, width=300, height=height, bg=parent.cget("bg"),
                         highlightthickness=0, borderwidth=0, **kwargs)
        self.fill = fill
        self.radius = radius
        self.inset = inset
        self.content = tk.Frame(self, bg=fill)
        self.content.pack_propagate(False)
        self.window_id = self.create_window(inset, inset, anchor="nw", window=self.content)
        self.bind("<Configure>", self._resize)

    def _resize(self, event):
        draw_rounded_shape(self, event.width, event.height, self.radius, self.fill)
        width = max(1, event.width - self.inset * 2)
        height = max(1, event.height - self.inset * 2)
        self.coords(self.window_id, self.inset, self.inset)
        self.itemconfigure(self.window_id, width=width, height=height)
        self.tag_lower("rounded-bg")


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, fill=ACCENT, fg=BG, height=44):
        super().__init__(parent, height=height, bg=parent.cget("bg"),
                         highlightthickness=0, borderwidth=0, cursor="hand2")
        self.text = text
        self.command = command
        self.fill = fill
        self.hover_fill = "#ffffff"
        self.fg = fg
        self.radius = 12
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._hover)
        self.bind("<Leave>", self._draw)
        self.bind("<Button-1>", lambda _event: self.command())

    def _draw(self, _event=None, color=None):
        self.delete("all")
        fill = color or self.fill
        width, height = self.winfo_width(), self.winfo_height()
        draw_rounded_shape(self, width, height, self.radius, fill)
        self.create_text(width / 2, height / 2, text=self.text, fill=self.fg,
                         font=("Avenir Next", 10, "bold"))

    def _hover(self, _event):
        self._draw(color=self.hover_fill)


def setup_database():
    with closing(sqlite3.connect(DATABASE)) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL DEFAULT 'desktop-user',
            day TEXT NOT NULL,
            name TEXT NOT NULL,
            meal TEXT NOT NULL,
            calories INTEGER NOT NULL,
            portion TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        db.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('daily_goal', ?)", (DAILY_GOAL,))
        db.commit()


def read_goal():
    with closing(sqlite3.connect(DATABASE)) as db:
        row = db.execute("SELECT value FROM app_settings WHERE key='daily_goal'").fetchone()
    return row[0] if row else DAILY_GOAL


def write_goal(value):
    with closing(sqlite3.connect(DATABASE)) as db:
        db.execute("INSERT INTO app_settings (key, value) VALUES ('daily_goal', ?) "
                   "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (value,))
        db.commit()


def read_today():
    with closing(sqlite3.connect(DATABASE)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            "SELECT id, name, meal, calories, created_at FROM food_entries "
            "WHERE day=? ORDER BY created_at DESC, id DESC",
            (date.today().isoformat(),),
        )]


class HarvestApp:
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

        summary = RoundedPanel(shell, PANEL, height=170)
        summary.pack(fill="x", pady=(0, 14))
        summary_body = summary.content
        top = tk.Frame(summary_body, bg=PANEL)
        top.pack(fill="x")
        left = tk.Frame(top, bg=PANEL)
        left.pack(side="left")
        self.label(left, "CALORIES CONSUMED", 9, MUTED, "bold").pack(anchor="w")
        self.total_label = self.label(left, "0 kcal", 31, TEXT, "bold")
        self.total_label.pack(anchor="w", pady=(5, 0))
        right = tk.Frame(top, bg=PANEL)
        right.pack(side="right", anchor="e", padx=(10, 0))
        self.remaining_label = self.label(right, "2,200", 19, TEXT, "bold")
        self.remaining_label.pack(anchor="e")
        self.label(right, "kcal remaining", 10, MUTED).pack(anchor="e", pady=(1, 0))
        self.progress = ttk.Progressbar(summary_body, style="Harvest.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x", pady=(14, 7))
        legend = tk.Frame(summary_body, bg=PANEL)
        legend.pack(fill="x")
        self.percent_label = self.label(legend, "0% of daily goal", 9, MUTED)
        self.percent_label.pack(side="left")
        self.goal_label = self.label(legend, f"Daily goal · {self.goal:,} kcal", 9, MUTED)
        self.goal_label.pack(side="right")

        content = tk.Frame(shell, bg=BG)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=6)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)
        log_shell = RoundedPanel(content, PANEL)
        log_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        log = log_shell.content
        log_header = tk.Frame(log, bg=PANEL)
        log_header.pack(fill="x", pady=(0, 9))
        self.label(log_header, "Today’s food", 15, TEXT, "bold").pack(side="left")
        self.count_label = self.label(log_header, "0 items", 10, MUTED)
        self.count_label.pack(side="right")

        list_area = tk.Frame(log, bg=PANEL)
        list_area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(list_area, bg=PANEL, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_area, orient="vertical", command=self.canvas.yview,
                                  style="Harvest.Vertical.TScrollbar")
        self.entries_frame = tk.Frame(self.canvas, bg=PANEL)
        self.entries_frame.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.entries_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        form_shell = RoundedPanel(content, PANEL)
        form_shell.grid(row=0, column=1, sticky="nsew")
        form = form_shell.content
        self.label(form, "Log food", 15, TEXT, "bold").pack(anchor="w")
        self.label(form, "Add the food and its calorie amount.", 10, MUTED,
                   wraplength=280, justify="left").pack(anchor="w", pady=(4, 14))

        self._field_label(form, "FOOD")
        self.name_entry = self._entry(form, self.name_var, "e.g. Toast with butter")
        self.name_entry.pack(fill="x", pady=(0, 12))
        self._field_label(form, "CALORIES")
        calories_entry = self._entry(form, self.calories_var, "e.g. 180")
        calories_entry.pack(fill="x", pady=(0, 12))
        calories_entry.bind("<Return>", lambda _event: self.add_food())
        self._field_label(form, "MEAL")
        meal = ttk.Combobox(form, textvariable=self.meal_var,
                            values=["Breakfast", "Lunch", "Dinner", "Snack"],
                            state="readonly", style="Harvest.TCombobox",
                            font=("Avenir Next", 10))
        meal.pack(fill="x", ipady=5, pady=(0, 15))
        self.add_button = RoundedButton(form, "Add to daily log", command=self.add_food)
        self.add_button.pack(fill="x")
        self.status_label = self.label(form, "", 9, MUTED, wraplength=280, justify="left")
        self.status_label.pack(anchor="w", pady=(10, 0))

        tk.Frame(form, bg=LINE, height=1).pack(fill="x", pady=(20, 15))
        self.goal_section_button = tk.Button(
            form, text="", command=self._toggle_goal_editor, bg=PANEL, fg=TEXT,
            activebackground=PANEL, activeforeground=TEXT, relief="flat", bd=0,
            font=("Avenir Next", 12, "bold"), anchor="w", cursor="hand2")
        self.goal_section_button.pack(fill="x")
        self.goal_hint = self.label(form, "Choose a target in 50-calorie steps.", 9, MUTED,
                                    wraplength=280, justify="left")
        goal_controls = tk.Frame(form, bg=PANEL)
        self.goal_controls = goal_controls
        goal_picker = ttk.Spinbox(goal_controls, from_=500, to=10000, increment=50,
                                  textvariable=self.goal_var, style="Harvest.TSpinbox",
                                  font=("Avenir Next", 10), width=9, justify="center")
        goal_picker.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        goal_picker.bind("<Return>", lambda _event: self.save_goal())
        tk.Button(goal_controls, text="Save goal", command=self.save_goal,
                  bg=FIELD, fg=TEXT, activebackground=LINE, activeforeground=TEXT,
                  relief="flat", bd=0, font=("Avenir Next", 9, "bold"),
                  padx=12, pady=8, cursor="hand2").pack(side="left")
        self.goal_status = self.label(form, "", 9, MUTED, wraplength=280, justify="left")
        self._update_goal_section_button()

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
