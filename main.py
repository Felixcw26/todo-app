from core.todo_manager import ToDoManager
from gui.console_ui import ConsoleUI

if __name__ == "__main__":
    manager = ToDoManager()
    ui = ConsoleUI(manager)
    try:
        ui.run()
    except KeyboardInterrupt as i:
        ui.save()