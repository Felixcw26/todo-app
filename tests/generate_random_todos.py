if __name__ == "__main__":
    import random
    from core.date_type import Date
    from core.todo_type import Priority, ToDo
    from core.todo_manager import ToDoManager

    # --- Setup ---
    NUM_TASKS = 100
    random.seed(42)  # reproducibility
    FILE_PATH = "/Users/felixcipher/Documents/coding/todo-app/"

    categories = ["University", "Fraunhofer", "Philosophy", "Room", "Life", "Reading"]
    priorities = list(Priority.ALLOWED_PRIORITIES.keys())
    tags_pool = ["urgent", "creative", "longterm", "coding", "health", "study", "paper"]

    manager = ToDoManager()

    # --- Generate 100 random ToDos ---
    for i in range(NUM_TASKS):
        title = f"Task {i+1}"
        category = random.choice(categories)
        prio = Priority(random.choice(priorities))

        # Create slightly staggered dates
        created_at = Date.today()
        deadline = Date.today() + random.randint(1, 30)

        tags = random.sample(tags_pool, random.randint(0, 3))

        todo = ToDo(
            title=title,
            category=category,
            priority=prio,
            created_at=created_at,
            deadline=deadline,
            tags=tags,
        )
        manager.add_todo(todo)

    # --- Randomly add dependencies (no cycles) ---
    todos = manager.todos
    for task in todos:
        # each task gets up to 3 random dependencies from earlier tasks
        num_deps = random.randint(0, 3)
        possible_deps = [t for t in todos if t != task and todos.index(t) < todos.index(task)]
        for dep in random.sample(possible_deps, min(num_deps, len(possible_deps))):
            try:
                task.add_dependency(dep)
            except Exception:
                pass  # skip invalid or circular dependencies

    # --- Save to JSON ---
    manager.save(FILE_PATH + "tests/data/generate_random_todos.json")
    print("✅ Saved 100 tasks to 'todos.json'.")

    # --- Load again ---
    new_manager = ToDoManager.load(FILE_PATH + "tests/data/generate_random_todos.json")
    print(f"✅ Loaded {len(new_manager.todos)} tasks from file.")

    # --- Optional: quick stats ---
    stats = new_manager.stats()
    print("Stats:", stats)

    new_manager.save(FILE_PATH + "tests/data/generate_random_todos.json")

    # --- Check file size ---
    import os
    size_kb = os.path.getsize(FILE_PATH + "tests/data/generate_random_todos.json") / 1024
    print(f"📦 JSON file size: {size_kb:.2f} KB")
