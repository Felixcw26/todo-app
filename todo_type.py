import numpy as np 
from date_type import Date
import uuid
from typing import Optional, Any
import json

class DependancyError(Exception):
    """Raised when an invalid dependency is created or used."""
    def __init__(self, task: "ToDo", reason: str = ""):
        self.task = task
        self.reason = reason
        message = f"Invalid dependency for '{task.title}' ({task.id})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class DeadlineError(Exception):
    def __init__(self, task: "ToDo", reason: str = ""):
        self.task = task
        self.reason = reason
        message = f"Invalid deadline for '{task.title}' ({task.id})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class CategoryError(Exception):
    def __init__(self, task: "ToDo", reason: str = ""):
        self.task = task
        self.reason = reason
        message = f"Invalid category for '{task.title}' ({task.id})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class TagError(Exception):
    def __init__(self, task: "ToDo", reason: str = ""):
        self.task = task
        self.reason = reason
        message = f"Invalid tag for '{task.title}' ({task.id})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class Priority:
    """
    Represents the priority level of a task as both a descriptive label
    and a corresponding numerical value.

    The `Priority` class validates the provided priority name against a fixed
    set of allowed priority levels and assigns a numerical rank internally.
    This allows tasks to be compared or sorted based on importance while
    keeping their semantic meaning human-readable.

    Examples
    --------
    >>> p1 = Priority("blocking")
    >>> p2 = Priority("moderate")
    >>> p1.level
    1
    >>> p2.level
    4
    >>> p1.name
    'blocking'

    Attributes
    ----------
    ALLOWED_PRIORITIES : dict[str, int]
        Mapping of valid priority names to their numeric levels.
        Lower numbers indicate higher importance.

        Default mapping:
        {
            "blocking": 1,
            "essential": 2,
            "important": 3,
            "moderate": 4,
            "background": 5,
            "optional": 6,
            "parked": 7
        }

    name : str
        The textual name of the priority level (e.g. 'important', 'optional').

    level : int
        The numerical rank corresponding to the priority name.
        Lower values represent higher priority.
    """

    ALLOWED_PRIORITIES = {
        "blocking": 1,
        "essential": 2,
        "important": 3,
        "moderate": 4,
        "background": 5,
        "optional": 6,
        "parked": 7
    }

    def __init__(self, name: str):
        if name not in self.ALLOWED_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{name}'. "
                f"Must be one of: {', '.join(self.ALLOWED_PRIORITIES)}"
            )
        self.name = name
        self.level = self.ALLOWED_PRIORITIES[name]
    
    def __add__(self, value: int) -> "Priority":
        """
        Increase the numerical priority level by a given integer value.

        Parameters
        ----------
        value : int
            The amount to increase the numeric level (positive integer).

        Returns
        -------
        Priority
            A new Priority instance representing the adjusted level.

        Raises
        ------
        TypeError
            If `value` is not an integer.
        ValueError
            If the resulting priority level exceeds the allowed range.
        """
        if not isinstance(value, int):
            raise TypeError("Can only add integers to Priority objects.")
        new_level = self.level + value
        if new_level > max(self.ALLOWED_PRIORITIES.values()):
            raise ValueError("Priority level cannot exceed the lowest priority.")
        # find the name corresponding to new_level
        new_name = next(k for k, v in self.ALLOWED_PRIORITIES.items() if v == new_level)
        return Priority(new_name)

    def __sub__(self, value: int) -> "Priority":
        """
        Decrease the numerical priority level by a given integer value.

        Parameters
        ----------
        value : int
            The amount to decrease the numeric level (positive integer).

        Returns
        -------
        Priority
            A new Priority instance representing the adjusted level.

        Raises
        ------
        TypeError
            If `value` is not an integer.
        ValueError
            If the resulting priority level is below the highest priority (1).
        """
        if not isinstance(value, int):
            raise TypeError("Can only subtract integers from Priority objects.")
        new_level = self.level - value
        if new_level < min(self.ALLOWED_PRIORITIES.values()):
            raise ValueError("Priority level cannot go above the highest priority.")
        new_name = next(k for k, v in self.ALLOWED_PRIORITIES.items() if v == new_level)
        return Priority(new_name)

class ToDo:
    """
    A structured task and project entity with prioritization, scheduling,
    dependencies, and serialization utilities.

    The `ToDo` class represents a single actionable unit within a personal
    task management system. Each instance encapsulates metadata such as
    deadlines, priorities, categories, dependencies, and completion state.
    It supports tagging, hierarchical task relationships, JSON serialization,
    and simple project management logic (e.g., marking tasks done, extending
    deadlines, or identifying blockers).

    Each `ToDo` is uniquely identifiable by a UUID and can represent either
    an individual task or a composite project containing dependent sub-tasks.

    Examples
    --------
    >>> t1 = ToDo("Write Thesis", "Research", priority=Priority("important"))
    >>> t2 = ToDo("Literature Review", "Research")
    >>> t1.add_dependency(t2)
    >>> print(t1)
    📁 🕓 Write Thesis
    Category: Research
    Priority: Important
    Created: 10-07-2025
    Deadline: 10-08-2025 (open)
    Estimated Time: - h | Dependencies: 1

    >>> t1.mark_done()
    >>> t1.done
    True

    Attributes
    ----------
    title : str
        Short title or name of the task.
    category : str
        Logical or thematic grouping (Must be one of: ["Philosophy", "University", "Fraunhofer", "Sport", "Band", "Reading", "Room", "Financial", "Life"]).
    description : str, optional
        Detailed description or notes associated with the task.
    priority : Priority
        Priority object defining task urgency (``blocking`` → ``parked``).
    created_at : Date
        Date of task creation.
    deadline : Date
        Date by which the task should be completed.
    in_progress : bool
        If the ToDo is in progress.
    done : bool
        Indicates whether the task has been completed.
    completed_at : Date, optional
        Date on which the task was marked as completed.
    tags : list of str
        Optional user-defined labels for grouping and filtering.
    est_time : float, optional
        Estimated duration in hours.
    actual_time : float, optional
        Actual time spent on the task (if completed).
    dependencies : list of ToDo
        Other tasks that must be completed before this one.
    is_project : bool
        Whether the ToDo represents a project grouping sub-tasks.
    id : str
        Globally unique identifier (UUID4 string).
    overdue : bool
        Whether the deadline lies before the creation date.

    Notes
    -----
    - Dependencies can form arbitrary hierarchical trees (no cycles recommended).
    - Overdue tasks are automatically detected via date comparison.
    - Serialization methods return flat structures; dependency names are
    re-linked through a manager on import.
    - Each ToDo behaves naturally in comparisons (by deadline, then priority).

    Methods
    -------
    mark_done()
        Mark the task as completed and record completion date.
    mark_undone()
        Revert a completed task to open status.
    set_in_progress()
        Set the ToDo in status in progress.
    is_overdue()
        Return ``True`` if the deadline has passed relative to today.
    extend_deadline()
        Extend the deadline by a specified number of days.
    update_priority()
        Adjust or replace the current priority (accepts ``int`` or ``Priority``).
    add_tag()
        Add a tag if not already present.
    remove_tag()
        Remove a tag if it exists.
    set_est_time()
        Define estimated work duration in hours.
    set_actual_time()
        Record actual time spent on the task.

    add_dependency()
        Add another ToDo as a prerequisite.
    remove_dependancy()
        Remove an existing dependency.
    remove_all_dependencies():
        Remove all dependencies recursively.
    is_unblocked()
        Return ``True`` if all dependencies are completed.
    get_blocking_tasks()
        Return a set of tasks blocking completion (possibly empty).
    get_all_dependencies()
        Recursively return all dependencies as a nested dictionary tree.
    depends_on():
        Return True if this task (directly or indirectly) depends on `other`.
    get_dependants():
        Return all tasks that depend on this one.
    is_root_task():
        Return True if this task has no dependants (nothing depends on it).
    is_leaf_task():
        Return True if this task has no dependencies (depends on nothing).

    to_dict()
        Convert the ToDo to a serializable dictionary (flat representation).
    from_dict()
        Reconstruct a ToDo from a dictionary (class method).
    to_json()
        Serialize the ToDo to a JSON string.
    from_json()
        Deserialize a ToDo from a JSON string (class method).

    _generate_id()
        Internal helper: generate a globally unique UUID.
    """

    categories = ["Philosophy", "University", "Fraunhofer", "Sport", "Band", "Reading", "Room", "Financial", "Life"]

    def __init__(
        self,
        title: str,
        category: str,
        description: Optional[str] = None,
        priority: Priority = None,
        created_at: Date = None,
        deadline: Date = None,
        done: bool = False,
        completed_at: Optional[Date] = None,
        tags: Optional[list[str]] = None,
        est_time: Optional[float] = None,
        actual_time: Optional[float] = None,
        dependencies: Optional[list["ToDo"]] = None,
        dependancy_of: list["ToDo"] = None,
        is_project: bool = False,
        id: Optional[str] = None
    ):
        self.title = title

        if category in self.categories:
            self.category = category
        else: 
            raise CategoryError(self, "Invalid category.")
        
        self.description = description
        self.priority = priority or Priority("parked")
        self.created_at = created_at or Date.today()

        if created_at == Date.today() and deadline < Date.today():
            raise DeadlineError(self, "Deadline already overdue!")
        else:
            self.deadline = deadline or (Date.today() + 1)
        
        self.in_progress = False
        self.done = done
        self.completed_at = completed_at

        if tags:
            for tag in tags:
                if tag in self.categories:
                    raise TagError(self, f"Tag {tag} must be a category.")
        
        self.tags = tags or []
        self.est_time = est_time
        self.actual_time = actual_time
        self.dependencies = dependencies or []
        self.dependancy_of = dependancy_of or []
        self.is_project = is_project
        self.id = id or self._generate_id()

        self.overdue = self.deadline < Date.today()

    # -------------------------------------------------------------------------
    # Representation Methods
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        """Return a concise technical representation for debugging."""
        return (
            f"ToDo(title='{self.title}', "
            f"category='{self.category}', "
            f"priority='{self.priority.name}', "
            f"done={self.done}, "
            f"id='{self.id[:8]}...')"
        )

    def __str__(self) -> str:
        """Return a human-readable, aesthetic summary of the task."""
        status_symbol = "✅" if self.done else ("⚠️" if self.overdue else "🕓")
        tags = f" | Tags: {', '.join(self.tags)}" if self.tags else ""
        deps = f" | Dependencies: {len(self.dependencies)}" if self.dependencies else ""
        project_flag = "📁 " if self.is_project else ""
        return (
            f"{project_flag}{status_symbol} {self.title}\n"
            f"   Category: {self.category}\n"
            f"   Priority: {self.priority.name.title()}\n"
            f"   Created: {self.created_at}\n"
            f"   Deadline: {self.deadline} "
            f"({'OVERDUE' if self.overdue else 'open'})\n"
            f"   Estimated Time: {self.est_time or '-'} h"
            f"{tags}{deps}"
        )

    def __eq__(self, other: object) -> bool:
        """Return True if two tasks represent the same item (by ID or title)."""
        if isinstance(other, ToDo):
            return self.id == other.id and self.title == other.title
        return NotImplemented

    def __hash__(self):
        """Allow ToDo objects to be used in sets and as dict keys."""
        return hash(self.id)

    def __lt__(self, other: object) -> bool:
        """Enable chronological or priority-based sorting of tasks."""
        if not isinstance(other, ToDo):
            return NotImplemented
        if self.deadline < other.deadline:
            return True
        elif self.deadline == other.deadline:
            return self.priority.level > other.priority.level
        return False

    def __bool__(self) -> bool:
        """Return True if the task contains valid core data."""
        return all(x is not None for x in (self.priority, self.created_at, self.deadline))

    # -------------------------------------------------------------------------
    # Core Functionality
    # -------------------------------------------------------------------------
    def mark_done(self, actual_time: Optional[float] = None) -> None:
        """Mark the task as completed and record completion date."""
        if not self.done and self.is_unblocked():
            self.done = True
            self.completed_at = Date.today()
            self.actual_time = actual_time
            self.in_progress = False

    def mark_undone(self) -> None:
        """Revert a completed task to open status."""
        if self.done:
            self.done = False
            self.completed_at = None
            self.actual_time = None
            self.in_progress = False

    def set_in_progress(self) -> None:
        """Set the ToDo in status in progress."""
        if not self.done and not self.in_progress:
            self.in_progress = True

    def is_overdue(self) -> bool:
        """Return True and set the attribute if the deadline has passed relative to today."""
        self.overdue = self.deadline < Date.today() and not self.done
        return self.deadline < Date.today() and not self.done

    def extend_deadline(self, days: int) -> None:
        """Extend the deadline by the given number of days."""
        self.deadline = self.deadline + days

    def update_priority(self, updater: int | Priority) -> None:
        """Adjust the priority by level or assign a new Priority instance."""
        try:
            if isinstance(updater, int):
                self.priority = self.priority - updater
            elif isinstance(updater, Priority):
                self.priority = updater
        except ValueError:
            m = self.priority.level - updater
            if m < 1:
                self.priority = Priority("blocking")
            elif m > 7:
                self.priority = Priority("parked")
    
    def add_tag(self, tag: str) -> None:
        """Add a new tag to the task if not already present."""
        if tag not in self.tags:
            if tag in self.categories:
                raise TagError(self, f"Tag {tag} must be a category.")
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag if present."""
        if tag in self.tags:
            self.tags.remove(tag)

    def set_est_time(self, est_time: float) -> None:
        """Set estimated work time in hours."""
        self.est_time = est_time

    def set_actual_time(self, actual_time: float) -> None:
        """Set actual time spent on the task in hours."""
        self.actual_time = actual_time
        
    def add_dependency(self, task: "ToDo") -> None:
        """Add a new dependency if not already present and not cyclic.
    
        Raises
        ------
        DependancyError:
            When itself is added as a dependancy.
            
            When circular dependancy is trying to be added.

            When task is already a dependancy of another task.
        """
        if task is self:
            raise DependancyError(task, "Cannot contain itself as dependency.")
        if task.depends_on(self):
            raise DependancyError(task, "Circular reference detected.")
        if task.dependancy_of:
            raise DependancyError(task, f"'{task.title}' is already a dependency of another task.")
        if task not in self.dependencies:
            self.dependencies.append(task)
            task.dependancy_of.append(self)

    def remove_dependancy(self, task: "ToDo") -> None:
        """Remove a dependency if present."""
        if task in self.dependencies:
            self.dependencies.remove(task)
            if self in task.dependancy_of:
                task.dependancy_of.remove(self)
        
    def remove_all_dependencies(self, visited: set = None) -> set:
        """
        Remove all dependencies recursively.
        Returns a list of all removed tasks for logging or cleanup in the manager.
        """
        if visited is None:
            visited = set()
        if self in visited:
            return []
        visited.add(self)

        removed = set()
        for dep in list(self.dependencies):
            removed.add(dep)
            removed.update(dep.remove_all_dependencies(visited))
            if self in dep.dependancy_of:
                dep.dependancy_of.remove(self)
        self.dependencies.clear()
        return removed
    
    def is_unblocked(self) -> bool:
        """Checks if undone dependancies exist."""
        for task in self.dependencies:
            if task.done:
                continue
            else:
                return False
        return True

    def get_blocking_tasks(self) -> list["ToDo"]:
        """Return a list of tasks blocking completion (possibly empty)."""
        return [t for t in self.dependencies if not t.done]
    
    def get_all_dependencies(self, visited=None) -> dict[str, Any] | None:
        """
        Recursively return all dependencies of the current task as a nested dictionary tree.

        Parameters
        ----------
        visited : set, optional
            Internal helper set to prevent infinite recursion in cyclic dependencies.

        Returns
        -------
        dict[str, dict] | None
            A nested dependency tree in the form:
            {
                "Task A": {
                    "Task B": {
                        "Task C": None
                    }
                }
            }
            Returns None if the task has no dependencies.
        """
        if not self.dependencies:
            return None

        if visited is None:
            visited = set()

        # Prevent infinite recursion in circular dependencies
        if self.id in visited:
            return {self.title: "Cyclic reference detected"}
        visited.add(self.id)

        dependency_tree = {}
        for task in self.dependencies:
            dependency_tree[task.title] = task.get_all_dependencies(visited)

        return dependency_tree

    def depends_on(self, other: "ToDo") -> bool:
        """Return True if this task (directly or indirectly) depends on `other`."""
        visited = set()
        stack = [self]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            if other in current.dependencies:
                return True
            stack.extend(current.dependencies)
        return False

    def get_dependants(self) -> list["ToDo"]:
        """Return all tasks that depend on this one."""
        return self.dependancy_of

    def is_root_task(self) -> bool:
        """Return True if this task has no dependants (nothing depends on it)."""
        return not self.dependancy_of

    def is_leaf_task(self) -> bool:
        """Return True if this task has no dependencies (depends on nothing)."""
        return not self.dependencies

    # -------------------------------------------------------------------------
    # Serialization & Persistence (robust ID-based)
    # -------------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the ToDo into a fully serializable dictionary representation.

        Dependencies and dependants are stored as lists of dictionaries containing
        both `id` and `title` for robust reconstruction.

        Returns
        -------
        dict[str, Any]
            Flat dictionary of task attributes, suitable for JSON serialization.
        """
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "priority": self.priority.name if self.priority else None,
            "created_at": repr(self.created_at) if self.created_at else None,
            "deadline": repr(self.deadline) if self.deadline else None,
            "done": self.done,
            "in_progress": self.in_progress,
            "completed_at": repr(self.completed_at) if self.completed_at else None,
            "tags": self.tags,
            "est_time": self.est_time,
            "actual_time": self.actual_time,
            "is_project": self.is_project,
            "overdue": self.overdue,
            "dependencies": [
                {"id": dep.id, "title": dep.title} for dep in self.dependencies
            ],
            "dependancy_of": [
                {"id": dep.id, "title": dep.title} for dep in self.dependancy_of
            ]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToDo":
        """
        Reconstruct a ToDo object from a serialized dictionary.

        Dependencies and dependants are initially stored as ID-title pairs and must
        later be resolved by the ToDoManager via `link_dependencies`.

        Parameters
        ----------
        data : dict
            The serialized ToDo data.

        Returns
        -------
        ToDo
            Reconstructed instance with placeholder reference fields.
        """
        created_at = Date.from_string(data["created_at"]) if data.get("created_at") else None
        deadline = Date.from_string(data["deadline"]) if data.get("deadline") else None
        completed_at = Date.from_string(data["completed_at"]) if data.get("completed_at") else None
        priority = Priority(data["priority"]) if data.get("priority") else Priority("parked")

        todo = cls(
            title=data["title"],
            category=data["category"],
            description=data.get("description"),
            priority=priority,
            created_at=created_at,
            deadline=deadline,
            done=data.get("done", False),
            completed_at=completed_at,
            tags=data.get("tags", []),
            est_time=data.get("est_time"),
            actual_time=data.get("actual_time"),
            dependencies=[],  # will be re-linked
            dependancy_of=[],
            is_project=data.get("is_project", False),
            id=data.get("id")
        )

        todo.overdue = data.get("overdue", False)
        todo.in_progress = data.get("in_progress", False)

        # Temporarily store unresolved references (IDs & titles)
        todo._dependency_refs = data.get("dependencies", [])
        todo._dependant_refs = data.get("dependancy_of", [])

        return todo

    def to_json(self, indent: int = 4) -> str:
        """Serialize this ToDo instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ToDo":
        """Deserialize a ToDo from a JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    @staticmethod
    def _generate_id() -> str:
        """Generate a globally unique identifier for the task."""
        return str(uuid.uuid4())