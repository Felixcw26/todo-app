from core.date_type import Date
from core.todo_type import ToDo, Priority
from core.todo_manager import ToDoManager
from core.key_listener import CursesKeyListener
from gui.dark_academia_theme import DarkAcademiaConsole, Palette
import time
import numpy as np 
import os

class ConsoleUI():
    def __init__(self, todo_manager: ToDoManager, theme: DarkAcademiaConsole, width: int = 120):
        self.todo_manager = todo_manager
        self.theme = theme
        self.running = False
        self.sort_mode = None
        self.filter_mode = None
        self.width = width
        self.save_paths = ("C:/Users/felixcipher/Documents/coding/todo-app/data/.todos.json", "C:/Users/felixcipher/Documents/coding/todo-app/data/.automations.json")
        self.back = self.home_menu

        self.menu_actions = {
            "home_menu" : {
                "m": [f"{self.theme.palette.SYMBOLS['MAIN']} (M) Main page", self.main_menu],
                "d": [f"{self.theme.palette.SYMBOLS['BOOKS']} (D) Diaries", self.diaries_menu],
                "q": [f"{self.theme.palette.SYMBOLS['GEAR']} (Q) Quit programmm", None]
            },
            "main_menu": {
                "a": [f"{self.theme.palette.SYMBOLS['PEN']} (A) Add ToDo", None],
                "e": [f"{self.theme.palette.SYMBOLS['WRITING']} (E) Edit ToDo", self.edit_todo_menu],
                "s": [f"{self.theme.palette.SYMBOLS['GLASS']} (S) Show ToDo", self.show_todo_menu],
                "c": [f"{self.theme.palette.SYMBOLS['CLIP']} (C) Change Status", self.change_status],
                "backspace": [f"{self.theme.palette.SYMBOLS['LEFT_ARROW']} ({self.theme.palette.SYMBOLS['BACKSPACE']}) Go backck", self.back]
            }
        }

    def render_segments(self, stdscr, y, segments):
        """Zeile segmentweise mit Farben/Stilen ausgeben."""
        x = 0
        for text, color, style in segments:
            attr = Palette.color(color)
            if style:
                attr |= Palette.STYLES[style]
            stdscr.addstr(y, x, text, attr)
            x += len(text)

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

            while True:
                # --------- 1) INPUT LESEN (sofort Cursor anpassen) ----------
                key = listener.get_key()
                if key:
                    kl = key.lower()
                    if kl == "backspace" or kl == "a":
                        self.menu_actions[site][kl][1]()
                        # kehre zurueck, dieser Aufruf zeichnet sein eigenes UI
                        return
                    elif kl in ["e", "s", "c"]:
                        # Wir rendern gleich neu; zuerst Aktion mit aktuell selektiertem Todo
                        # (falls keine Todos: ignorieren)
                        todos_all = self.todo_manager.list_all()
                        todos = [t for t in todos_all if (not t.done) or (t.done and Date.today() - t.completed_at <= 4)]
                        if todos:
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

                # --------- 2) LAYOUT JEDES MAL NEU BERECHNEN ----------
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
                    max([len(t.dependancy_of[0].title) if t.dependancy_of else 0 for t in todos] + [len("Dependancy of")]),
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
                        name_color = status_color = "YELLOW"
                    else:
                        name_color = status_color = "GRAY"

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

                # --------- 3) RENDER MIT AKTUELLER BREITE/HÖHE ----------
                render_screen(stdscr, header_segments, upper_frame, title_frame,
                            middle_frame, rows_segments[n:n+visual_todos], lower_frame, footer_segments)

                time.sleep(0.05)
    
    def add_todo_menu(self):
        return
    
    def edit_todo_menu(self, todo: ToDo):
        return
    
    def change_status(self, todo: ToDo):
        return
    
    def show_todo_menu(self, todo: ToDo):
        return
    
    def diaries_menu(self):
        return
    def save(self):
        self.todo_manager.save(self.save_paths)