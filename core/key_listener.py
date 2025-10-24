# core/key_listener_curses.py
import curses

class CursesKeyListener:
    """
    Kontextmanager, der curses initialisiert und Tasteneingaben abfängt.
    Er gibt lesbare Key-Namen zurück (inkl. Pfeile, STRG, ENTER, ESC).
    """

    def __enter__(self):
        self.stdscr = curses.initscr()
        curses.noecho()            # keine automatische Ausgabe
        curses.cbreak()            # sofortige Reaktion (kein Enter nötig)
        self.stdscr.keypad(True)   # Spezialtasten wie Pfeile aktivieren
        self.stdscr.nodelay(True)  # nicht blockierend lesen
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def get_key(self):
        """Nicht blockierend lesen; gibt z. B. 'UP', 'DOWN', 'q' oder None zurück."""
        try:
            key = self.stdscr.getch()
            if key == -1:
                return None
            elif key in (10, 13):
                return "ENTER"
            elif key in (curses.KEY_BACKSPACE, 127):
                return "BACKSPACE"
            elif key == curses.KEY_UP:
                return "UP"
            elif key == curses.KEY_DOWN:
                return "DOWN"
            elif key == curses.KEY_LEFT:
                return "LEFT"
            elif key == curses.KEY_RIGHT:
                return "RIGHT"
            elif key == 27:
                return "ESC"
            elif key == ord('q'):
                return "q"
            else:
                return chr(key) if 32 <= key <= 126 else str(key)
        except curses.error:
            return None