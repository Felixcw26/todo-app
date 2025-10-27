from core.date_type import Date
from core.todo_type import ToDo, Priority
from core.todo_manager import ToDoManager
from core.key_listener import CursesKeyListener
from gui.dark_academia_theme import DarkAcademiaConsole, Palette
import time
from pathlib import Path

class InputField:
    def __init__(self, width: int):
        self.text = ""
        self.cursor = 0
        self.width = max(1, width)  # Ensure width is at least 1

    def insert(self, ch: str):
        # Only insert if adding the character doesn't exceed width
        if len(self.text) < self.width:
            self.text = self.text[:self.cursor] + ch + self.text[self.cursor:]
            self.cursor += 1

    def backspace(self):
        if self.cursor > 0:
            self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
            self.cursor -= 1

    def move_left(self):
        if self.cursor > 0:
            self.cursor -= 1

    def move_right(self):
        if self.cursor < len(self.text):
            self.cursor += 1

    def get_display_text(self, input_bool: bool = False) -> str | list[tuple[str, str, str | None]]:
        if not input_bool:
            # Standard behavior: return a string, padded to width
            return self.text + " " * (self.width - len(self.text))
        else:
            # Enhanced behavior: return segments with cursor highlighting
            segments = []
            text_before = self.text[:self.cursor]
            char_at_cursor = self.text[self.cursor:self.cursor+1]  # Character behind cursor
            text_after = self.text[self.cursor+1:]
            # Add segments
            if text_before:
                segments.append((text_before, "WHITE", None))
            if char_at_cursor:
                segments.append((char_at_cursor, "GREEN", None))  # Highlight in green
            if text_after:
                segments.append((text_after, "WHITE", None))
            # Pad with spaces
            total_len = len(self.text)
            if total_len < self.width:
                segments.append((" " * (self.width - total_len), "WHITE", None))
            return segments

class MaskedInputField:
    def __init__(self, mask: str, default_value: str = None):
        if mask == "mm-dd-yyyy":
            editable_chars = "mdy"
        elif mask == "00h00min":
            editable_chars = "0"
        self.mask = mask
        self.chars = list(mask)
        self.editable_positions = [
            i for i, ch in enumerate(mask) if ch.lower() in editable_chars
        ]
        self.pos_index = 0

        # Default-Wert setzen, falls angegeben
        if default_value is not None and default_value != mask:
            # Prüfen, ob die Länge des Default-Werts mit der Maske übereinstimmt
            if len(default_value) == len(self.mask):
                # Default-Wert direkt übernehmen
                self.chars = list(default_value)
                self.pos_index = len(self.editable_positions)  # Cursor ans Ende setzen

    def insert(self, ch: str):
        if self.pos_index < len(self.editable_positions):
            pos = self.editable_positions[self.pos_index]
            self.chars[pos] = ch
            self.pos_index += 1

    def backspace(self):
        if self.pos_index > 0:
            self.pos_index -= 1
            pos = self.editable_positions[self.pos_index]
            self.chars[pos] = self.mask[pos]

    def get_display_text(self):
        return "".join(self.chars)

    def reset(self):
        self.chars = list(self.mask)
        self.pos_index = 0

class MultilineInputField:
    def __init__(self, widths: list[int]):
        """
        Initialize a multiline input field.
        widths: List of widths for each line, e.g., [57, 72, 72].
        """
        self.widths = [max(1, w) for w in widths]  # Ensure each width is at least 1
        self.text = ""
        self.cursor = 0
        self._update_capacity()

    def _update_capacity(self):
        """Update the total capacity based on current widths."""
        curser_lines = 0
        for i in range(len(self.widths)):
            if len(self.text) < sum(self.widths[:i+1]):
                curser_lines += 1
        self.total_capacity = sum(self.widths) - curser_lines

        # Truncate text if it exceeds the new capacity
        if len(self.text) > self.total_capacity:
            self.text = self.text[:self.total_capacity]
            self.cursor = min(self.cursor, self.total_capacity)

    def set_widths(self, new_widths: list[int]):
        """Update the widths and adjust text/cursor accordingly."""
        self.widths = [max(1, w) for w in new_widths]
        self._update_capacity()

    def insert(self, ch: str):
        """Insert a character at the cursor position if within capacity."""
        if len(self.text) < self.total_capacity:
            self.text = self.text[:self.cursor] + ch + self.text[self.cursor:]
            self.cursor += 1

    def backspace(self):
        """Remove the character before the cursor."""
        if self.cursor > 0:
            self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
            self.cursor -= 1

    def move_left(self):
        """Move the cursor left."""
        if self.cursor > 0:
            self.cursor -= 1

    def move_right(self):
        """Move the cursor right."""
        if self.cursor < len(self.text):
            self.cursor += 1

    def _get_cursor_line_col(self, cursor: int) -> tuple[int, int]:
        """Determine the line and column of the cursor position."""
        pos = 0
        for line_idx, width in enumerate(self.widths):
            if cursor <= pos + width:
                return line_idx, cursor - pos
            pos += width
        # If cursor is beyond text, place it at the end of the last line
        last_line = len(self.widths) - 1
        return last_line, min(cursor - pos, self.widths[last_line])

    def _build_lines(self, text: str, cursor: int) -> tuple[list[str], int, int]:
        """
        Split text into lines with word breaks and hyphenation.
        Returns (lines, cursor_line, cursor_col).
        """
        lines = []
        current_line = []
        current_len = 0
        cursor_line = 0
        cursor_col = 0
        pos = 0

        words = text.replace("\n", " ").split(" ") if text else [""]
        for word in words:
            if word == "":
                word = " "  # Handle multiple spaces

            while word and len(lines) < len(self.widths):
                current_line_idx = len(lines)
                max_width = self.widths[current_line_idx]

                # Track cursor position
                if pos <= cursor <= pos + len(word) + (1 if current_line else 0):
                    cursor_line = current_line_idx
                    cursor_col = cursor - pos + (len(" ".join(current_line)) + 1 if current_line else 0)

                # Check if word fits in current line
                word_len = len(word) + (1 if current_line else 0)  # Account for space
                if current_len + word_len <= max_width:
                    current_line.append(word)
                    current_len += word_len
                    pos += len(word) + (1 if current_line else 0)
                    word = ""
                else:
                    # Try to hyphenate
                    available = max_width - current_len - (1 if current_line else 0)
                    if available >= 2:  # Need at least 2 chars for hyphenation
                        part = word[:available - 1]
                        current_line.append(part + "-")
                        current_len += len(part) + 1 + (1 if current_line else 0)
                        word = word[available - 1:]
                        pos += len(part) + (1 if current_line else 0)
                    else:
                        # Move to next line
                        if current_line:
                            lines.append(" ".join(current_line).ljust(max_width))
                            current_line = []
                            self.current_len = 0
                        if len(lines) < len(self.widths):
                            current_line.append(word)
                            current_len = len(word)
                            pos += len(word) + (1 if current_line else 0)
                            word = ""

                # Finalize line if full
                if current_len >= max_width and len(lines) < len(self.widths):
                    lines.append(" ".join(current_line).ljust(max_width))
                    current_line = []
                    current_len = 0

        # Append any remaining content
        if current_line and len(lines) < len(self.widths):
            lines.append(" ".join(current_line).ljust(self.widths[len(lines)]))

        # Fill remaining lines with spaces
        while len(lines) < len(self.widths):
            lines.append(" " * self.widths[len(lines)])

        # Adjust cursor if not found
        if pos < cursor:
            cursor_line = len(self.widths) - 1
            cursor_col = min(cursor - pos, self.widths[cursor_line])

        return lines, cursor_line, cursor_col

    def get_lines(self, input_bool: bool = False) -> list[str] | list[list[tuple[str, str, str | None]]]:
        """
        Return the text as lines, with hyphenation and cursor highlighting.
        If input_bool=True, returns segments with cursor highlighted in green.
        """
        lines, cursor_line, cursor_col = self._build_lines(self.text, self.cursor)
        if not input_bool:
            return lines
        else:
            result = []
            for i, line in enumerate(lines):
                if i == cursor_line and self.cursor <= len(self.text) and cursor_col < self.widths[i]:
                    # Highlight character at cursor
                    segments = []
                    text_before = line[:cursor_col]
                    char_at_cursor = line[cursor_col:cursor_col+1]
                    text_after = line[cursor_col+1:]
                    if text_before:
                        segments.append((text_before, "WHITE", None))
                    if char_at_cursor:
                        segments.append((char_at_cursor, "GREEN", None))
                    if text_after:
                        segments.append((text_after, "WHITE", None))
                    result.append(segments)
                else:
                    result.append([(line, "WHITE", None)])
            return result

