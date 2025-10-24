# tests/keylistener_curses_test.py
from core.key_listener import CursesKeyListener
import time

def main():
    with CursesKeyListener() as listener:
        stdscr = listener.stdscr
        # stdscr.clear()
        stdscr.addstr(0, 0, "🕯️  Dark Academia Mode")
        stdscr.addstr(1, 0, "Drücke Pfeile, Buchstaben, Zahlen. 'q' oder STRG+C beendet.\n")
        stdscr.refresh()

        while True:
            key = listener.get_key()
            if key:
                stdscr.addstr(3, 0, f"Aktuell: {key}        ")
                stdscr.refresh()
                if key.lower() == "q" or key == "ESC":
                    break
            time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass