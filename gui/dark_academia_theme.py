import curses
import random
import sys
from time import sleep
from wcwidth import wcswidth
from core.date_type import Date

class Palette:
    """Definiert Farbpaar-IDs und Style-Konstanten für curses."""

    COLORS = {
        "GOLD": 178,
        "BRONZE": 136,
        "IVORY": 230,
        "GRAY": 244,
        "RED": 124,
        "GREEN": 107,
        "BLUE": 110,
        "WHITE": 231,
        "YELLOW": 220
    }

    STYLES = {
        "BOLD": curses.A_BOLD,
        "ITALIC": getattr(curses, "A_ITALIC", 0),
        "DIM": curses.A_DIM,
        "UNDERLINE": curses.A_UNDERLINE,
        "REVERSE": curses.A_REVERSE,
        "NORMAL": curses.A_NORMAL,
    }

    SYMBOLS = {
        "CORNER_LEFT_TOP": "╔",
        "CORNER_RIGHT_TOP": "╗",
        "CORNER_LEFT_BOTTOM": "╚",
        "CORNER_RIGHT_BOTTOM": "╝",
        "EDGE_HORIZONTAL": "═",
        "EDGE_VERTICAL": "║",
        "BRANCHING_LEFT": "╠",
        "BRANCHING_RIGHT": "╣",
        "BRANCHING_TOP": "╦",
        "BRANCHING_BOTTOM": "╩",
        "BRANCHING_CROSS": "╬",
        "CANDLE" : "🕯️",
        "GEAR" : "⚙️",
        "BOOK" : "📖",
        "ATTENTION" : "⚠️",
        "HOOK" : "✔️",
        "PEN" : "✒️",
        "BOOKS" : "📚",
        "TEMPEL" : "🏛️",
        "DOCTOR_HAT" : "🎓",
        "HOURGLASS" : "⏳",
        "HOME" : "🏠",
        "MAIN" : "📜",
        "GLASS": "🔍",
        "CLIP": "📎",
        "WRITING": "📝",
        "POINT_TRIANGLE" : "▸",
        "RIGHT_ARROW" : "→",
        "LEFT_ARROW" : "←",
        "POINT_DOT" : "•",
        "POINT_SQUARE" : "⋅",
        "LONG_RIGHT_ARROW" : "⟶",
        "LONG_LEFT_ARROW" : "⟵",
        "BACKSPACE" : "⌫"
        
    }

    @classmethod
    def init_colors(cls):
        curses.start_color()
        curses.use_default_colors()
        for i, (_, color) in enumerate(cls.COLORS.items(), start=1):
            curses.init_pair(i, color, -1)

    @classmethod
    def color(cls, name):
        index = list(cls.COLORS.keys()).index(name) + 1
        return curses.color_pair(index)


