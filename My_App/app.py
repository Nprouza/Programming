#!/usr/bin/env python3
"""Simple calorie tracker. Data is stored in a local SQLite database."""

import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(os.environ.get("CALORIE_DB", Path.home() / ".calorie_tracker.db"))
MEALS = ["breakfast", "lunch", "dinner", "snack"]
DEFAULT_GOAL = 2000


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            food TEXT NOT NULL,
            calories INTEGER NOT NULL,
            meal TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    return conn


def get_goal(conn):
    row = conn.execute("SELECT value FROM settings WHERE key = 'goal'").fetchone()
    return int(row[0]) if row else DEFAULT_GOAL


def set_goal(conn):
    goal = ask_int("New daily calorie goal: ", minimum=1)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('goal', ?)", (str(goal),))
    conn.commit()
    print(f"Goal set to {goal} kcal.")


def ask_int(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt).strip())
            if value >= minimum:
                return value
        except ValueError:
            pass
        print(f"Please enter a whole number (at least {minimum}).")


def add_entry(conn):
    food = input("Food name: ").strip()
    if not food:
        print("Food name can't be empty.")
        return
    calories = ask_int("Calories: ")
    meal = ""
    while meal not in MEALS:
        meal = input(f"Meal ({'/'.join(MEALS)}): ").strip().lower()
    conn.execute(
        "INSERT INTO entries (day, food, calories, meal) VALUES (?, ?, ?, ?)",
        (date.today().isoformat(), food, calories, meal),
    )
    conn.commit()
    print(f"Added {food} ({calories} kcal).")


def show_today(conn):
    today = date.today().isoformat()
    rows = conn.execute(
        "SELECT id, meal, food, calories FROM entries WHERE day = ? ORDER BY id", (today,)
    ).fetchall()
    goal = get_goal(conn)
    total = sum(r[3] for r in rows)

    print(f"\n--- Today ({today}) ---")
    if not rows:
        print("Nothing logged yet.")
    for entry_id, meal, food, calories in rows:
        print(f"  [{entry_id}] {meal:<9} {food:<25} {calories:>5} kcal")
    print(f"\nTotal: {total} / {goal} kcal")
    remaining = goal - total
    if remaining >= 0:
        print(f"{remaining} kcal remaining.")
    else:
        print(f"{-remaining} kcal over your goal.")


def delete_entry(conn):
    show_today(conn)
    entry_id = ask_int("\nID of entry to delete (0 to cancel): ")
    if entry_id == 0:
        return
    cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    print("Deleted." if cur.rowcount else "No entry with that ID.")


def weekly_summary(conn):
    goal = get_goal(conn)
    print("\n--- Last 7 days ---")
    for offset in range(6, -1, -1):
        day = (date.today() - timedelta(days=offset)).isoformat()
        total = conn.execute(
            "SELECT COALESCE(SUM(calories), 0) FROM entries WHERE day = ?", (day,)
        ).fetchone()[0]
        bar = "#" * min(total * 30 // goal, 40)
        print(f"{day}  {total:>5} kcal  {bar}")


def main():
    conn = connect()
    actions = {
        "1": ("Add food", add_entry),
        "2": ("Today's log", show_today),
        "3": ("Delete an entry", delete_entry),
        "4": ("Set daily goal", set_goal),
        "5": ("Weekly summary", weekly_summary),
    }
    while True:
        print("\n=== Calorie Tracker ===")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("q. Quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            break
        if choice in actions:
            actions[choice][1](conn)
        else:
            print("Invalid choice.")
    conn.close()


if __name__ == "__main__":
    main()