class ConsoleUI():
    def __init__(self, todo_manager: ToDoManager):
        self.todo_manager = todo_manager
        self.theme = DarkAcademiaConsole(Palette)
        self.running = False
        self.sort_mode = None
        self.filter_mode = None
        self.input_bool = False
        self.width = None

        root_path = str(Path(__file__).resolve().parents[1])
        self.save_paths = (root_path + "/data/.todos.json", root_path + "/data/.automations.json")
        self.back = []

        self.menu_actions = {
            "home_menu" : {
                "m": [f"{self.theme.palette.SYMBOLS['MAIN']} (M) Main page", self.main_menu],
                "d": [f"{self.theme.palette.SYMBOLS['BOOKS']} (D) Diaries", self.diaries_menu],
                "q": [f"{self.theme.palette.SYMBOLS['GEAR']} (Q) Quit programmm", None]
            },
            "main_menu": {
                "a": [f"{self.theme.palette.SYMBOLS['PEN']} (A) Add ToDo", self.add_todo_start],
                "e": [f"{self.theme.palette.SYMBOLS['WRITING']} (E) Edit ToDo", self.standard_todo],
                "s": [f"{self.theme.palette.SYMBOLS['GLASS']} (S) Show ToDo", self.show_todo_menu],
                "c": [f"{self.theme.palette.SYMBOLS['CLIP']} (C) Change Status", self.change_status],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go backck", lambda: self.back.pop(-1)()]
            },
            "change_status_menu": {
                "enter": [f"{self.theme.palette.SYMBOLS['PEN']} ({self.theme.palette.SYMBOLS['ENTER']}) Submit", lambda: self.back.pop(-1)()],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go back", lambda: self.back.pop(-1)()]
            },
            "add_todo_start": {
                "enter": [f"{self.theme.palette.SYMBOLS['PEN']} ({self.theme.palette.SYMBOLS['ENTER']}) Submit", self.get_next_add_menu],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go back", lambda: self.back.pop(-1)()]
            },
            "standard_todo": {
                "i": [f"{self.theme.palette.SYMBOLS['WRITING']} (I) Enable Input", None],
                "esc": [f"{self.theme.palette.SYMBOLS['WRITING']} (Esc) Disable Input", None],
                "enter": [f"{self.theme.palette.SYMBOLS['PEN']} ({self.theme.palette.SYMBOLS['ENTER']}) Submit", None],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go back", lambda: self.back.pop(-1)()]
            },
            "dropdown_input": {
                "enter": [f"{self.theme.palette.SYMBOLS['PEN']} ({self.theme.palette.SYMBOLS['ENTER']}) Submit", None],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go back", lambda: self.back.pop(-1)()]
            }
        }

    def run(self):
        if Path(self.save_paths[0]).exists() and Path(self.save_paths[1]).exists():
            self.load()
        self.home_menu()

        self.save()

    def render_segments(self, stdscr, y, segments):
        """Zeile segmentweise mit Farben/Stilen ausgeben (robust gegen Überlauf)."""
        x = 0
        max_y, max_x = stdscr.getmaxyx()
        for text, color, style in segments:
            # Falls Terminal kleiner als erwartet ist: Text ggf. kürzen
            if y >= max_y:
                break  # außerhalb des sichtbaren Bereichs
            if x >= max_x:
                break  # kein Platz mehr in dieser Zeile
            if x + len(text) > max_x:
                text = text[:max_x - x - 1]
            if x > max_x:
                # Optionales Debug-Log
                # print(f"[DEBUG] Line overflowed: y={y}, x={x}, width={max_x}")
                pass

            attr = Palette.color(color)
            if style:
                attr |= Palette.STYLES[style]

            try:
                stdscr.addstr(y, x, text, attr)
            except Exception:
                # Curses kann bei bestimmten Unicode-Symbolen oder Farben trotzdem scheitern
                pass

            x += len(text)

    def get_input(self, row_selected: int, col_selected: int, key: str) -> tuple[int, int]:
        """
        Berechnet die neue Position im Menü-Grid abhängig von der Eingabe.
        
        Layout:
            Row 1: [1]
            Row 2: [1][2][3]
            Row 3: [1][2]
            Row 4: [1]
            Row 5: [1]
        """

        # Definiere, wie viele Spalten jede Zeile hat
        row_structure = {1: 1, 2: 3, 3: 2, 4: 1, 5: 1}
        max_row = len(row_structure)

        # Lokale Variablen (Kopie)
        r, c = row_selected, col_selected
        key = key.lower()

        if key == "up":
            if r > 1:
                if r == 2:  # von Zeile 2 -> Zeile 1
                    c = 1
                elif r == 3:  # von Zeile 3 -> Zeile 2
                    c = min(c, 3)
                elif r == 4:  # von Zeile 4 -> Zeile 3
                    c = 1  # FIXED: bleibt in Spalte 1
                elif r == 5:  # von Zeile 5 -> Zeile 4
                    c = 1
                r -= 1

        elif key == "down":
            if r < max_row:
                if r == 1:  # von Zeile 1 -> Zeile 2
                    c = 1
                elif r == 2:  # von Zeile 2 -> Zeile 3
                    c = min(c, 2)  # es gibt in Zeile 3 nur 2 Spalten
                elif r == 3:  # von Zeile 3 -> Zeile 4
                    c = 1
                elif r == 4:  # von Zeile 4 -> Zeile 5
                    c = 1
                r += 1

        elif key == "left":
            if c > 1:
                c -= 1

        elif key == "right":
            if c < row_structure[r]:
                c += 1

        return r, c
    
    def home_menu(self):
        site = "home_menu"
        s = Palette.SYMBOLS
        quote = self.theme.quote()

        def wrap_quote(quote: str, max_width: int) -> list[str]:
            """Bricht das Zitat in Zeilen um, die ins Terminal passen."""
            words = quote.split(" ")
            lines, current = [], ""
            for w in words:
                if len(current) + len(w) + 1 <= max_width - 6:
                    current += (" " if current else "") + w
                else:
                    lines.append(current)
                    current = w
            if current:
                lines.append(current)
            return lines

        def render_screen(stdscr, header_segments, quoting_lines, footer_segments,
                        spacer, horizontal, pad_top, pad_bottom):
            stdscr.erase()
            y = 0

            # Header
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            # obere Rahmenlinie
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            # obere vertikale Padding-Zeilen
            for _ in range(pad_top):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            # Zitat-Zeilen (mittig horizontal)
            for line in quoting_lines:
                pad_left = (self.width - len(line) + 2) // 2
                pad_right = self.width - len(line) - pad_left + 2
                quoting_segments = [
                    ("║", "IVORY", None),
                    (" " * pad_left, "IVORY", None),
                    (line, "GOLD", "BOLD"),
                    (" " * pad_right, "IVORY", None),
                    ("║", "IVORY", None),
                ]
                self.render_segments(stdscr, y, quoting_segments)
                y += 1

            # untere vertikale Padding-Zeilen
            for _ in range(pad_bottom):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            # untere Rahmenlinie
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            # Footer
            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()

            while True:
                # --- 1️⃣ Terminalgröße ---
                term_h, term_w = stdscr.getmaxyx()
                self.height = term_h - 1
                self.width = term_w - 4
                self.theme.width = self.width
                horizontal = s["EDGE_HORIZONTAL"] * (self.width + 2)
                spacer = self.theme._center_line()

                # --- 2️⃣ Layoutteile ---
                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['HOME']} Homee")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())
                quoting_lines = wrap_quote(quote, self.width)

                # --- 3️⃣ Vertikale Zentrierung ---
                # Zeilen, die kein Zitat sind (Header, Linien, Footer)
                static_lines = len(header_segments) + len(footer_segments) + 2  # obere+untere Rahmenlinie
                remaining = self.height - static_lines - len(quoting_lines)
                pad_top = max(0, remaining // 2)
                pad_bottom = max(0, remaining - pad_top)

                # --- 4️⃣ Zeichnen ---
                render_screen(stdscr, header_segments, quoting_lines,
                            footer_segments, spacer, horizontal, pad_top, pad_bottom)

                # --- 5️⃣ Input ---
                key = listener.get_key()
                if key:
                    key = key.lower()
                    if key in [key for key, _ in self.menu_actions[site].items()]:
                        self.back.append(self.home_menu)
                        self.menu_actions[site][key][1]()
                        return
                    elif key in ("q", "esc"):
                        break
                time.sleep(0.05)

    def main_menu(self):
        site = "main_menu"
        s = Palette.SYMBOLS

        # Auswahlzeiger-Index (1-basiert)
        line_selected = 1
        n = 0

        # --- Render-Funktion: zeichnet NUR; keine Logik/State hier drin ---
        def render_screen(stdscr, header_segments, upper_frame, title_frame, middle_frame,
                        rows_segments, lower_frame, footer_segments):
            stdscr.erase()
            y = 0
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            self.render_segments(stdscr, y, upper_frame);   y += 1
            self.render_segments(stdscr, y, title_frame);   y += 1
            self.render_segments(stdscr, y, middle_frame);  y += 1

            for row in rows_segments:
                self.render_segments(stdscr, y, row)
                y += 1

            self.render_segments(stdscr, y, lower_frame);   y += 1
            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()
            self.save()

            while True:
                self.todo_manager.update_automations()
                self.todo_manager.automatic_priority_update()
                self.todo_manager.automatic_status_update()
                # --------- INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()
                    if kl == "backspace" or kl == "a":
                        if kl == "a":
                            self.back.append(self.main_menu)

                        self.menu_actions[site][kl][1]()
                        # kehre zurueck, dieser Aufruf zeichnet sein eigenes UI
                        return
                    elif kl in ["e", "s", "c"]:
                        # Wir rendern gleich neu; zuerst Aktion mit aktuell selektiertem Todo
                        # (falls keine Todos: ignorieren)
                        todos_all = self.todo_manager.list_all()
                        todos = [t for t in todos_all if (not t.done) or (t.done and Date.today() - t.completed_at <= 4)]
                        if todos:
                            self.back.append(self.main_menu)
                            if kl == "e":
                                todo_dict = todos[line_selected - 1].to_dict()
                                self.menu_actions[site][kl][1](is_project=todo_dict["is_project"], dict=todo_dict, new=False)
                            else:
                                self.menu_actions[site][kl][1](todos[line_selected - 1])
                        # nach Aktion einfach weiterlaufen (Layout wird unten neu gebaut)
                    elif kl in ["up", "down"]:
                        todos_all = self.todo_manager.list_all()
                        todos_len = len([t for t in todos_all if (not t.done) or (t.done and Date.today() - t.completed_at <= 4)])
                        if kl == "up":
                            line_selected = max(1, line_selected - 1)
                            if line_selected < n + 1:
                                n = max(0, n - 1)

                        elif kl == "down":
                            line_selected = min(todos_len, line_selected + 1)
                            if line_selected > n + visual_todos:
                                n = min(max(0, todos_len - visual_todos), n + 1)

                    elif kl in ("q", "esc"):
                        break

                # --------- LAYOUT JEDES MAL NEU BERECHNEN ----------
                # aktuelle Terminalgröße
                self.height, self.width = stdscr.getmaxyx()[0] - 3, stdscr.getmaxyx()[1] - 4
                self.theme.width = self.width
                USED_SPACE = 9
                CUSTOM_SPACE = 0
                visual_todos = self.height - (USED_SPACE + CUSTOM_SPACE)

                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['MAIN']} Mainn")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())

                # Daten besorgen & filtern
                todos_all = self.todo_manager.list_all()
                todos = [t for t in todos_all if (not t.done) or (t.done and Date.today() - t.completed_at <= 4)]
                if not todos:
                    # Leerer Zustand: einfache Nachricht rendern
                    upper_frame = [(s["BRANCHING_LEFT"], "IVORY", None),
                                (s["EDGE_HORIZONTAL"] * (self.width - 2), "IVORY", None),
                                (s["BRANCHING_RIGHT"], "IVORY", None)]
                    title_frame = [(s["EDGE_VERTICAL"], "IVORY", None),
                                ("  No tasks to display".ljust(self.width - 2, " "), "WHITE", "BOLD"),
                                (s["EDGE_VERTICAL"], "IVORY", None)]
                    middle_frame = [(s["BRANCHING_LEFT"], "IVORY", None),
                                    (s["EDGE_HORIZONTAL"] * (self.width - 2), "IVORY", None),
                                    (s["BRANCHING_RIGHT"], "IVORY", None)]
                    lower_frame = middle_frame
                    rows_segments = []
                    render_screen(stdscr, header_segments, upper_frame, title_frame,
                                middle_frame, rows_segments, lower_frame, footer_segments)
                    time.sleep(0.05)
                    continue  # zurück zur Schleife (Input/LAYOUT weiter)

                # Spaltenbreiten (Header + Inhalte)
                lengths = [
                    max([len(t.title) for t in todos] + [len("Title")]) + 2,
                    max([len(str(t.deadline)) for t in todos] + [len("Deadline")]),
                    max([len(t.priority.name) for t in todos] + [len("Priority")]),
                    max([len(t.category) for t in todos] + [len("Category")]),
                    max([len(f"{t.get_est_time()[0]}h{t.get_est_time()[-1]}min") for t in todos] + [len("Estimated Time")]),
                    max([len(t.dependancy_of[0].title) if t.dependancy_of else 0 for t in todos] + [len("Dependency of")]),
                    max([len(t.get_status()) for t in todos] + [len("Status")]),
                ]

                # linker/rechter Außen-Padding für symmetrischen Rahmen
                # "space" ~ Rahmen + 6 Vertikalbalken + Kreuzungen ≈ 18 (wie bei dir)
                space = 18
                total_content = sum(lengths)
                if total_content + space < self.width:
                    free = self.width - (total_content + space)
                    padding_left  = free // 2 + (free % 2)  # linke Seite minimal größer
                    padding_right = free // 2
                else:
                    padding_left = padding_right = 0

                upper_frame = []
                length_n = 1
                for length in lengths:
                    if length_n == 1:
                        upper_frame.append((s["BRANCHING_LEFT"], "IVORY", None))
                        upper_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_left) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    elif length_n == 7:
                        upper_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_right) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    else:
                        upper_frame.append((s["EDGE_HORIZONTAL"] * (length + 2) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    if length_n == 7:
                        upper_frame.append((s["BRANCHING_RIGHT"], "IVORY", None))
                    else:
                        upper_frame.append((s["BRANCHING_TOP"], "IVORY", None))
                    length_n += 1
                
                middle_frame = []
                length_n = 1
                for length in lengths:
                    if length_n == 1:
                        middle_frame.append((s["BRANCHING_LEFT"], "IVORY", None))
                        middle_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_left) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    elif length_n == 7:
                        middle_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_right) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    else:
                        middle_frame.append((s["EDGE_HORIZONTAL"] * (length + 2) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    if length_n == 7:
                        middle_frame.append((s["BRANCHING_RIGHT"], "IVORY", None))
                    else:
                        middle_frame.append((s["BRANCHING_CROSS"], "IVORY", None))
                    length_n += 1
                
                title_frame = [
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f"   Title" + (lengths[0] - len("Title") - 1 + padding_left) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f" Deadline" + (lengths[1] - len("Deadline") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f" Priority" + (lengths[2] - len("Priority") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f" Category" + (lengths[3] - len("Category") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f" Estimated Time" + (lengths[4] - len("Estimated Time") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (f" Dependancy of" + (lengths[5] - len("Dependancy of") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (" " * padding_right + f" Status" + (lengths[6] - len("Status") + 1) * " ", "WHITE", "BOLD"),
                    (s["EDGE_VERTICAL"], "IVORY", None)
                ]

                lower_frame = []
                length_n = 1
                for length in lengths:
                    if length_n == 1:
                        lower_frame.append((s["BRANCHING_LEFT"], "IVORY", None))
                        lower_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_left) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    elif length_n == 7:
                        lower_frame.append((s["EDGE_HORIZONTAL"] * (length + 2 + padding_right) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    else:
                        lower_frame.append((s["EDGE_HORIZONTAL"] * (length + 2) if length != 1 else s["EDGE_HORIZONTAL"] * (length + 1), "IVORY", None))
                    if length_n == 7:
                        lower_frame.append((s["BRANCHING_RIGHT"], "IVORY", None))
                    else:
                        lower_frame.append((s["BRANCHING_BOTTOM"], "IVORY", None))
                    length_n += 1

                # Datenzeilen (inkl. Cursorpfeil)
                rows_segments = []
                for idx, task in enumerate(todos, start=1):
                    # Farben je Status
                    if task.done and not task.in_progress:
                        name_color = status_color = "GREEN"
                    elif (not task.done) and (not task.in_progress) and (not task.is_overdue()):
                        name_color = status_color = "WHITE"
                    elif (not task.done) and (not task.in_progress) and task.is_overdue():
                        name_color = status_color = "RED"
                    elif (not task.done) and task.in_progress and task.is_overdue():
                        name_color = status_color = "DARK_ORANGE"
                    else:
                        name_color = status_color = "LIGHT_ORANGE"

                    row = [
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (f" {s['POINT_TRIANGLE']}" if line_selected == idx else f"  ", "WHITE", "BOLD"),
                        (f" {task.title}" + (lengths[0] - len(task.title) - 1 + padding_left) * " ", name_color, "BOLD"),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (f" {str(task.deadline)}" + (lengths[1] - len(str(task.deadline)) + 1) * " ", "WHITE", "ITALIC"),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (f" {task.priority.name}" + (lengths[2] - len(task.priority.name) + 1) * " ", "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (f" {task.category}" + (lengths[3] - len(task.category) + 1) * " ", "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (f" {task.get_est_time()[0]}h{task.get_est_time()[-1]}min"
                        + (lengths[4] - len(f"{task.get_est_time()[0]}h{task.get_est_time()[-1]}min") + 1) * " ", "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        ((f" {task.dependancy_of[0].title}" + (lengths[5] - len(task.dependancy_of[0].title) + 1) * " ")
                        if task.dependancy_of else (" " * (lengths[5] + 2)), "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (" " * padding_right + f" {task.get_status()}" + (lengths[6] - len(task.get_status()) + 1) * " ", status_color, "BOLD"),
                        (s["EDGE_VERTICAL"], "IVORY", None)
                    ]
                    rows_segments.append(row)

                # --------- RENDER MIT AKTUELLER BREITE/HÖHE ----------
                render_screen(stdscr, header_segments, upper_frame, title_frame,
                            middle_frame, rows_segments[n:n+visual_todos], lower_frame, footer_segments)

                time.sleep(0.05)

    def add_todo_start(self):
        site = "add_todo_start"
        s = Palette.SYMBOLS

        # Auswahlzeiger-Index (1-basiert)
        line_selected = 1

        # --- Render-Funktion: zeichnet NUR; keine Logik/State hier drin ---
        def render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom):
            stdscr.erase()
            y = 0
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for _ in range(pad_top):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            for row in rows_segments:
                self.render_segments(stdscr, y, row)
                y += 1
            
            for _ in range(pad_bottom):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()

            while True:
                # --------- INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()
                    if kl == "backspace":
                        self.menu_actions[site][kl][1]()
                        # kehre zurueck, dieser Aufruf zeichnet sein eigenes UI
                        return
                        # nach Aktion einfach weiterlaufen (Layout wird unten neu gebaut)
                    elif kl == "enter":
                        self.back.append(self.add_todo_start)
                        self.menu_actions[site][kl][1](line_selected=line_selected)()
                    
                    elif kl in ["up", "down"]:
                        if kl == "up":
                            line_selected = max(1, line_selected - 1)

                        elif kl == "down":
                            line_selected = min(3, line_selected + 1)

                    elif kl in ("q", "esc"):
                        break

                # --------- LAYOUT JEDES MAL NEU BERECHNEN ----------
                # aktuelle Terminalgröße
                self.height, self.width = stdscr.getmaxyx()[0] - 1, stdscr.getmaxyx()[1] - 4
                self.theme.width = self.width

                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['WRITING']} Add Todo - Type Selectionn")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())
                horizontal = s['EDGE_HORIZONTAL'] * (self.width + 2)
                spacer = self.theme._center_line()

                inner_width = 19  # Breite deiner Box-Inhalte (ohne Rahmen)
                total_space = self.width - inner_width
                padding_left = total_space // 2
                padding_right = total_space - padding_left

                rows_segments = [
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_TOP'] + 19 * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_TOP'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 1 else "  ", "WHITE", "BOLD"),
                        (f"ToDo (Standard)" + " ", "WHITE", "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 2 else "  ", "WHITE", "BOLD"),
                        (f"Project" + 9 * " ", "WHITE", "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 3 else "  ", "WHITE", "BOLD"),
                        (f"Automation" + 6 * " ", "WHITE", "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_BOTTOM'] + 19 * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_BOTTOM'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ]
                ]

                static_lines = len(header_segments) + len(footer_segments) + 2  # obere+untere Rahmenlinie
                remaining = self.height - static_lines - len(rows_segments)
                pad_top = remaining // 2
                pad_bottom = (remaining - pad_top) + (remaining % 2)

                render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom)

                time.sleep(0.05)

    def standard_todo(self, is_project: bool = False, dict: dict = None, new: bool = True):
        site = "standard_todo"
        s = Palette.SYMBOLS

        row_selected = 1
        col_selected = 1
        self.input_bool = False

        # --- Input-Objekte definieren ---
        inputs = {
            "title": InputField(width=53),
            "category": self.dropdown_input,
            "deadline": MaskedInputField("mm-dd-yyyy"),
            "priority": self.dropdown_input,
            "est_time": MaskedInputField("00h00min"),
            "tags": InputField(width=37),
            "dependency": InputField(width=57),
            "description": MultilineInputField([59, 74, 74, 74, 74, 74]),
        }

        if not dict:
            # Auswahlzeiger-Index (1-basiert)
            category = "Philosophy"
            priority = "blocking"
            
        else:
            category = dict["category"]
            priority = dict["priority"]
            est_time = dict["est_time"]

            if type(est_time) == float:
                default_est_time = f"{int(est_time):02d}h{int((float(est_time) - int(est_time)) * 60):02d}min" if est_time is not None and isinstance(est_time, (int, float)) else "00h00min"
            elif type(est_time) == str:
                default_est_time = est_time
            elif est_time is None:
                default_est_time = "00h00min"

            inputs["title"].text = dict["title"]
            if type(dict["deadline"]) == Date:
                inputs["deadline"] = MaskedInputField("mm-dd-yyyy", default_value=repr(dict["deadline"]))
            else:
                inputs["deadline"] = MaskedInputField("mm-dd-yyyy", default_value=dict["deadline"])
            inputs["est_time"] = MaskedInputField("00h00min", default_value=default_est_time)
            inputs["tags"].text = ", ".join(dict["tags"])
            if type(dict["dependancy_of"]) == list:
                inputs["dependency"].text = dict["dependancy_of"][0]["title"] if dict["dependancy_of"] else ""
            elif type(dict["dependancy_of"]) == str:
                inputs["dependency"].text = dict["dependancy_of"]
            inputs["description"].text = dict["description"]

        # --- Zuordnung: Grid-Position -> Feldname ---
        active_map = {
            (1, 1): "title",
            (2, 1): "category",
            (2, 2): "deadline",
            (2, 3): "priority",
            (3, 1): "est_time",
            (3, 2): "tags",
            (4, 1): "dependency",
            (5, 1): "description",
        } 

        # --- Render-Funktion: zeichnet NUR; keine Logik/State hier drin ---
        def render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom):
            stdscr.erase()
            y = 0
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1
            
            for _ in range(pad_top):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            try:
                for idx, row in enumerate(rows_segments, start=1):
                    self.render_segments(stdscr, y, row)
                    y += 1
            except ValueError:
                raise ValueError(f"Row {idx} is wrong!")
            
            for _ in range(pad_bottom):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()

            while True:
                # --------- INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()

                    # --- Beenden / Navigation ---
                    if kl == "enter" and not self.input_bool:
                        est_time_float = float(inputs["est_time"].get_display_text().split("h")[0]) + float(inputs["est_time"].get_display_text().split("h")[1].replace("min", "")) / 60
                        todo_dict = {
                                "title": inputs["title"].text,
                                "category": category,
                                "deadline": inputs["deadline"].get_display_text(),
                                "priority": priority,
                                "est_time": est_time_float,
                                "tags": inputs["tags"].text.split(", "), 
                                "description": inputs["description"].text,
                                "is_project": is_project
                            }
                        if new:
                            # try:
                                new_todo = ToDo.from_dict(todo_dict)
                                self.todo_manager.add_todo(new_todo)
                                if inputs["dependency"].text:
                                    self.todo_manager.add_dependancy_of(new_todo, title=inputs["dependency"].text)
                                self.back.pop(-1)
                                self.main_menu()
                            # except Exception as e:
                                # import tkinter.messagebox; tkinter.messagebox.showerror("Fehler", str(e))
                                # continue
                        else:
                            # try:
                                self.todo_manager.update_todo(todo_dict, dict["title"], dict["id"])
                                if inputs["dependency"].text:
                                    for task in self.todo_manager.get_todo(title=inputs["dependency"].text):
                                        if task not in self.todo_manager.get_todo(todo_dict["title"], dict["id"])[0]:
                                            self.todo_manager.add_dependancy_of(self.todo_manager.get_todo(todo_dict["title"], dict["id"]), title=inputs["dependency"].text)
                            # except Exception as e:
                                # import tkinter.messagebox; tkinter.messagebox.showerror("Fehler", str(e))

                    if kl == "backspace" and not self.input_bool:
                        self.menu_actions[site][kl][1]()
                        return
                    elif kl == "i" and not self.input_bool:
                        self.input_bool = not self.input_bool  # toggle input mode
                    elif kl == "esc" and self.input_bool:
                        self.input_bool = not self.input_bool
                    elif kl in ("q"):
                        break

                    # --- Navigation im Grid ---
                    elif not self.input_bool and kl in ["up", "down", "left", "right"]:
                        row_selected, col_selected = self.get_input(row_selected, col_selected, kl)

                    # --- Eingabemodus aktiv ---
                    elif self.input_bool:
                        field_name = active_map.get((row_selected, col_selected))
                        if not field_name:
                            continue  # kein editierbares Feld

                        field = inputs[field_name]

                        # Masked Input (Deadline, Estimated Time)
                        if isinstance(field, MaskedInputField):
                            if kl.isdigit():
                                field.insert(kl)
                            elif kl == "backspace":
                                field.backspace()

                        # Multiline Input (Description)
                        elif isinstance(field, MultilineInputField):
                            if len(kl) == 1 and kl.isprintable():
                                field.insert(key)
                            elif kl == "backspace":
                                field.backspace()

                        # Normal Input (Title, Tags, Dependency)
                        elif isinstance(field, InputField):
                            if len(kl) == 1 and kl.isprintable():
                                field.insert(key)
                            elif kl == "backspace":
                                field.backspace()
                            elif kl == "left":
                                field.move_left()
                            elif kl == "right":
                                field.move_right()
                        
                        else:
                            todo_dict = {
                                "title": inputs["title"].text,
                                "category": category,
                                "deadline": inputs["deadline"].get_display_text(),
                                "priority": priority,
                                "est_time": inputs["est_time"].get_display_text(),
                                "tags": inputs["tags"].text.split(", "), 
                                "dependancy_of": inputs["dependency"].text,
                                "description": inputs["description"].text,
                                "is_project": is_project
                            }
                            if field_name == "category":
                                self.back.append(self.standard_todo)
                                self.dropdown_input("category", todo_dict, new)
                            elif field_name == "priority":
                                self.back.append(self.standard_todo)
                                self.dropdown_input("priority", todo_dict, new)

                # --------- LAYOUT JEDES MAL NEU BERECHNEN ----------
                # aktuelle Terminalgröße
                self.height, self.width = stdscr.getmaxyx()[0] - 1, stdscr.getmaxyx()[1] - 4
                self.theme.width = self.width

                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['WRITING']} Add Todo - Information Inputs" if new else f"{self.theme.palette.SYMBOLS['WRITING']} Edit Todo - Information Inputs")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())
                horizontal = s['EDGE_HORIZONTAL'] * (self.width + 2)
                spacer = self.theme._center_line()

                inner_width = 76  # Breite deiner Box-Inhalte (ohne Rahmen)
                total_space = self.width - inner_width
                padding_left = max(1, total_space // 2)
                padding_right = max(1, total_space - padding_left)

                rows_segments = [
                    [
                        (s["EDGE_VERTICAL"] + " " * (padding_left + 6) + s["CORNER_LEFT_TOP"] + 64 * s["EDGE_HORIZONTAL"] + s["CORNER_RIGHT_TOP"] + " " * (padding_right + 6) + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * (padding_left + 6) + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 1 and row_selected == 1) else " " * 2, "WHITE", "BOLD"),
                        (" Title:", "WHITE", "BOLD"),
                        *([(" " + inputs["title"].get_display_text(self.input_bool), "WHITE", None)] if not self.input_bool else [(" ", "WHITE", None)] + inputs["title"].get_display_text(self.input_bool)),
                        (" " + s["EDGE_VERTICAL"] + " " * (padding_right + 6) + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * (padding_left + 6) + s["CORNER_LEFT_BOTTOM"] + 64 * s["EDGE_HORIZONTAL"] + s["CORNER_RIGHT_BOTTOM"] + " " * (padding_right + 6) + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * padding_left + s["CORNER_LEFT_TOP"] + 26 * s["EDGE_HORIZONTAL"] + s["BRANCHING_TOP"] + 24 * s["EDGE_HORIZONTAL"] + s["BRANCHING_TOP"] + 24 * s["EDGE_HORIZONTAL"] + s["CORNER_RIGHT_TOP"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * padding_left + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 1 and row_selected == 2) else " " * 2, "WHITE", "BOLD"),
                        (f" Category: {category}" + (13 - len(category)) * " ", "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 2 and row_selected == 2) else " " * 2, "WHITE", "BOLD"),
                        (" Deadline: " + inputs["deadline"].get_display_text() + " ", "WHITE", None),
                        (s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 3 and row_selected == 2) else " " * 2, "WHITE", "BOLD"),
                        (f" Priority: {priority}" + (10 - len(priority)) * " ", "WHITE", None),
                        (" " + s["EDGE_VERTICAL"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * padding_left + s["BRANCHING_LEFT"] + 26 * s["EDGE_HORIZONTAL"] + s["BRANCHING_BOTTOM"] + s["EDGE_HORIZONTAL"] + s["BRANCHING_TOP"] + 22 * s["EDGE_HORIZONTAL"] + s["BRANCHING_BOTTOM"] + 24 * s["EDGE_HORIZONTAL"] + s["BRANCHING_RIGHT"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + " " * padding_left + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 1 and row_selected == 3) else " " * 2, "WHITE", "BOLD"),
                        (" Estimated Time: " + inputs["est_time"].get_display_text(), "WHITE", None),
                        (" " + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 2 and row_selected == 3) else " " * 2, "WHITE", "BOLD"),
                        *([(" Tags: " + inputs["tags"].get_display_text(self.input_bool), "WHITE", None)] if not self.input_bool else [(" Tags: ", "WHITE", None)] + inputs["tags"].get_display_text(self.input_bool)),
                        (" " + s["EDGE_VERTICAL"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["BRANCHING_LEFT"] + 28 * s["EDGE_HORIZONTAL"] + s["BRANCHING_BOTTOM"] + 47 * s["EDGE_HORIZONTAL"] + s["BRANCHING_RIGHT"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 1 and row_selected == 4) else " " * 2, "WHITE", "BOLD"),
                        *([(" Dependency of: " + inputs["dependency"].get_display_text(self.input_bool), "WHITE", None)] if not self.input_bool else [(" Dependency of: ", "WHITE", None)] + inputs["dependency"].get_display_text(self.input_bool)),
                        (" " + s["EDGE_VERTICAL"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["BRANCHING_LEFT"] + 76 * s["EDGE_HORIZONTAL"] + s["BRANCHING_RIGHT"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ],
                    [
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["EDGE_VERTICAL"], "IVORY", None),
                        (" " + s["POINT_TRIANGLE"] if (col_selected == 1 and row_selected == 5) else " " * 2, "WHITE", "BOLD"),
                        (" Description:", "WHITE", "BOLD"),
                        (" " + inputs["description"].get_lines()[0], "WHITE", None),
                        (" " + s["EDGE_VERTICAL"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ]
                ]

                static_lines = len(header_segments) + len(footer_segments) + 2  # obere+untere Rahmenlinie
                # Berechne verbleibenden Platz, bevor Description hinzugefügt wird
                remaining = self.height - static_lines - (len(rows_segments) + 1)

                # Beschreibung bekommt max. 5 Zeilen, aber nie mehr als (remaining - 2)
                # damit mindestens 1 Zeile Padding oben und unten bleibt
                description_lines = min(5, max(1, remaining - 2))
                inputs["description"].widths = [59] + [74] * description_lines

                # Übriger Platz nach Description
                remaining = self.height - static_lines - (len(rows_segments) + 1 + description_lines)

                # Padding gleichmäßig verteilen, aber mindestens 1 Zeile
                pad_top = max(1, remaining // 2)
                pad_bottom = max(1, remaining - pad_top)

                desc_lines = inputs["description"].get_lines()
                for i in range(description_lines):
                    line_text = desc_lines[i + 1] if i + 1 < len(desc_lines) else ""
                    rows_segments.append([
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["EDGE_VERTICAL"] + " ", "IVORY", None),
                        (line_text, "WHITE", None),
                        (" " + s["EDGE_VERTICAL"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ])

                rows_segments.append([
                        (s["EDGE_VERTICAL"] + padding_left * " " + s["CORNER_LEFT_BOTTOM"] + 76 * s["EDGE_HORIZONTAL"] + s["CORNER_RIGHT_BOTTOM"] + " " * padding_right + s["EDGE_VERTICAL"], "IVORY", None)
                    ])

                
                render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom)

                time.sleep(0.05)

    def dropdown_input(self, field_name: str, dict: dict, new: bool = True):
        site = "dropdown_input"
        s = Palette.SYMBOLS

        if field_name == "priority": 
            input_type = "Priority"
            input_values = [key for key, _ in Priority.ALLOWED_PRIORITIES.items()]
            line_selected = input_values.index(dict["priority"]) + 1
        elif field_name == "category":
            input_type = "Category"
            input_values = ToDo.CATEGORIES
            line_selected = input_values.index(dict["category"]) + 1

        # --- Render-Funktion: zeichnet NUR; keine Logik/State hier drin ---
        def render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom):
            stdscr.erase()
            y = 0
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for _ in range(pad_top-2):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1

            self.render_segments(stdscr, y, [(f"{s['EDGE_VERTICAL']}" + ((self.width - len(input_type)) // 2) * " ", "IVORY", None),
                                             (input_type, "GOLD", "BOLD"),
                                             (" " * (((self.width - len(input_type)) // 2) + 2 + ((self.width - len(input_type)) % 2)) + s["EDGE_VERTICAL"], "IVORY", None)])
            y += 1

            stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
            y += 1

            for row in rows_segments:
                self.render_segments(stdscr, y, row)
                y += 1
            
            for _ in range(pad_bottom):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()

            while True:
                # --------- INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()
                    if kl == "backspace":
                        self.menu_actions[site][kl][1]()
                        # kehre zurueck, dieser Aufruf zeichnet sein eigenes UI
                        return
                        # nach Aktion einfach weiterlaufen (Layout wird unten neu gebaut)
                    elif kl == "enter":
                        self.back.pop(-1)
                        if field_name == "category":
                            dict["category"] = input_values[line_selected - 1]
                        elif field_name == "priority":
                            dict["priority"] = input_values[line_selected - 1]
                        
                        self.standard_todo(is_project=dict["is_project"],dict=dict, new=new)
                    
                    elif kl in ["up", "down"]:
                        if kl == "up":
                            line_selected = max(1, line_selected - 1)

                        elif kl == "down":
                            line_selected = min(len(input_values), line_selected + 1)

                    elif kl in ("q", "esc"):
                        break

                # --------- LAYOUT JEDES MAL NEU BERECHNEN ----------
                # aktuelle Terminalgröße
                self.height, self.width = stdscr.getmaxyx()[0] - 1, stdscr.getmaxyx()[1] - 4
                self.theme.width = self.width

                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['WRITING']} Add Todo - {input_type} Selectionn" if new else f"{self.theme.palette.SYMBOLS['WRITING']} Edit Todo - {input_type} Selectionn")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())
                horizontal = s['EDGE_HORIZONTAL'] * (self.width + 2)
                spacer = self.theme._center_line()

                inner_width = max([len(input_value) for input_value in input_values]) + 4 # Breite deiner Box-Inhalte (ohne Rahmen)
                total_space = self.width - inner_width
                padding_left = total_space // 2
                padding_right = total_space - padding_left

                rows_segments = [
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_TOP'] + inner_width * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_TOP'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ]
                ]
                for idx, input_value in enumerate(input_values, start=1):
                    rows_segments.append([
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == idx else "  ", "WHITE", "BOLD"),
                        (input_value + " " * (inner_width - len(input_value) - 4), "WHITE", "BOLD"),
                        (" " + f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ])

                rows_segments.append([
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_BOTTOM'] + inner_width * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_BOTTOM'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ])

                static_lines = len(header_segments) + len(footer_segments) + 2  # obere+untere Rahmenlinie
                remaining = self.height - static_lines - len(rows_segments)
                pad_top = remaining // 2
                pad_bottom = (remaining - pad_top) + (remaining % 2)

                render_screen(stdscr, header_segments, horizontal, spacer, rows_segments, footer_segments, pad_top, pad_bottom)

                time.sleep(0.05)

    def add_automation():
        pass

    def get_next_add_menu(self, line_selected: int):
        if line_selected == 1:
            return self.standard_todo(is_project=False)
        
        elif line_selected == 2:
            return self.standard_todo(is_project=True)
        
        elif line_selected == 3:
            return self.add_automation
    
    def edit_todo_menu(self, todo: ToDo):
        return
    
    def change_status(self, todo: ToDo):
        site = "change_status_menu"
        s = Palette.SYMBOLS

        # Auswahlzeiger-Index (1-basiert)
        line_selected = 1

        # --- Render-Funktion: zeichnet NUR; keine Logik/State hier drin ---
        def render_screen(stdscr, header_segments, horizontal, spacer, name_row, rows_segments, footer_segments, pad_top, pad_bottom):
            stdscr.erase()
            y = 0
            for seg in header_segments:
                self.render_segments(stdscr, y, seg)
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for _ in range(pad_top - 2):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1
            
            self.render_segments(stdscr, y, name_row)
            y += 1

            stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
            y += 1

            for row in rows_segments:
                self.render_segments(stdscr, y, row)
                y += 1
            
            for _ in range(pad_bottom):
                stdscr.addstr(y, 0, spacer, Palette.color("IVORY"))
                y += 1
            
            self.render_segments(stdscr, y, [
                (f"{s['BRANCHING_LEFT']}{horizontal}{s['BRANCHING_RIGHT']}", "IVORY", None)
            ])
            y += 1

            for seg in footer_segments:
                self.render_segments(stdscr, y, seg)
                y += 1

            stdscr.refresh()

        with CursesKeyListener() as listener:
            stdscr = listener.stdscr
            Palette.init_colors()

            while True:
                # --------- INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()
                    if kl == "backspace" or kl == "a":
                        self.menu_actions[site][kl][1]()
                        # kehre zurueck, dieser Aufruf zeichnet sein eigenes UI
                        return
                        # nach Aktion einfach weiterlaufen (Layout wird unten neu gebaut)
                    elif kl == "enter":
                        if line_selected == 1:
                            self.todo_manager.mark_done(todo.title, todo.id)
                            self.menu_actions[site][kl][1]()
                        if line_selected == 2:
                            self.todo_manager.set_in_progress(todo.title, todo.id)
                            self.menu_actions[site][kl][1]()
                        if line_selected == 3:
                            self.todo_manager.mark_undone(todo.title, todo.id)
                            self.menu_actions[site][kl][1]()
                    elif kl in ["up", "down"]:
                        if kl == "up":
                            line_selected = max(1, line_selected - 1)

                        elif kl == "down":
                            line_selected = min(3, line_selected + 1)

                    elif kl in ("q", "esc"):
                        break

                # --------- LAYOUT JEDES MAL NEU BERECHNEN ----------
                # aktuelle Terminalgröße
                self.height, self.width = stdscr.getmaxyx()[0] - 1, stdscr.getmaxyx()[1] - 4
                self.theme.width = self.width

                header_segments = self.theme.header(f"{self.theme.palette.SYMBOLS['PEN']} Status Change")
                footer_segments = self.theme.footer(value[0] for _, value in self.menu_actions[site].items())
                horizontal = s['EDGE_HORIZONTAL'] * (self.width + 2)
                spacer = self.theme._center_line()

                inner_width = 15  # Breite deiner Box-Inhalte (ohne Rahmen)
                total_space = self.width - inner_width
                padding_left = total_space // 2
                padding_right = total_space - padding_left

                status_colors = ["GREEN" if todo.done else "WHITE", "YELLOW" if todo.in_progress and not todo.done else "WHITE", "RED" if not todo.done and not todo.in_progress else "WHITE"]

                rows_segments = [
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_TOP'] + 15 * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_TOP'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 1 else "  ", "WHITE", "BOLD"),
                        (f"Done" + 8 * " ", status_colors[0], "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 2 else "  ", "WHITE", "BOLD"),
                        (f"In Progress" + " ", status_colors[1], "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (f"{s['EDGE_VERTICAL']} ", "IVORY", None),
                        (f"{s['POINT_TRIANGLE']} " if line_selected == 3 else "  ", "WHITE", "BOLD"),
                        (f"Undone" + 6 * " ", status_colors[2], "BOLD"),
                        (f"{s['EDGE_VERTICAL']}" + padding_right * " " + f"{s['EDGE_VERTICAL']}", "IVORY", None)
                    ],
                    [
                        (f"{s['EDGE_VERTICAL']}" + padding_left * " ", "IVORY", None),
                        (s['CORNER_LEFT_BOTTOM'] + 15 * s['EDGE_HORIZONTAL'] + s['CORNER_RIGHT_BOTTOM'], "IVORY", None),
                        (padding_right * " " + f"{s['EDGE_VERTICAL']}" , "IVORY", None)
                    ]
                ]

                name_row = [
                    (s["EDGE_VERTICAL"], "IVORY", None),
                    (" " * ((self.width - len(todo.title)) // 2 + 1), "WHITE", None),
                    (todo.title, "GOLD", "BOLD"),
                    (" " * (((self.width - len(todo.title)) // 2) + 1 + ((self.width - len(todo.title)) % 2)), "WHITE", None),
                    (s["EDGE_VERTICAL"], "IVORY", None)
                ]

                static_lines = len(header_segments) + len(footer_segments) + 2  # obere+untere Rahmenlinie
                remaining = self.height - static_lines - len(rows_segments)
                pad_top = remaining // 2
                pad_bottom = (remaining - pad_top) + (remaining % 2)

                render_screen(stdscr, header_segments, horizontal, spacer, name_row, rows_segments, footer_segments, pad_top, pad_bottom)

                time.sleep(0.05)

    def show_todo_menu(self, todo: ToDo):
        return
    
    def diaries_menu(self):
        return
    
    def load(self):
        self.todo_manager.load(self.save_paths[0])
        self.todo_manager.load_automations(self.save_paths[1])
    def save(self):
        self.todo_manager.save(self.save_paths[0])
        self.todo_manager.save_automations(self.save_paths[1])