class DarkAcademiaConsole:
    """Dark-Academia-Style Console – kompatibel mit curses oder Standard-Terminal."""

    curses_mode = False
    stdscr = None

    def __init__(self, palette: Palette, width: int = 60):
        self.palette = palette
        self.width = width
        self.quotes = [
            "🕯️  „Nichts Großes ist je ohne Leidenschaft entstanden.“ – Hegel",
            "📖  „Das Denken ist das Selbstgespräch der Seele.“ – Platon",
            "🏛️  „In der Stille wächst das Wahre.“ – Dag Hammarskjöld",
            "✒️  „Nicht weil es schwer ist, wagen wir es nicht, sondern weil wir es nicht wagen, ist es schwer.“ – Seneca",
            "🕰️  „Ich habe keine Zeit, mich zu beeilen.“ – Igor Strawinsky",
            "⚙️  „Disziplin ist Freiheit.“ – Jocko Willink",
            "📚  „Wer das Warum seines Lebens kennt, erträgt fast jedes Wie.“ – Nietzschee",
            "🏛️  „Philosophie ist ein stilles Gespräch mit der Ewigkeit.“",
            "🕯️  „Der Tag gehört dem, der ihn bewusst beginnt.“",
            "📖  „Zwischen Ordnung und Chaos wohnt die Schöpfung.““",
            "🪶  „Ein Gedanke ist eine Aufgabe, die noch nicht geschrieben wurde.““",
            "⏳  „Die Zeit, die du dir nimmst, ist keine verlorene Zeit.“ – Saint-Exupéryy",
            "📚  „Wissenschaft ohne Philosophie ist blind, Philosophie ohne Wissenschaft ist leer.““",
            "🕯️  „Ruhe ist die höchste Form der Stärke.“ – Schiller",
            "🏛️  „Alles, was wir sehen, ist nur ein Schatten dessen, was wir nicht sehen.“ – Platon",
            "✒️  „Verstehen heißt, den Schatten in der Tiefe zu erkennen, nicht das Licht an der Oberfläche.“",
            "📖  „Der Mensch ist das Wesen, das Ordnung sucht – und Bedeutung darin findet.““",
            "⚙️  „Arbeit ist Gebet, wenn sie mit Hingabe geschieht.“",
            "🕯️  „Im Rhythmus der Arbeit liegt der Sinn des Lebens.“",
            "🏛️  „Wir leben in Fragmenten, aber denken im Ganzen.“ – Novalis",
            "📚  „Das Schönste, was wir erleben können, ist das Geheimnisvolle.“ – Einsteinn",
            "✒️  „Ordnung ist die Freude der Vernunft, aber Unordnung die Wonne der Fantasie.“ – Paul Claudel",
            "🕰️  „Die Zukunft gehört denen, die sich heute darauf vorbereiten.“ – Malcolm X",
            "📖  „Wer die Stille meistert, hat das Denken verstanden.““",
            "🕯️  „Zwischen Geist und Handlung liegt die Verantwortung.“",
            "🏛️  „Wissen verpflichtet – vor allem den, der versteht.“",
            "📚  „Du bist, was du ordnest.““",
            "✒️  „In der Konzentration liegt die Freiheit.“",
            "🕯️  „Ein strukturierter Tag ist kein Käfig, sondern eine Bühne.“",
            "⚙️  „Perfektion ist nicht das Ziel, sondern das Nebenprodukt der Hingabe.“",
        ]

    def _center_line(self, text: str = "", padding: int = 2) -> str:
        """Zentrierte Zeile mit Rändern, ohne Zeilenumbruch."""
        s = self.palette.SYMBOLS
        text_width = wcswidth(text)
        spaces = self.width - text_width + padding
        left = spaces // 2
        right = spaces - left
        return f"{s['EDGE_VERTICAL']}{' ' * left}{text}{' ' * right}{s['EDGE_VERTICAL']}"

    def header(self, title: str, compact: bool = False):
        """Gibt Header-Zeilen als segmentierte Struktur zurück (farbkompatibel für curses)."""
        s = self.palette.SYMBOLS
        lines = []
        horizontal = s["EDGE_HORIZONTAL"] * (self.width + 2)

        # Rahmen oben – komplett Ivory
        lines.append([(f"{s['CORNER_LEFT_TOP']}{horizontal}{s['CORNER_RIGHT_TOP']}", "IVORY", None)])

        if (self.width - len("📖 ToDo-App") + 2) % 2 == 0:
            padding_right = padding_left =  (self.width - len("📖 ToDo-App") + 2) // 2
        else:
            padding_right = ((self.width - len("📖 ToDo-App") + 2) // 2) + 1
            padding_left = (self.width - len("📖 ToDo-App") + 2) // 2
        
        if (self.width - len(title) + 2) % 2 == 0:
            padding_title_right = padding_title_left = (self.width - len(title) + 2) // 2
        else: 
            padding_title_right = ((self.width - len(title) + 2) // 2) + 1
            padding_title_left = (self.width - len(title) + 2) // 2
        # Zwischenzeilen
        if not compact:
            lines.append([(self._center_line(), "IVORY", None)])
            lines.append([
                ("║", "IVORY", None),
                (" " * 2, "IVORY", None),
                (str(Date.today()), "GOLD", "BOLD"),
                (" " * (padding_left - 2 - len(str(Date.today()))), "IVORY", None),
                ("📖 ", "GOLD", None),
                ("ToDo-App", "WHITE", "BOLD"),
                (" " * padding_right, "IVORY", None),
                ("║", "IVORY", None)
            ])
            lines.append([
                ("║", "IVORY", None),
                (" " * padding_title_left, "IVORY", None),
                (title, "WHITE", "BOLD"),
                (" " * padding_title_right, "IVORY", None),
                ("║", "IVORY", None)
            ])
            lines.append([(self._center_line(), "IVORY", None)])
        else:
            lines.append([
                ("║", "IVORY", None),
                (" " * padding_left, "IVORY", None),
                ("📖 ", "GOLD", None),
                ("ToDo-App", "WHITE", "BOLD"),
                (" " * padding_right, "IVORY", None),
                ("║", "IVORY", None)
            ])
            lines.append([
                ("║", "IVORY", None),
                (" " * padding_title_left, "IVORY", None),
                (title, "WHITE", "BOLD"),
                (" " * padding_title_right, "IVORY", None),
                ("║", "IVORY", None)
            ])

        return lines


    def footer(self, controls: list[str]) -> list[list[tuple[str, str, str]]]:
        """
        Gibt Footer-Zeilen segmentiert zurück:
        - Rahmen und Linien: Ivory
        - Steuerungstexte (controls): Weiß (BOLD)
        """
        s = self.palette.SYMBOLS
        lines = []
        horizontal = s["EDGE_HORIZONTAL"] * (self.width + 2)

        # Mittlere Steuerungszeile
        text = "  ".join(controls)
        padding = (self.width - len(text) + 2) // 2
        if (self.width - len(text) + 2) % 2 == 0:
            padding_right = padding_left = (self.width - len(text) + 2) // 2
        else:
            padding_right = (self.width - len(text) + 2) // 2
            padding_left = ((self.width - len(text) + 2) // 2) + 1
        lines.append([
            (s["EDGE_VERTICAL"], "IVORY", None),
            (" " * padding_right, "IVORY", None),
            (text, "WHITE", "BOLD"),
            (" " *(padding_left), "IVORY", None),
            (s["EDGE_VERTICAL"], "IVORY", None),
        ])

        # Unterer Abschlussrahmen
        lines.append([(f"{s['CORNER_LEFT_BOTTOM']}{horizontal}{s['CORNER_RIGHT_BOTTOM']}", "IVORY", None)])

        return lines
    
    # -------------------------------------------------------------------------
    # Misc
    # -------------------------------------------------------------------------
    @staticmethod
    def clear(stdscr):
        """Gesamten Bildschirm löschen (curses-kompatibel)."""
        stdscr.erase()
        stdscr.refresh()

    @staticmethod
    def clear_current_line(stdscr, y=None):
        """Aktuelle oder bestimmte Zeile löschen."""
        if y is None:
            y, _ = stdscr.getyx()
        stdscr.move(y, 0)
        stdscr.clrtoeol()
        stdscr.refresh()

    @staticmethod
    def erase_last_line(stdscr):
        """Vorherige Zeile löschen."""
        y, _ = stdscr.getyx()
        if y > 0:
            stdscr.move(y - 1, 0)
            stdscr.clrtoeol()
        stdscr.refresh()

    @staticmethod
    def pause(seconds: float = 1.0):
        sleep(seconds)

    @staticmethod
    def typewriter(text, delay=0.04):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            sleep(delay)
        print()

    def quote(self):
        return random.choice(self.quotes)