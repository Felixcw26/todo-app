# 🕰️ ToDo-App — A Modular, Object-Oriented Task Manager

> *"Code is architecture. Order made visible."*

This repository contains a modular, fully object-oriented task management system written in Python.  
It models tasks (`ToDo`) as interconnected objects with priorities, deadlines, dependencies, and persistence,  
managed by a central `ToDoManager`.  

The design emphasizes **academic rigor and aesthetic structure**, balancing logical clarity with maintainability.  
Built to evolve, this project progresses from core logic to a console-based interface, with plans for a future Tkinter GUI.

---

## 🌿 Overview

| Component         | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **`date_type.py`** | Custom date abstraction with validation, comparison, and arithmetic — a lightweight alternative to `datetime`. |
| **`todo_type.py`** | Defines `ToDo` and `Priority` — core entities representing tasks or projects with dependencies, deadlines, and tags. |
| **`todo_manager.py`** | Central controller for creating, managing, updating, serializing, and linking all tasks. |
| **`console_ui.py`** | Current console-based interface using `curses` for task management and visualization. |
| **`tk_gui.py`**    | Planned graphical interface using Tkinter (future development).             |

---

## 🧩 Design Principles

- **Pure OOP Structure** — Clear class boundaries with no procedural shortcuts.
- **Bidirectional Dependency System** — Tasks and projects can depend on each other.
- **JSON Persistence** — Seamless saving and loading of tasks (e.g., `.todos.json`).
- **Extendable Modules** — Designed for future enhancements (CLI, GUI, analytics).
- **Readable, Elegant Code** — Prioritizes maintainability and clarity.

---

## 🚀 Current Features (Alpha v0.1.0)

### ✅ `ToDo`
- Core attributes: title, category, description, priority, deadline, tags, estimated & actual time.
- Logical relationships: `dependencies` and `dependency_of`.
- Methods: `mark_done()`, `extend_deadline()`, `add_dependency()`, `is_overdue()`, etc.
- Serialization: `to_dict()`, `to_json()`, `from_dict()`, `from_json()`.

### ✅ `ToDoManager`
- CRUD operations: add, remove, update, clear.
- Sorting and filtering by priority, category, or deadline.
- Dependency linking and completion propagation.
- JSON persistence via `save()` and `load()`.
- Basic statistics (e.g., `stats()`, `average_completion_time()`).

### ✅ `console_ui.py`
- Terminal-based interface using `curses` for interactive task management.
- Supports adding and changing tasks (e.g., `standard_todo`) with categories and priorities.
- Displays task lists and basic navigation.

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
    manager.save("data/.todos.json")

    # Load again
    new_manager = ToDoManager.load("data/.todos.json")
    print(new_manager.list_all())
````

---

## 🔁 Project Phases (Roadmap)

| Phase | Description | Status |
|--------|--------------|--------|
| **I. Core Architecture** | `Date`, `Priority`, `ToDo`, `ToDoManager` | ✅ Done |
| **II. Console UI** | `console_ui.py` with `curses` interface | 🟡 In progress |
| **III. Tkinter GUI** | Full graphical interface | 🔜 Planned |
| **IV. Extensions** | Export, analytics, notifications | 🔜 Planned |

---

## 📁 Folder Structure

```
todo-app/
│
├── core/
|   ├── __init__.py
|   ├── automatic_todo.py
|   ├── date_type.py
|   ├── key_listener.py
|   ├── todo_manager.py
|   └── todo_type.py
|
├── data/
|   ├── .automations.json
|   └── .todos.json
|
├── gui/
|   ├── __init__.py
|   ├── console_gui.py
|   ├── dark_academia_theme.py
|   └── tk_gui.py # (planned)
|
├── tests/
|   ├── data/
|   |   ├── automation_test_todos.json
|   |   ├── generate_random_todos.json
|   |   ├── generate_relevant_todos.json
|   |   └── test_automations.json
|   |
|   ├── automation_test.py
|   ├── console_test.py
|   ├── generate_random_todos.py
|   ├── generate_relevant_todos.py
|   ├── keylistener_test.py
|   ├── sorting_test.py
|   └── theme_test.py
|
├── __init__.py 
├── .gitignore
├── LICENSE
├── main.py
├── README.md
├── requirements.txt
└── requirements.txt
```

---

## ⚙️ Installation

```bash
git clone https://github.com/Felixcw26/todo-app.git
cd todo-app
# Activate Conda environment (if using Conda)
conda activate todo
# Install dependencies
pip install -r requirements.txt
# Run the app
python todo_manager.py
```

---

## 🧰 Requirements

**Python Version:**  
- Python ≥ 3.11

**Dependencies:**  
This project leverages the Python standard library and a few external packages. Install them via:

```bash
pip install -r requirements.txt
```

**Installed dependencies (via `pip list`):**

| Package             | Version  | Purpose                                      |
|----------------------|-----------|----------------------------------------------|
| `DateTime`           | 5.5       | Enhanced datetime handling for `DateType`.     |
| `linkify-it-py`      | 2.0.3     | URL processing (optional utility).           |
| `markdown-it-py`     | 4.0.0     | Markdown rendering (documentation).          |
| `mdit-py-plugins`    | 0.5.0     | Markdown plugin support.                     |
| `mdurl`              | 0.1.2     | URL parsing for Markdown.                    |
| `numpy`              | 2.3.3     | Numerical operations and date math.          |
| `pip`                | 25.2      | Package manager.                             |
| `platformdirs`       | 4.5.0     | Platform-specific directory handling.        |
| `Pygments`           | 2.19.2    | Syntax highlighting (documentation).         |
| `pyobjc`             | 12.0      | macOS-specific framework (optional).         |
| `pytz`               | 2025.2    | Timezone support.                            |
| `rich`               | 14.2.0    | Rich text formatting (optional UI).          |
| `setuptools`         | 78.1.1    | Build and package management.                |
| `textual`            | 6.3.0     | Terminal UI enhancements (optional).         |
| `typing`             | 3.7.4.3   | Type hints for better code clarity.          |
| `typing_extensions`  | 4.15.0    | Extended type hints.                         |
| `uc-micro-py`        | 1.0.3     | Unicode micro-parsing (Markdown).            |
| `uuid`               | 1.30      | Unique identifier generation.                |
| `wcwidth`            | 0.2.14    | Terminal character width handling.           |
| `wheel`              | 0.45.1    | Package building.                            |
| `zope.interface`     | 8.0.1     | Interface definitions (optional).            |


**Note**: The `pyobjc` family of packages (e.g., `pyobjc-framework-*`) is macOS-specific and may not be required for all platforms. They are included due to your macOS environment.

--- 

## 🧠 Philosophy

This project transcends a simple ToDo app — it’s a system for structured thinking.
Each task is a node, each dependency a logical link, forming a personal graph of intention.

> *"Structure is freedom in form."*

---

## 🪶 Author

**Felix Christoph Winkler**

Physics student, developer, and advocate of structured aesthetics.
Combines theoretical precision with creative design in every project.

---

## 📜 License

MIT License © 2025 Felix Winkler

## 📢 Feedback

We welcome your feedback! Please report issues or suggest enhancements via the GitHub Issues page.