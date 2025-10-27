from __future__ import annotations
import uuid
from typing import Optional
from core.todo_type import ToDo, Priority
from core.date_type import Date

class AutomaticToDo:
    """
    Blueprint for recurring ToDo structures.
    Can generate full ToDo trees (parent + dependencies),
    where generated instances remain fully editable.
    """

    def __init__(
        self,
        title_pattern: str,
        category: str,
        interval_days: int,
        start_date: Date,
        end_date: Optional[Date] = None,
        parent: Optional[ToDo] = None,
        priority: Optional[Priority] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None
    ):
        self.id = str(uuid.uuid4())
        self.title_pattern = title_pattern
        self.category = category
        self.interval_days = interval_days
        self.start_date = start_date
        self.end_date = end_date
        self.parent = parent
        self.priority = priority or Priority("normal")
        self.description = description
        self.tags = tags or []

        # Template-Subtasks definieren (werden bei jedem Zyklus geklont)
        self.template_subtasks: list[tuple[ToDo, int]] = []
        self.generated_todos: list[str] = []
        self.last_generated_date: Optional[Date] = None
        self.active = True

    # ----------------------------------------------------------
    # Template-Aufgaben definieren
    # ----------------------------------------------------------
    def add_template_subtask(self, title: str, priority: Optional[Priority] = None, tags: Optional[list[str]] = None, offset_days = 0):
        """Add a subtask template to this automation blueprint."""
        todo = ToDo(title=title, category=self.category, priority=priority or self.priority, tags=tags or [])
        self.template_subtasks.append((todo, offset_days))

    # ----------------------------------------------------------
    # Hauptlogik: Generierung (inkl. Unteraufgaben)
    # ----------------------------------------------------------
    def generate_due_tasks(self, manager: "ToDoManager", today: Date) -> list[ToDo]:
        """Generate all missing ToDos and their subtasks since last check."""
        from .todo_manager import ToDoManager
        if not self.active or today < self.start_date:
            return []

        new_tasks = []
        last_date = self.last_generated_date or (self.start_date - self.interval_days)
        current_date = last_date

        while (current_date + self.interval_days) <= today:
            current_date += self.interval_days
            n = len(self.generated_todos) + 1
            title = self.title_pattern.format(n=n)
            deadline = current_date + self.interval_days

            # Hauptaufgabe (z. B. "Übungsblatt 3")
            parent_todo = ToDo(
                title=title,
                category=self.category,
                priority=self.priority,
                deadline=deadline,
                description=self.description,
                tags=self.tags,
            )
            parent_todo.source_automation_id = self.id
            manager.add_todo(parent_todo)

            # Unteraufgaben klonen
            for sub, offset in self.template_subtasks:
                sub_copy = sub.clone()
                sub_copy.dependencies = []
                sub_copy.dependancy_of = [parent_todo]
                
                # 🕓 Korrigierte Deadline-Logik:
                sub_copy.deadline = parent_todo.deadline + offset  # explizit setzen!

                manager.add_todo(sub_copy)
                parent_todo.dependencies.append(sub_copy)

            self.generated_todos.append(parent_todo.id)
            new_tasks.append(parent_todo)

        if new_tasks:
            self.last_generated_date = current_date
        return new_tasks

    # ----------------------------------------------------------
    # Speicherfunktionen
    # ----------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title_pattern": self.title_pattern,
            "category": self.category,
            "interval_days": self.interval_days,
            "start_date": repr(self.start_date),
            "end_date": repr(self.end_date) if self.end_date else None,
            "priority": self.priority.name,
            "tags": self.tags,
            "parent_id": getattr(self.parent, "id", None),
            "generated_todos": self.generated_todos,
            "last_generated_date": repr(self.last_generated_date) if self.last_generated_date else None,
            "active": self.active,

            # 🧩 Jede Subtask + ihr Offset in einem Objekt speichern
            "template_subtasks": [
                {"todo": sub.to_dict(), "offset_days": offset_days}
                for sub, offset_days in self.template_subtasks
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomaticToDo":
        obj = cls(
            title_pattern=data["title_pattern"],
            category=data["category"],
            interval_days=data["interval_days"],
            start_date=Date.from_string(data["start_date"]),
            end_date=Date.from_string(data["end_date"]) if data["end_date"] else None,
            priority=Priority(data.get("priority", "normal")),
            tags=data.get("tags", []),
        )
        obj.id = data["id"]
        obj.generated_todos = data.get("generated_todos", [])
        obj.last_generated_date = (
            Date.from_string(data["last_generated_date"])
            if data.get("last_generated_date")
            else None
        )
        obj.active = data.get("active", True)

        # Template-Subtasks rekonstruieren
        from .todo_type import ToDo  # lokale Vermeidung von Zirkularimport

        obj.template_subtasks = []
        for entry in data.get("template_subtasks", []):
            # Support für alte Versionen ohne Offset
            if isinstance(entry, dict) and "todo" in entry:
                sub = ToDo.from_dict(entry["todo"])
                offset = entry.get("offset_days", 0)
            else:
                sub = ToDo.from_dict(entry)
                offset = 0
            obj.template_subtasks.append((sub, offset))

        return obj