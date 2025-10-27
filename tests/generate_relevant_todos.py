if __name__ == "__main__":
    import random
    from core.date_type import Date
    from core.todo_type import Priority, ToDo
    from core.todo_manager import ToDoManager

    # --- Setup ---
    random.seed(42)
    FILE_PATH = "/Users/felixcipher/Documents/coding/todo-app/"

    manager = ToDoManager()

    # --- Thematic Pools ---
    categories = [
        "University",
        "Fraunhofer",
        "Philosophy",
        "Room",
        "Life",
        "Reading"
    ]
    priorities = list(Priority.ALLOWED_PRIORITIES.keys())
    tags_pool = ["urgent", "creative", "deep", "routine", "analysis", "health", "writing"]

    # --- Realistic Task Seeds ---
    templates = {
        "University": [
            "Solve HM3 Problem Set {n}",
            "Prepare for Theoretical Physics II — Lecture {n}",
            "Write Lab Report: Experiment {n}",
            "Review Quantum Mechanics Notes",
            "Revise Electrodynamics — Chapter {n}",
            "Create Flashcards for HM3",
            "Attend Study Group (Theo3)"
        ],
        "Fraunhofer": [
            "Debug Quantum Decoder Module",
            "Refactor Autoencoder Training Script",
            "Analyze Detection Events for Surface Code",
            "Read Google Nature 2024 Paper",
            "Optimize Loss Function (Partial Trace)",
            "Implement LSTM Model for Decoding",
            "Run Evaluation on Validation Dataset"
        ],
        "Philosophy": [
            "Write essay: 'Freedom and Necessity'",
            "Draft notes on Nietzsche’s 'Genealogy of Morals'",
            "Meditate on Stoic Ethics (Seneca Letter {n})",
            "Outline metaphysical model (4D Projection Hypothesis)",
            "Revise manuscript 'The Shadow and the Light'"
        ],
        "Room": [
            "Organize Bookshelf — Section {n}",
            "Polish Writing Desk",
            "Clean MacBook Screen and Keyboard",
            "Sort university notes by semester",
            "Declutter Nightstand Drawer"
        ],
        "Life": [
            "Grocery Shopping",
            "Laundry",
            "Call parents",
            "Cook dinner for Ronja",
            "Go for a walk — evening reflection",
            "Sort monthly finances",
            "Schedule dentist appointment"
        ],
        "Reading": [
            "Read Chapter {n} of 'Thus Spoke Zarathustra'",
            "Study Chapter {n} of Feynman Lectures",
            "Annotate 'The Myth of Sisyphus'",
            "Summarize insights from 'Being and Time'",
            "Finish novel 'Crime and Punishment'"
        ]
    }

    # --- Generate Tasks ---
    NUM_TASKS = 80
    today = Date.today()
    for i in range(NUM_TASKS):
        category = random.choice(categories)
        template = random.choice(templates[category])
        title = template.format(n=random.randint(1, 10)) if "{n}" in template else template
        prio = Priority(random.choice(priorities))
        created_at = today
        deadline = today + random.randint(1, 30)
        tags = random.sample(tags_pool, random.randint(0, 2))

        todo = ToDo(
            title=title,
            category=category,
            priority=prio,
            created_at=created_at,
            deadline=deadline,
            tags=tags,
        )
        manager.add_todo(todo)

    # --- Logical Dependencies ---
    todos = manager.todos

    dependency_patterns = [
        ("Research", "Write"),
        ("Write", "Review"),
        ("Read", "Summarize"),
        ("Summarize", "Revise"),
        ("Implement", "Analyze"),
        ("Debug", "Optimize"),
        ("Organize", "Clean"),
        ("Draft", "Revise"),
        ("Prepare", "Solve"),
        ("Meditate", "Write"),
    ]

    for task in todos:
        possible_parents = [
            t for t in todos
            if t != task and any(
                kw1.lower() in t.title.lower() and kw2.lower() in task.title.lower()
                for kw1, kw2 in dependency_patterns
            )
        ]
        if possible_parents:
            parent = random.choice(possible_parents)
            try:
                task.add_dependency(parent)
            except Exception:
                pass

    # --- Save ---
    manager.save(FILE_PATH + "tests/data/generate_relevant_todos.json")
    print("✅ Saved realistic tasks to 'generate_relevant_todos.json'.")

    # --- Load again ---
    new_manager = ToDoManager.load(FILE_PATH + "tests/data/generate_relevant_todos.json")
    print(f"✅ Loaded {len(new_manager.todos)} tasks from file.")

    # --- Quick Stats ---
    stats = new_manager.stats()
    print("📊 Stats:", stats)

    # --- Resave for consistency ---
    new_manager.save(FILE_PATH + "tests/data/generate_relevant_todos.json")

    # --- File size check ---
    import os
    size_kb = os.path.getsize(FILE_PATH + "tests/data/generate_relevant_todos.json") / 1024
    print(f"📦 JSON file size: {size_kb:.2f} KB")