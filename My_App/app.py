"""A simple desktop app for building and tracking a Christmas wish list."""

import json
import queue
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk


BACKGROUND = "#F7F6F2"
PAPER = "#FFFFFF"
INK = "#26352E"
MUTED = "#7C847F"
GREEN = "#315C49"
GREEN_LIGHT = "#E8EFEA"
RED = "#A14B45"
DATA_FILE = Path(__file__).with_name("christmas_list.json")
INTERESTS = (
    "Art & drawing",
    "Cooking",
    "Gardening",
    "Gaming",
    "History",
    "Music",
    "Photography",
    "Science",
    "Sports",
    "Travel",
)


def fetch_book_ideas(interest):
    query = urllib.parse.urlencode(
        {"q": interest, "maxResults": 8, "printType": "books", "orderBy": "relevance"}
    )
    request = urllib.request.Request(
        f"https://www.googleapis.com/books/v1/volumes?{query}",
        headers={"User-Agent": "ChristmasListIdeas/1.0"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    if not isinstance(data, dict) or not isinstance(data.get("items", []), list):
        raise ValueError("The book service returned an unexpected response.")

    ideas = []
    for result in data.get("items", []):
        if not isinstance(result, dict):
            continue
        info = result.get("volumeInfo", {})
        if not isinstance(info, dict):
            continue
        title = info.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        authors = info.get("authors", [])
        if not isinstance(authors, list):
            authors = []
        ideas.append(
            {
                "title": title.strip(),
                "authors": ", ".join(
                    author for author in authors if isinstance(author, str)
                )
                or "Author not listed",
                "description": info.get("description", "No description available."),
                "url": info.get("infoLink", ""),
            }
        )
    return ideas


class ChristmasListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Christmas List")
        self.root.geometry("760x820")
        self.root.minsize(560, 620)
        self.root.configure(bg=BACKGROUND)

        self.items = self._load_items()
        self.search_queue = queue.Queue()
        self.book_ideas = []
        self._configure_styles()
        self._build_ui()
        self._render_items()
        self.root.after(100, self._check_search_queue)

    def _load_items(self):
        if not DATA_FILE.exists():
            return []

        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                items = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not load your list",
                f"Your saved list could not be read:\n{error}",
            )
            return []

        if not isinstance(items, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not isinstance(item.get("done"), bool)
            for item in items
        ):
            messagebox.showerror(
                "Could not load your list",
                "The saved list has an unexpected format. It will not be changed "
                "until you add or edit an item.",
            )
            return []
        return items

    def _save_items(self):
        try:
            with DATA_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.items, file, indent=2, ensure_ascii=False)
        except OSError as error:
            messagebox.showerror(
                "Could not save your list",
                f"Your changes could not be saved:\n{error}",
            )

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=PAPER,
            fieldbackground=PAPER,
            foreground=INK,
            rowheight=42,
            borderwidth=0,
            font=("Helvetica", 12),
        )
        style.configure(
            "Treeview.Heading",
            background=BACKGROUND,
            foreground=MUTED,
            relief="flat",
            font=("Helvetica", 10, "bold"),
        )
        style.configure(
            "TCombobox",
            fieldbackground=PAPER,
            background=PAPER,
            foreground=INK,
            arrowcolor=GREEN,
            padding=8,
        )
        style.map(
            "Treeview",
            background=[("selected", GREEN_LIGHT)],
            foreground=[("selected", INK)],
        )

    def _build_ui(self):
        page = tk.Frame(self.root, bg=BACKGROUND, padx=36, pady=30)
        page.pack(fill="both", expand=True)

        tk.Label(
            page,
            text="A LITTLE CHRISTMAS PLANNING",
            bg=BACKGROUND,
            fg=GREEN,
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            page,
            text="My Christmas list",
            bg=BACKGROUND,
            fg=INK,
            font=("Helvetica", 28, "bold"),
        ).pack(anchor="w", pady=(8, 4))
        tk.Label(
            page,
            text="Keep all your gift ideas in one calm, happy place.",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 12),
        ).pack(anchor="w", pady=(0, 18))

        discover_card = tk.Frame(page, bg=PAPER, padx=18, pady=16)
        discover_card.pack(fill="x")
        tk.Label(
            discover_card,
            text="Find ideas from your interests",
            bg=PAPER,
            fg=INK,
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w", pady=(0, 9))

        search_row = tk.Frame(discover_card, bg=PAPER)
        search_row.pack(fill="x")
        self.interest_input = ttk.Combobox(
            search_row,
            values=INTERESTS,
            state="normal",
            font=("Helvetica", 12),
        )
        self.interest_input.set("Photography")
        self.interest_input.pack(
            side="left", fill="x", expand=True, ipady=3, padx=(0, 10)
        )
        self.interest_input.bind("<Return>", self._search_ideas)
        self.search_button = self._button(
            search_row, "Find ideas", self._search_ideas, GREEN, PAPER
        )
        self.search_button.pack(side="right")
        self.search_status = tk.Label(
            discover_card,
            text="Choose an interest, or type your own, to find book ideas online.",
            bg=PAPER,
            fg=MUTED,
            font=("Helvetica", 10),
            anchor="w",
        )
        self.search_status.pack(fill="x", pady=(9, 0))

        results_card = tk.Frame(page, bg=PAPER, padx=12, pady=10)
        results_card.pack(fill="x", pady=(10, 0))
        self.idea_view = ttk.Treeview(
            results_card,
            columns=("title", "author"),
            show="headings",
            selectmode="browse",
            height=3,
        )
        self.idea_view.heading("title", text="BOOK IDEA")
        self.idea_view.heading("author", text="AUTHOR")
        self.idea_view.column("title", width=330, anchor="w")
        self.idea_view.column("author", width=210, anchor="w")
        self.idea_view.pack(fill="x")
        self.idea_view.bind("<<TreeviewSelect>>", self._show_idea_description)

        self.idea_description = tk.Label(
            results_card,
            text="Search results will appear here.",
            bg=PAPER,
            fg=MUTED,
            font=("Helvetica", 10),
            justify="left",
            anchor="w",
            wraplength=600,
        )
        self.idea_description.pack(fill="x", pady=(8, 4))

        idea_actions = tk.Frame(results_card, bg=PAPER)
        idea_actions.pack(fill="x")
        self._button(
            idea_actions, "Add selected idea", self._add_selected_idea, GREEN, PAPER
        ).pack(side="left")
        self._button(
            idea_actions,
            "Open book details",
            self._open_selected_idea,
            GREEN_LIGHT,
            GREEN,
        ).pack(side="left", padx=(8, 0))

        entry_card = tk.Frame(page, bg=PAPER, padx=18, pady=14)
        entry_card.pack(fill="x", pady=(10, 0))
        tk.Label(
            entry_card,
            text="Or add your own idea",
            bg=PAPER,
            fg=INK,
            font=("Helvetica", 11, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        entry_row = tk.Frame(entry_card, bg=PAPER)
        entry_row.pack(fill="x")
        self.name_input = tk.Entry(
            entry_row,
            bg=BACKGROUND,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            font=("Helvetica", 12),
        )
        self.name_input.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 10))
        self.name_input.bind("<Return>", self._add_item)
        self._button(
            entry_row, "Add to list", self._add_item, GREEN, PAPER
        ).pack(side="right")

        list_header = tk.Frame(page, bg=BACKGROUND)
        list_header.pack(fill="x", pady=(27, 10))
        tk.Label(
            list_header,
            text="GIFT IDEAS",
            bg=BACKGROUND,
            fg=INK,
            font=("Helvetica", 11, "bold"),
        ).pack(side="left")
        self.progress = tk.Label(
            list_header,
            text="0 ideas",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 10),
        )
        self.progress.pack(side="right")

        list_card = tk.Frame(page, bg=PAPER, padx=12, pady=12)
        list_card.pack(fill="both", expand=True)
        self.list_view = ttk.Treeview(
            list_card,
            columns=("status", "name"),
            show="headings",
            selectmode="browse",
        )
        self.list_view.heading("status", text="STATUS")
        self.list_view.heading("name", text="GIFT IDEA")
        self.list_view.column("status", width=110, anchor="center", stretch=False)
        self.list_view.column("name", width=450, anchor="w")
        self.list_view.pack(fill="both", expand=True)
        self.list_view.bind("<Double-1>", self._toggle_selected)

        footer = tk.Frame(page, bg=BACKGROUND)
        footer.pack(fill="x", pady=(12, 0))
        tk.Label(
            footer,
            text="Tip: double-click an idea to mark it as received.",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 10),
        ).pack(side="left")
        self._button(
            footer, "Remove selected", self._remove_selected, "#EEECEA", INK
        ).pack(side="right")

    def _search_ideas(self, _event=None):
        interest = self.interest_input.get().strip()
        if not interest:
            self.search_status.configure(
                text="Enter an interest first, such as music or hiking.",
                fg=RED,
            )
            self.interest_input.focus_set()
            return
        if len(interest) > 100:
            self.search_status.configure(
                text="Please keep the interest under 100 characters.",
                fg=RED,
            )
            return

        for row in self.idea_view.get_children():
            self.idea_view.delete(row)
        self.book_ideas.clear()
        self.idea_description.configure(text="Searching books online…")
        self.search_status.configure(text="Searching online…", fg=MUTED)
        self.search_button.configure(state="disabled", text="Searching…")
        threading.Thread(
            target=self._search_worker,
            args=(interest,),
            daemon=True,
        ).start()

    def _search_worker(self, interest):
        try:
            self.search_queue.put((interest, fetch_book_ideas(interest), None))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            self.search_queue.put((interest, None, str(error)))

    def _check_search_queue(self):
        try:
            interest, ideas, error = self.search_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.search_button.configure(state="normal", text="Find ideas")
            if error:
                self.idea_description.configure(text="Try searching again in a moment.")
                self.search_status.configure(
                    text=f"Could not search online: {error}",
                    fg=RED,
                )
            elif not ideas:
                self.idea_description.configure(text="Try another interest or search term.")
                self.search_status.configure(
                    text=f"No book ideas found for “{interest}”.",
                    fg=MUTED,
                )
            else:
                self.book_ideas = ideas
                for index, idea in enumerate(ideas):
                    self.idea_view.insert(
                        "",
                        "end",
                        iid=str(index),
                        values=(idea["title"], idea["authors"]),
                    )
                self.search_status.configure(
                    text=f"Found {len(ideas)} ideas for “{interest}” · Google Books",
                    fg=GREEN,
                )
                self.idea_view.selection_set("0")
                self._show_idea_description()

        self.root.after(100, self._check_search_queue)

    def _selected_book_idea(self):
        selected = self.idea_view.selection()
        if not selected or not selected[0].isdigit():
            return None
        index = int(selected[0])
        if index >= len(self.book_ideas):
            return None
        return self.book_ideas[index]

    def _show_idea_description(self, _event=None):
        idea = self._selected_book_idea()
        if idea:
            description = idea["description"]
            if not isinstance(description, str):
                description = "No description available."
            description = " ".join(description.split())
            if len(description) > 320:
                description = f"{description[:317].rstrip()}..."
            self.idea_description.configure(
                text=description or "No description available."
            )

    def _add_selected_idea(self):
        idea = self._selected_book_idea()
        if not idea:
            self.search_status.configure(
                text="Select a book idea to add it to your list.",
                fg=RED,
            )
            return
        name = idea["title"]
        if idea["authors"] != "Author not listed":
            name += f" — {idea['authors']}"
        self.items.append({"name": name, "done": False})
        self._save_items()
        self._render_items()
        self.search_status.configure(text="Added to your Christmas list.", fg=GREEN)

    def _open_selected_idea(self):
        idea = self._selected_book_idea()
        if not idea:
            self.search_status.configure(
                text="Select a book idea first.",
                fg=RED,
            )
            return
        url = idea.get("url")
        if not isinstance(url, str) or not url:
            self.search_status.configure(
                text="No online details link is available for this book.",
                fg=RED,
            )
            return
        if urllib.parse.urlparse(url).scheme != "https" or not webbrowser.open(url):
            self.search_status.configure(
                text="Could not open the book details link.",
                fg=RED,
            )

    @staticmethod
    def _button(parent, text, command, background, foreground):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=background,
            activeforeground=foreground,
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=11,
            cursor="hand2",
            font=("Helvetica", 10, "bold"),
        )

    def _add_item(self, _event=None):
        name = self.name_input.get().strip()
        if not name:
            self.name_input.focus_set()
            return

        self.items.append({"name": name, "done": False})
        self.name_input.delete(0, "end")
        self._save_items()
        self._render_items()
        self.name_input.focus_set()

    def _toggle_selected(self, _event=None):
        selected = self.list_view.selection()
        if not selected or not selected[0].isdigit():
            return
        index = int(selected[0])
        self.items[index]["done"] = not self.items[index]["done"]
        self._save_items()
        self._render_items()
        self.list_view.selection_set(str(index))

    def _remove_selected(self):
        selected = self.list_view.selection()
        if not selected or not selected[0].isdigit():
            messagebox.showinfo("Choose an idea", "Select an idea to remove first.")
            return
        del self.items[int(selected[0])]
        self._save_items()
        self._render_items()

    def _render_items(self):
        for row in self.list_view.get_children():
            self.list_view.delete(row)

        for index, item in enumerate(self.items):
            status = "Received" if item["done"] else "Still hoping"
            self.list_view.insert(
                "",
                "end",
                iid=str(index),
                values=(status, item["name"]),
            )

        received = sum(item["done"] for item in self.items)
        self.progress.configure(
            text=f"{len(self.items)} ideas · {received} received"
        )
        if not self.items:
            self.list_view.insert(
                "",
                "end",
                iid="empty",
                values=("✦", "Your first idea is waiting to be added"),
                tags=("empty",),
            )
            self.list_view.tag_configure("empty", foreground=MUTED)


def main():
    root = tk.Tk()
    ChristmasListApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()