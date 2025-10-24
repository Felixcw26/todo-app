from gui.dark_academia_theme import DarkAcademiaConsole, Palette

DA = DarkAcademiaConsole(Palette(), 120)
# Beispiel
DA.clear()
DA.typewriter(f"🕯️  {Palette.IVORY}Willkommen zurück, Felix.{Palette.RESET}", 0.03)
DA.pause(0.8)
DA.typewriter(f"Ein weiterer {Palette.ITALIC}Abend zwischen Denken und Tun.{Palette.RESET}", 0.04)
DA.pause(1)
DA.erase_last_line()
DA.typewriter("📖  Die ToDo-Liste wartet auf ihre Fortsetzung...", 0.03)
footer = DA.footer(["Beenden", "Hinzufügen", "Löschen", "JKJJHFGJEDJFHEJHEJDHFJGHJ"])
header = DA.header("Menu")
print(header + footer[0])