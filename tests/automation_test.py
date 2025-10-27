from core.todo_manager import ToDoManager
from core.automatic_todo import AutomaticToDo
from core.date_type import Date
from core.todo_type import Priority

def main():
    manager = ToDoManager()

    auto = AutomaticToDo(
        title_pattern="ExPhys4 – Übungsblatt {n}",
        category="University",
        interval_days=7,
        start_date=Date.from_string("10-22-2025"),
        end_date=Date.from_string("12-01-2025"),
        priority=Priority("important"),
    )

    # Template-Unteraufgaben definieren
    auto.add_template_subtask("Aufgabe 1: Theoriefragen", offset_days=-4)
    auto.add_template_subtask("Aufgabe 2: Rechenaufgaben", offset_days=-2)
    auto.add_template_subtask("Aufgabe 3: Bonusaufgabe", offset_days=-1)

    manager.automations.append(auto)

    for t in manager.todos:
         print(t)

    print("Dateum updaten um zwei Wochen.")

    # Simuliere: zwei Wochen später geöffnet
    manager.update_automations(today=Date.from_string("10-29-2025"))

    for t in manager.todos:
            print(t)

    print("Manager speichern!")

    manager.save_automations("/Users/felixcipher/Documents/coding/todo-app/tests/data/test_automations.json")
    manager.save("/Users/felixcipher/Documents/coding/todo-app/tests/data/automation_test_todos.json")

    print("Manager laden!")

    manager2 = ToDoManager.load("/Users/felixcipher/Documents/coding/todo-app/tests/data/automation_test_todos.json")
    manager2.load_automations("/Users/felixcipher/Documents/coding/todo-app/tests/data/test_automations.json")

    print("Manager geladen!")

    for t in manager.todos:
         print(t)

    print("Erneute Woche später.")

    manager2.update_automations(today=Date.from_string("11-06-2025"))

    for t in manager2.todos:
         print(t)

    manager2.save_automations("/Users/felixcipher/Documents/coding/todo-app/tests/data/test_automations.json")
    manager2.save("/Users/felixcipher/Documents/coding/todo-app/tests/data/automation_test_todos.json")

if __name__ == "__main__":
    main()