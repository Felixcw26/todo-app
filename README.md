# 🕰️ ToDo-App — A Modular, Object-Oriented Task Manager

> *"Code is architecture. Order made visible."*

This repository contains a modular, fully object-oriented task management system written in Python.  
It models tasks (`ToDo`) as interconnected objects with priorities, deadlines, dependencies, and persistence,  
managed by a central `ToDoManager`.  

The design is both **academic and aesthetic** — balancing logical structure with human usability.  
It is built to evolve: from core logic to a console interface and later a full Tkinter GUI.

---

## 🌿 Overview

| Component | Description |
|------------|-------------|
| **`date_type.py`** | Custom date abstraction with validation, comparison, and arithmetic — a lightweight replacement for `datetime`. |
| **`todo_type.py`** | Defines `ToDo` and `Priority` — core entities representing tasks or projects with dependencies, deadlines, and tags. |
| **`todo_manager.py`** | Central controller for creating, managing, updating, serializing, and linking all tasks. |
| **`console_gui.py`** *(planned)* | Command-line interface for managing and visualizing tasks interactively. |
| **`tk_gui.py`** *(planned)* | A full graphical interface using **Tkinter**, designed with a dark, academic aesthetic. |

---

## 🧩 Design Principles

- **Pure OOP structure** — clear class boundaries, no procedural shortcuts  
- **Bidirectional dependency system** — projects can depend on subtasks (and vice versa)  
- **JSON persistence** — tasks can be saved and reloaded seamlessly  
- **Extendable modules** — new features can be plugged in easily (CLI, GUI, analytics, etc.)  
- **Readable, elegant code** — designed for maintainability and clarity  

---

## 🚀 Current Features

### ✅ `ToDo`
- Core attributes: title, category, description, priority, deadline, tags, estimated & actual time  
- Logical relationships: `dependencies` and `dependancy_of`  
- Methods: `mark_done()`, `extend_deadline()`, `add_dependency()`, `is_overdue()`, etc.  
- Serialization: `to_dict()`, `to_json()`, `from_dict()`, `from_json()`  

### ✅ `ToDoManager`
- CRUD: add, remove, update, clear  
- Sorting & filtering by priority, category, or deadline  
- Dependency linking and completion propagation  
- JSON persistence (`save()` and `load()`)  
- Basic statistics (`stats()`, `average_completion_time()`)  

---

## 🧪 Example Usage

```python
if __name__ == "__main__":
    from date_type import Date
    from todo_type import Priority, ToDo
    from todo_manager import ToDoManager

    t1 = ToDo("Write Thesis", "University", priority=Priority("important"))
    t2 = ToDo("Literature Review", "University", priority=Priority("moderate"))
    t1.add_dependency(t2)

    manager = ToDoManager()
    manager.add_todo(t1)
    manager.add_todo(t2)

    # Save to file
    manager.save("todos.json")

    # Load again
    new_manager = ToDoManager.load("todos.json")
    print(new_manager.list_all())
```
---

## 🔁 Project Phases (Roadmap)

| Phase | Description | Status |
|--------|--------------|--------|
| **I. Core Architecture** | `Date`, `Priority`, `ToDo`, `ToDoManager` | ✅ Done |
| **II. ConsoleGUI** | Interactive CLI interface for creating and managing tasks | 🟡 In progress |
| **III. Tkinter GUI** | Full graphical user interface (Dark Academia aesthetic) | 🔜 Planned |
| **IV. Extensions** | Export, analytics, notifications, data sync | 🔜 Planned |

---

## 📁 Folder Structure

```
todo-app/
│
├── data/
|   └── todos.json
|
├── gui/
|   ├── console_gui.py # (planned)
|   └── tk_gui.py # (planned)
|
├── tests/
|   └── generate_random_todos.py
|
├── .gitignore
├── date_type.py
├── LICENSE
├── README.md
├── requirements.txt
├── todo_manager.py
└── todo_type.py
```

---

## 🧱 Planned Additions

### `console_gui.py`
Interactive shell for task management:
```bash
add "Write report" -c University -p important
done "Write report"
list --sort deadline
stats
```

### `tk_gui.py`
Graphical interface features

- Sidebar for categories & filters
- Main view with color-coded tasks
- Detail view for description, dependencies, and timing
- Optional Dark Academia theme with serif fonts and warm color palette

--- 

## ⚙️ Installation

```bash
git clone https://github.com/Felixcw26/todo-app.git
cd todo-app
python3 todo_manager.py
```

---

## 🧰 Requirements

**Python Version:**  
- Python ≥ 3.11

**Dependencies:**  
This project is lightweight and mostly uses the standard library.  
Only the following external packages are required:

```bash
pip install numpy DateTime
```

**Installed dependencies (via `pip list`):**

| Package | Version | Purpose |
|----------|----------|----------|
| `numpy` | ≥ 2.3 | numerical operations and date math |
| `DateTime` | ≥ 5.5 | enhanced datetime handling (used in `DateType`) |

All other packages (`uuid`, `typing`, `pytz`, `zope.interface`) are automatically installed as dependencies.

--- 

## 🧠 Philosophy

This project is more than a ToDo app — it’s a system for structured thinking.
Each task is a node, each dependency a logical link, forming a personal graph of intention.

> *"Structure is freedom in form."*

---

## 🪶 Author

**Felix Winkler**

Physics student, developer, and admirer of structured aesthetics.
Combines theoretical clarity with creative design in every project.

---

## 📜 License

MIT License © 2025 Felix Winkler