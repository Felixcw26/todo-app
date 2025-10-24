# test_sorting.py
from core.todo_manager import ToDoManager   # ggf. anpassen: engine.todo_manager etc.
from core.todo_type import ToDo, Priority
from core.date_type import Date


def show_sorted(tasks, title):
    """Schöne Konsolenausgabe der sortierten ToDos."""
    print(f"\n🕯️  {title}")
    print("──────────────────────────────────────────────")
    for t in tasks:
        print(f"{t.category:<12} | {t.priority.name:<10} | {t.deadline} | {t.title}")
    print("──────────────────────────────────────────────")


def main():
    # === 1️⃣ Manager initialisieren ===
    manager = ToDoManager()

    # === 2️⃣ Beispiel-ToDos erzeugen (Datumsformat %m-%d-%y) ===
    todos = [
        ToDo("Write Thesis", "University", priority=Priority("important"),
             deadline=Date.from_string("10-10-2025")),
        ToDo("Read Kant", "Reading", priority=Priority("moderate"),
             deadline=Date.from_string("11-02-2025")),
        ToDo("Exercise", "Sport", priority=Priority("background"),
             deadline=Date.from_string("10-05-2025")),
        ToDo("Prepare Presentation", "University", priority=Priority("background"),
             deadline=Date.from_string("10-03-2025")),
        ToDo("Buy Lamp", "Room", priority=Priority("parked"),
             deadline=Date.from_string("10-03-2025")),
        ToDo("Read Plato", "Reading", priority=Priority("important"),
             deadline=Date.from_string("09-30-2025")),
    ]

    for t in todos:
        manager.add_todo(t)

    # === 3️⃣ Verschiedene Sortiertests ===
    show_sorted(manager.list_all(("deadline", "priority")), "Sortierung nach Deadline")

    show_sorted(manager.list_all("priority", reverse=False),
                "Sortierung nach Priorität (absteigend)")

    show_sorted(manager.list_all(("category", "deadline")),
                "Sortierung nach Kategorie, dann Deadline")

    show_sorted(manager.list_all(("priority", "title"), reverse=False),
                "Sortierung nach Priorität, dann Titel (absteigend)")

    # Falls du die rekursive Mehrfachsortierung nutzt:
    show_sorted(manager.list_all(("category", "priority", "deadline")),
                "Sortierung nach Kategorie, dann Priorität, dann Deadline")


if __name__ == "__main__":
    main()