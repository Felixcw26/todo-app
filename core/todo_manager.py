from __future__ import annotations
from core.date_type import Date
from core.todo_type import ToDo, Priority
from core.automatic_todo import AutomaticToDo
from typing import Optional, Any
import json

class ToDoManager:
    """
    High-level management system for organizing and manipulating `ToDo` objects.

    The `ToDoManager` maintains a collection of `ToDo` instances and provides
    utilities for creation, update, deletion, filtering, sorting, dependency
    linking, state transitions (done/undone), and basic statistical analysis.

    It acts as the central interface for a user's task ecosystem, encapsulating
    both standalone tasks and project-like aggregations with dependency graphs.

    Examples
    --------
    >>> manager = ToDoManager()
    >>> t1 = ToDo("Write Thesis", "Research", priority=Priority("important"))
    >>> t2 = ToDo("Literature Review", "Research")
    >>> t1.add_dependency(t2)
    >>> manager.add_todo(t1); manager.add_todo(t2)
    >>> manager.mark_done(title="Literature Review")  # may auto-complete parent if unblocked
    >>> manager.list_all(sort_by="priority")[:1]
    [ToDo(title='Write Thesis', category='Research', priority='important', done=False, id='...')]

    Attributes
    ----------
    todos : list[ToDo]
        The in-memory collection of all managed tasks/projects.

    Methods
    -------
    add_todo()
        Add a new `ToDo` to the manager if not already present.
    remove_todo()
        Remove a `ToDo` from the manager; if it is a project, recursively
        clears its dependencies before removal. Returns True if removed.
    clear_all()
        Remove all tasks from the manager.
    get_todo()
        Retrieve tasks by title or by unique ID. Always returns a list
        (length 1 for ID lookups). Raises `ValueError` if not found or no
        identifier is provided.
    list_all()
        Return all ToDos sorted by one or two criteria. Supported keys:
        {"deadline", "priority", "created_at", "title", "category"}.
    update_todo()
        Update an existing `ToDo` in place (no new ID). Raises `ValueError` on
        ambiguous title matches or missing items; raises `AttributeError` on
        unknown fields.
    mark_done()
        Mark matching tasks as completed and propagate completion to parent
        projects when all dependencies are done (checks happen in `ToDo.mark_done`).
    automatic_priority_update()
        Automatic priority update based on days left till deadline.
    mark_undone()
        Revert matching tasks to the open state.
    filter_by_category()
        Return tasks whose `category` equals the given value.
    filter_by_tag()
        Return tasks containing the specified tag.
    filter_by_priority()
        Return tasks with the specified `Priority`.
    sort_by_deadline()
        Return tasks sorted by `deadline` (ascending).
    sort_by_priority()
        Return tasks sorted by `priority.level` (descending importance).
    sort_by_creation_date()
        Return tasks sorted by `created_at` (ascending).
    get_overdue()
        Return tasks whose `deadline` has passed (`ToDo.is_overdue()` is True).
    get_upcoming(days: int = 3)
        Return tasks whose `deadline` lies within the next `days` (inclusive).
    get_in_progress()
        Return tasks flagged as currently in progress (if attribute exists).
    update_overdue_flags()
        Recompute and store `task.overdue` for all tasks.
    link_dependencies()
        Resolve flat dependency names loaded from serialized data into live
        object references and build inverse relationships (`dependancy_of`).
    get_unblocked_tasks()
        Return tasks for which all dependencies are completed.
    get_dependants()
        Return tasks that act as parents (i.e., have at least one dependency).
    get_leaf_tasks()
        Return tasks with no dependencies (leaves in the dependency graph).
    get_root_tasks()
        Return tasks with no dependants (no parent projects).
    stats()
        Compute collection statistics:
        {
            "overall": int,
            "done": int,
            "undone": int,
            "overdue": int,
            "done_quote": float  # completion ratio excluding projects
        }.
    average_completion_time()
        Average duration (days) between `created_at` and `completed_at`.
        If `search` is provided, filters by matching category or tag first.

    Notes
    -----
    - Sorting uses Python's built-in stable and adaptive Timsort via `sorted`.
    - `get_todo` always returns a list; ID lookups yield a single-element list.
    - `link_dependencies` expects tasks created from flat data to carry
      `_dependency_names`, which are then resolved to live references.
    - Completion propagation relies on `ToDo.mark_done` and `ToDo.is_unblocked`
      to ensure correctness in nested project hierarchies.
    - All time/date comparisons assume compatible `Date` semantics.

    See Also
    --------
    ToDo
        Task/project entity with priority, scheduling, and dependency logic.
    Priority
        Priority levels and numeric ranks.
    date_type.Date
        Date abstraction used for creation/completion/deadline fields.
    """

    def __init__(self):
        """Initialize an empty ToDoManager instance."""
        self.todos: list[ToDo] = []
        self.automations: list[AutomaticToDo] = []

    # -------------------------------------------------------------------------
    # Core CRUD Operations
    # -------------------------------------------------------------------------
    def add_todo(self, task: ToDo) -> None:
        """Add a new ToDo object to the manager if not already present."""
        if task not in self.todos:
            self.todos.append(task)
            self.update_todo_states()

    def remove_todo(self, task: ToDo) -> bool:
        """
        Remove a ToDo object from the manager.

        If the task represents a project, all dependencies are recursively removed.

        Returns
        -------
        bool
            True if the task was successfully removed, False otherwise.
        """
        if task in self.todos:
            if task.is_project:
                task.remove_all_dependencies()
            self.todos.remove(task)
            self.update_todo_states()
            return True
        return False

    def clear_all(self) -> None:
        """Completely clear the ToDo list."""
        self.todos.clear()

    # -------------------------------------------------------------------------
    # Retrieval and Querying
    # -------------------------------------------------------------------------
    def get_todo(self, title: str = None, id: str = None) -> list[ToDo]:
        """
        Retrieve one or more ToDo objects by title or ID.

        Parameters
        ----------
        title : str, optional
            The title of the ToDo to retrieve.
        id : str, optional
            The unique identifier (UUID) of the ToDo to retrieve.

        Returns
        -------
        list[ToDo]
            A list of matching ToDo objects.

        Raises
        ------
        ValueError
            If no matching ToDo is found or no identifier is provided.
        """
        if not title and not id:
            raise ValueError("At least one parameter must be specified (title or id).")

        if id is not None:
            todo = next((t for t in self.todos if t.id == id), None)
            if todo is None:
                raise ValueError(f"No ToDo found with id: {id}")
            return [todo]

        matches = [t for t in self.todos if t.title == title]
        if not matches:
            raise ValueError(f"No ToDo found with title: {title}")
        return matches

    def list_all(
        self,
        sort_by: str | tuple[str, str] = ("deadline", "priority"),
        reverse: bool = False
    ) -> list["ToDo"]:
        """
        Return all ToDos sorted by one or two criteria.

        Parameters
        ----------
        sort_by : str or tuple[str, str], optional
            Primary and optionally secondary sorting keys.
            Supported keys: {'deadline', 'priority', 'created_at', 'title', 'category'}.
            Examples:
                'priority' → sort only by priority
                ('category', 'deadline') → first by category, then by deadline
        reverse : bool, optional
            If True, reverse the final order (applies globally).

        Returns
        -------
        list[ToDo]
            Sorted list of ToDo objects.
        """

        # 🔹 Mögliche Sortierschlüssel definieren
        key_funcs = {
            "deadline": lambda t: t.deadline,
            "priority": lambda t: t.priority.level,
            "created_at": lambda t: t.created_at,
            "title": lambda t: t.title.lower(),
            "category": lambda t: t.category.lower(),
        }

        # 🔹 Normalisiere Eingabe
        if isinstance(sort_by, str):
            sort_keys = (sort_by,)
        elif isinstance(sort_by, (tuple, list)):
            sort_keys = tuple(sort_by)
        else:
            raise TypeError("sort_by must be str or tuple[str, str].")

        # 🔹 Falls nur ein Kriterium angegeben → normale Sortierung
        if len(sort_keys) == 1:
            key_func = key_funcs.get(sort_keys[0], lambda t: t.deadline)
            return sorted(self.todos, key=key_func, reverse=reverse)

        # 🔹 Falls zwei Kriterien: gruppiere nach dem ersten
        primary, secondary = sort_keys[:2]
        primary_key_func = key_funcs.get(primary, lambda t: t.deadline)

        # Gruppierung nach Primärkriterium
        grouped: dict[Any, list] = {}
        for task in self.todos:
            key = primary_key_func(task)
            grouped.setdefault(key, []).append(task)

        # 🔹 Innerhalb jeder Gruppe rekursiv nach dem zweiten Kriterium sortieren
        sorted_groups = []
        for _, group_tasks in sorted(grouped.items(), key=lambda kv: kv[0], reverse=reverse):
            temp_manager = type(self)()  # erzeugt temporären Manager
            temp_manager.todos = group_tasks
            sorted_sublist = temp_manager.list_all(sort_by=secondary, reverse=reverse)
            sorted_groups.extend(sorted_sublist)

        return sorted_groups

    # -------------------------------------------------------------------------
    # Updating and State Control
    # -------------------------------------------------------------------------
    def update_todo(self, attributes: dict, title: str = None, id: str = None) -> ToDo:
        """
        Update an existing ToDo object in place by title or ID.

        Parameters
        ----------
        attributes : dict
            Dictionary of attribute names and new values to assign.
        title : str, optional
            Title of the task to update.
        id : str, optional
            ID of the task to update.

        Returns
        -------
        ToDo
            The updated ToDo object.

        Raises
        ------
        ValueError
            If no matching ToDo is found or multiple tasks share the same title.
        AttributeError
            If an invalid attribute is passed.
        """
        matches = self.get_todo(title=title, id=id)

        if not matches:
            raise ValueError("No matching ToDo found.")
        if len(matches) > 1:
            raise ValueError(f"More than one ToDo found with title '{title}' — use an ID instead.")

        todo = matches[0]
        for key, value in attributes.items():
            if hasattr(todo, key):
                setattr(todo, key, value)
            else:
                raise AttributeError(f"'{type(todo).__name__}' object has no attribute '{key}'")

        return todo

    def mark_done(self, title: str = None, id: str = None, actual_time: Optional[float] = None) -> None:
        """Public entry point — handles lookup and passes to recursive helper."""
        tasks = self.get_todo(title=title, id=id)
        for task in tasks:
            self._mark_done_recursive(task, actual_time, visited=set())

    def _mark_done_recursive(self, task: ToDo, actual_time: Optional[float], visited: set):
        """Recursively mark task and parent projects as completed."""
        if task.id in visited:
            return
        visited.add(task.id)

        # Mark this task as done
        task.mark_done(actual_time)

        # Check parents
        for parent in task.dependancy_of:
            if parent.is_project and parent.is_unblocked():
                # Summe der tatsächlichen Zeiten der Kinder
                total_time = sum(dep.actual_time or 0 for dep in parent.dependencies)
                # Markiere das Projekt selbst
                parent.mark_done(actual_time=total_time)
                # Rekursiv weiter nach oben
                self._mark_done_recursive(parent, total_time, visited)

    def mark_undone(self, title: str = None, id: str = None) -> None:
        """
        Revert one or more ToDos (and *all* parent dependencies) to undone state.

        This recursively propagates upwards through the entire dependency tree:
        if a task becomes undone, all tasks depending on it—project or not—
        must also become undone to maintain logical consistency.
        """
        tasks = self.get_todo(title=title, id=id)
        for task in tasks:
            self._mark_undone_recursive(task, visited=set())

    def _mark_undone_recursive(self, task, visited: set) -> None:
        """Recursively revert task and all parents to undone."""
        if task.id in visited:
            return
        visited.add(task.id)

        # Diesen Task rückgängig machen
        task.mark_undone()

        # Alle direkten Parents rückgängig machen (egal ob Projekt oder nicht)
        for parent in task.dependancy_of:
            # Falls Parent bereits undone ist, überspringen
            if parent.done or parent.in_progress:
                parent.mark_undone()
                # Und weiter nach oben gehen
                self._mark_undone_recursive(parent, visited)
    
    def set_in_progress(self, title: str = None, id: str = None) -> None:
        tasks = self.get_todo(title=title, id=id)
        for task in tasks:
            self.mark_undone(title=title, id=id)
            task.set_in_progress()

    def update_todo_states(self):
        """
        Re-synchronize logical task states across the entire dependency graph.

        This method ensures that the completion status (`done`/`undone`) of all
        tasks and projects is consistent with their dependency relationships.

        Behavior
        --------
        1. **Downward correction**:
        If a task is marked as done but *not unblocked* (i.e., one or more
        dependencies are undone), it is automatically reverted to undone,
        and this change propagates recursively to all its parent dependants.

        2. **Upward propagation**:
        If a project is not yet marked as done but *is unblocked* (i.e., all
        its dependencies are completed), it is automatically marked as done,
        and this completion propagates upward through all parent projects.

        In essence, this method maintains global logical consistency:
        - Projects close themselves when all their subtasks are done.
        - Any newly blocked or inconsistent tasks revert automatically.

        Notes
        -----
        - Normal (non-project) tasks never auto-complete; they must be marked
        manually. This preserves a semantic difference between "projects"
        and "regular tasks".
        - This method is safe to call repeatedly and will converge to a stable
        state (idempotent over the same dependency graph).

        Recommended Call Sites
        -----------------------
        Call `update_todo_states()` whenever the dependency structure or
        completion state of any task changes, for example:
            • after adding or removing a dependency
            • after adding a new ToDo (which might block an existing one)
            • after manually marking a task done or undone
            • after loading ToDos from disk (to rebuild consistent states)
            • after batch operations (bulk imports, automation generation)

        Example
        -------
        >>> manager.add_todo(new_task)
        >>> manager.update_todo_states()   # ensures consistency
        """
        for task in self.todos:
            if task.done and not task.is_unblocked():
                self.mark_undone(title=task.title, id=task.id)
            elif not task.done and task.is_project and task.is_unblocked():
                self.mark_done(title=task.title, id=task.id)
    
    def add_dependancy_of(self, todo: ToDo, title: str = None, id: str = None) -> None:
        """Declare that another ToDo depends on this one.

        Parameters
        ----------
        todo : ToDo
            The ToDo that acts as the prerequisite (dependency).
        title : str, optional
            The title of the dependent ToDo.
        id : str, optional
            The unique ID of the dependent ToDo.

        Raises
        ------
        ValueError
            If no matching ToDo was found or if multiple matches exist.
        """
        parents = self.get_todo(title=title, id=id)
        if not parents:
            raise ValueError(f"No ToDo found for title={title!r}, id={id!r}.")
        if len(parents) > 1:
            raise ValueError(f"Multiple ToDos found for title={title!r}, id={id!r}. "
                            "Expected exactly one match.")

        parent = parents[0]
        parent.add_dependency(todo)

    def automatic_priority_update(self) -> None:
        """Automatic priority update based on days left till deadline."""
        for task in self.todos:
            if Date.today() - task.deadline == 3 and task.updated == 0:
                task.update_priority(1)
                task.updated += 1
            elif Date.today() - task.deadline == 1 and task.updated <= 1:
                task.update_priority(1)
                task.updated += 1
            elif task.is_overdue() and Date.today() - task.deadline == -1 and task.updated <= 2:
                task.update_priority(1)
                task.updated += 1
    
    def automatic_status_update(self) -> None:
        for task in self.todos:
            if not task.is_unblocked() and (task.done or task.in_progress):
                self.mark_undone(task.title, task.id)
    
    def update_automations(self, today: Date = Date.today()):
        """Run all active automations and generate missed tasks."""
        for automation in self.automations:
            new_tasks = automation.generate_due_tasks(self, today)
            if new_tasks:
                print(f"⚙️ Generated {len(new_tasks)} new tasks from {automation.title_pattern}")

    # -------------------------------------------------------------------------
    # Filtering and Selection
    # -------------------------------------------------------------------------
    def filter_by_category(self, category: str) -> list[ToDo]:
        """Return all tasks belonging to a specified category."""
        return [task for task in self.todos if task.category == category]

    def filter_by_tag(self, tag: str) -> list[ToDo]:
        """Return all tasks that contain a given tag."""
        return [task for task in self.todos if tag in task.tags]

    def filter_by_priority(self, priority: Priority) -> list[ToDo]:
        """Return all tasks with the specified priority level."""
        return [task for task in self.todos if task.priority == priority]

    # -------------------------------------------------------------------------
    # Sorting Shortcuts
    # -------------------------------------------------------------------------
    def sort_by_deadline(self) -> list[ToDo]:
        """Return all tasks sorted by deadline."""
        return self.list_all()

    def sort_by_priority(self) -> list[ToDo]:
        """Return all tasks sorted by priority."""
        return self.list_all(sort_by="priority")

    def sort_by_creation_date(self) -> list[ToDo]:
        """Return all tasks sorted by creation date."""
        return self.list_all(sort_by="created_at")
    
    # -------------------------------------------------------------------------
    # Getter
    # -------------------------------------------------------------------------
    def get_attributes(self, attr: str = "name", todos: list[ToDo] = None):
        set = set()
        if not todos:
            todos = self.todos

        for task in todos:
            if attr == "name":
                set.append(task.name)
            elif attr == "deadline":
                set.append(task.deadline)
            elif attr == "category":
                set.append(task.category)
            elif attr == "priority":
                set.append(task.priority)

    # -------------------------------------------------------------------------
    # Temporal Queries
    # -------------------------------------------------------------------------
    def get_overdue(self) -> list[ToDo]:
        """Return all tasks whose deadlines have passed."""
        return [task for task in self.todos if task.is_overdue()]

    def get_upcoming(self, days: int = 3) -> list[ToDo]:
        """
        Return all tasks whose deadlines are within the next `days`.

        Parameters
        ----------
        days : int, optional
            Number of days from today to include (default: 3).
        """
        return [
            task for task in self.todos
            if 0 <= (task.deadline - Date.today()) <= days
        ]

    def get_in_progress(self) -> list[ToDo]:
        """Return all tasks currently in progress."""
        return [task for task in self.todos if getattr(task, "in_progress", False)]

    def update_overdue_flags(self) -> None:
        """Recalculate overdue status for all tasks."""
        for task in self.todos:
            task.overdue = task.is_overdue()

    # -------------------------------------------------------------------------
    # Dependency Management
    # -------------------------------------------------------------------------
    def link_dependencies(self) -> None:
        """
        Resolve flat dependency references after loading serialized data.

        Re-links `ToDo.dependencies` and builds inverse relationships
        (`dependancy_of`) for bidirectional traversal.
        """
        title_map = {t.title: t for t in self.todos}
        for task in self.todos:
            if hasattr(task, "_dependency_names"):
                task.dependencies = [
                    title_map[name]
                    for name in task._dependency_names
                    if name in title_map
                ]
                delattr(task, "_dependency_names")
            for dep in task.dependencies:
                if task not in dep.dependancy_of:
                    dep.dependancy_of.append(task)
        self.update_todo_states()

    def get_unblocked_tasks(self) -> list[ToDo]:
        """Return all tasks whose dependencies are fully completed."""
        return [task for task in self.todos if task.is_unblocked()]

    def get_dependants(self) -> list[ToDo]:
        """Return all tasks that act as parent projects for others."""
        return [task for task in self.todos if not task.is_leaf_task()]

    def get_leaf_tasks(self) -> list[ToDo]:
        """Return all tasks that have no dependencies (leaves in dependency graph)."""
        return [task for task in self.todos if task.is_leaf_task()]

    def get_root_tasks(self) -> list[ToDo]:
        """Return all top-level tasks that have no dependants."""
        return [task for task in self.todos if task.is_root_task()]

    # -------------------------------------------------------------------------
    # Statistical Analysis
    # -------------------------------------------------------------------------
    def stats(self) -> dict:
        """
        Compute basic statistics over the current ToDo collection.

        Returns
        -------
        dict
            {
                "overall": total number of tasks,
                "done": number of completed tasks,
                "undone": number of incomplete tasks,
                "overdue": number of overdue tasks,
                "done_quote": completion ratio (excluding projects)
            }
        """
        overall = len(self.todos)
        done = [t for t in self.todos if t.done]
        undone = [t for t in self.todos if not t.done]
        overdue = [t for t in self.todos if t.is_overdue()]

        non_project_done = [t for t in done if not t.is_project]
        non_project_undone = [t for t in undone if not t.is_project]
        done_quote = (
            len(non_project_done) / (len(non_project_done) + len(non_project_undone))
            if (non_project_done or non_project_undone)
            else 0.0
        )

        return {
            "overall": overall,
            "done": len(done),
            "undone": len(undone),
            "overdue": len(overdue),
            "done_quote": round(done_quote, 2),
        }

    def average_completion_time(self, search: str = None) -> float:
        """
        Compute the average completion duration (in days).

        Parameters
        ----------
        search : str, optional
            Category or tag to filter tasks before averaging.

        Returns
        -------
        float
            Average duration between creation and completion dates.
        """
        tasks = []
        if search:
            tasks = self.filter_by_category(search) or self.filter_by_tag(search)
        else:
            tasks = self.todos

        times = [
            (task.completed_at - task.created_at)
            for task in tasks if task.done
        ]

        return sum(times) / len(times) if times else 0.0
    
    # -------------------------------------------------------------------------
    # JSON Persistence Layer
    # -------------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """
        Convert all ToDos in the manager to a serializable dictionary.

        Returns
        -------
        dict[str, Any]
            {
                "todos": [ <todo_dict>, <todo_dict>, ... ]
            }
        """
        return {"todos": [t.to_dict() for t in self.todos]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToDoManager":
        """
        Reconstruct a ToDoManager from a serialized dictionary.

        Parameters
        ----------
        data : dict
            Serialized data containing a list of ToDos.

        Returns
        -------
        ToDoManager
            Manager with all ToDos re-linked and dependencies restored.
        """
        manager = cls()
        manager.todos = [ToDo.from_dict(td) for td in data.get("todos", [])]

        # Build ID-based lookup for relinking
        id_map = {t.id: t for t in manager.todos}

        for task in manager.todos:
            # Resolve dependencies
            if hasattr(task, "_dependency_refs"):
                task.dependencies = [
                    id_map.get(ref["id"]) for ref in task._dependency_refs if ref["id"] in id_map
                ]
                delattr(task, "_dependency_refs")

            # Resolve dependants
            if hasattr(task, "_dependant_refs"):
                task.dependancy_of = [
                    id_map.get(ref["id"]) for ref in task._dependant_refs if ref["id"] in id_map
                ]
                delattr(task, "_dependant_refs")

        return manager

    def to_json(self, indent: int = 4) -> str:
        """Serialize the entire ToDoManager (all tasks) to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ToDoManager":
        """Deserialize a ToDoManager (including all tasks) from JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    # -------------------------------------------------------------------------
    # File I/O
    # -------------------------------------------------------------------------
    def save(self, path: str) -> None:
        """
        Save the entire manager (and all ToDos) to a JSON file.

        Parameters
        ----------
        path : str
            File path to save the JSON data.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
        print(f"✅ ToDoManager saved successfully → {path}")

    @classmethod
    def load(cls, path: str) -> "ToDoManager":
        """
        Load a ToDoManager from a JSON file and reconstruct dependencies.

        Parameters
        ----------
        path : str
            Path to the JSON file.

        Returns
        -------
        ToDoManager
            Fully reconstructed manager instance.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        manager = cls.from_dict(data)
        print(f"📂 ToDoManager loaded successfully ← {path}")
        manager.update_todo_states()
        return manager
    
    # -------------------------------------------------------------------------
    # Automation Persistence Layer
    # -------------------------------------------------------------------------
    def automations_to_dict(self) -> dict[str, Any]:
        """
        Convert all AutomaticToDos in the manager to a serializable dictionary.

        Returns
        -------
        dict[str, Any]
            {
                "automations": [ <automation_dict>, <automation_dict>, ... ]
            }
        """
        return {"automations": [a.to_dict() for a in self.automations]}

    @classmethod
    def automations_from_dict(cls, data: dict[str, Any]) -> list["AutomaticToDo"]:
        """
        Reconstruct all AutomaticToDo objects from serialized data.

        Parameters
        ----------
        data : dict
            Serialized automation data.

        Returns
        -------
        list[AutomaticToDo]
            Reconstructed automation objects.
        """
        from .automatic_todo import AutomaticToDo  # avoid circular import
        automations = [AutomaticToDo.from_dict(ad) for ad in data.get("automations", [])]
        return automations

    def automations_to_json(self, indent: int = 4) -> str:
        """Serialize all AutomaticToDos in the manager to a JSON string."""
        return json.dumps(self.automations_to_dict(), indent=indent)

    @classmethod
    def automations_from_json(cls, json_str: str) -> list["AutomaticToDo"]:
        """Deserialize AutomaticToDos from a JSON string."""
        data = json.loads(json_str)
        return cls.automations_from_dict(data)

    def save_automations(self, path: str) -> None:
        """
        Save all automations in the manager to a separate JSON file.

        Parameters
        ----------
        path : str
            File path to save the JSON data.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.automations_to_dict(), f, indent=4)
        print(f"✅ Automations saved successfully → {path}")

    def load_automations(self, path: str) -> None:
        """
        Load all automations from a JSON file and reconstruct them.

        Parameters
        ----------
        path : str
            Path to the JSON file.
        """
        from .automatic_todo import AutomaticToDo  # local import to prevent circular dependency
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.automations = [AutomaticToDo.from_dict(ad) for ad in data.get("automations", [])]
        print(f"📂 Automations loaded successfully ← {path}")
        self.update_todo_states()