from gui.console_ui import ConsoleUI
from core.todo_manager import ToDoManager
from gui.dark_academia_theme import DarkAcademiaConsole, Palette
from core.todo_type import ToDo, Priority
from core.date_type import Date
import random

try:
    # -------------------------------------------------------------------------
    # Initialisierung
    # -------------------------------------------------------------------------
    manager = ToDoManager.load("/Users/felixcipher/Documents/coding/todo-app/tests/data/generate_relevant_todos.json")
    theme = DarkAcademiaConsole(Palette, 120)

    # -------------------------------------------------------------------------
    # Zufällige ToDos erzeugen
    # -------------------------------------------------------------------------
    titles = [
        "ExPhys3 Übungsblatt", 
        "Theo2 Aufgabenblatt", 
        "HM3 Serie", 
        "Essay Philosophie",
        "Projektbericht QML", 
        "Python Mini-Projekt",
        "Laborprotokoll Optik"
    ]

    categories = ["Philosophy", "University", "Fraunhofer", "Sport", "Band", "Reading", "Room", "Financial", "Relationship", "Life"]
    priorities = ["background", "important", "essential", "blocking"]

    # Deadlines ab 23. Oktober 2025
    base_day = 23
    base_month = 10
    base_year = 2025

    # for i in range(1, 6):  # 5 zufällige Aufgaben
    #     title = f"{random.choice(titles)} {i}"
    #     category = random.choice(categories)
    #     priority_level = random.choice(priorities)

    #     # zufällige Deadline zwischen +0 und +30 Tagen
    #     deadline = Date.today() + random.randint(0, 30)
        
    #     # zufällige geschätzte Zeit
    #     hours = random.randint(1, 5)
    #     minutes = random.choice([1, 15, 30, 45])
    #     estimated_time = hours + minutes / 60

    #     todo = ToDo(
    #         title=title,
    #         deadline=deadline,
    #         priority=Priority(priority_level),
    #         category=category,
    #         est_time=estimated_time,
    #     )

    #     manager.add_todo(todo)

    # -------------------------------------------------------------------------
    # UI starten
    # -------------------------------------------------------------------------
    console = ConsoleUI(manager)
    console.home_menu()
except KeyboardInterrupt:
    print("Abgebrochen")