from date_type import Date
from todo_type import ToDo, Priority
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
        Return all tasks sorted by a chosen criterion. Supported keys:
        {"deadline", "priority", "created_at", "title", "category"}.
    update_todo()
        Update an existing `ToDo` in place (no new ID). Raises `ValueError` on
        ambiguous title matches or missing items; raises `AttributeError` on
        unknown fields.
    mark_done()
        Mark matching tasks as completed and propagate completion to parent
        projects when all dependencies are done (checks happen in `ToDo.mark_done`).
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
    DateType.Date
        Date abstraction used for creation/completion/deadline fields.
    """

    def __init__(self):
        """Initialize an empty ToDoManager instance."""
        self.todos: list[ToDo] = []

    # -------------------------------------------------------------------------
    # Core CRUD Operations
    # -------------------------------------------------------------------------
    def add_todo(self, task: ToDo) -> None:
        """Add a new ToDo object to the manager if not already present."""
        if task not in self.todos:
            self.todos.append(task)

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

    def list_all(self, sort_by: str = "deadline", reverse: bool = False) -> list[ToDo]:
        """
        Return all ToDos sorted by a specified criterion.

        Parameters
        ----------
        sort_by : {'deadline', 'priority', 'created_at', 'title', 'category'}, optional
            Sorting criterion (default: 'deadline').
        reverse : bool, optional
            If True, sort in descending order.

        Returns
        -------
        list[ToDo]
            Sorted list of ToDo objects.
        """
        key_funcs = {
            "deadline": lambda t: t.deadline,
            "priority": lambda t: t.priority.level,
            "created_at": lambda t: t.created_at,
            "title": lambda t: t.title.lower(),
            "category": lambda t: t.category.lower(),
        }
        key_func = key_funcs.get(sort_by, lambda t: t.deadline)
        return sorted(self.todos, key=key_func, reverse=reverse)

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
        """
        Mark one or more ToDos as completed.

        Automatically propagates completion to parent projects if all dependencies
        are completed.

        Parameters
        ----------
        title : str, optional
            Title of the ToDo to mark as done.
        id : str, optional
            ID of the ToDo to mark as done.
        actual_time : float, optional
            Actual time spent on the task.
        """
        tasks = self.get_todo(title=title, id=id)

        for task in tasks:
            task.mark_done(actual_time)
            for parent in task.dependancy_of:
                parent.mark_done()

    def mark_undone(self, title: str = None, id: str = None) -> None:
        """
        Revert a ToDo (and its parent projects) to undone state.

        Parameters
        ----------
        title : str, optional
            Title of the ToDo to revert.
        id : str, optional
            ID of the ToDo to revert.
        """
        tasks = self.get_todo(title=title, id=id)
        for task in tasks:
            task.mark_undone()

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
        return manager
     