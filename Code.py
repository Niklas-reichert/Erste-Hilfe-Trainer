import flet as ft
import sqlite3
import datetime

# --- Datenbank Setup ---
def init_db():
    conn = sqlite3.connect("rettungssimulator.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ergebnisse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            level TEXT,
            chance INTEGER,
            erfolg INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_result(level, chance, erfolg):
    conn = sqlite3.connect("rettungssimulator.db")
    cursor = conn.cursor()
    datum = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO ergebnisse (datum, level, chance, erfolg) VALUES (?, ?, ?, ?)", 
                   (datum, level, chance, 1 if erfolg else 0))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("rettungssimulator.db")
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(chance), COUNT(*), SUM(erfolg) FROM ergebnisse")
    row = cursor.fetchone()
    conn.close()
    avg_chance = row[0] if row and row[0] is not None else 0
    total_games = row[1] if row and row[1] is not None else 0
    total_wins = row[2] if row and row[2] is not None else 0
    return {"avg_chance": round(avg_chance, 1), "total_games": total_games, "total_wins": total_wins}

init_db()

# --- DATEN (VOLLSTÄNDIG) ---
uebung_daten = {
    1: {
        "story": "SZENARIO: Schwerer Verkehrsunfall auf der Landstraße. Rauch steigt auf, Trümmer liegen überall.\n\nFRAGE: Welche Notrufnummer wählen Sie jetzt sofort, um Hilfe zu holen?",
        "choices": [
            {"massnahme": "112 wählen (Feuerwehr/Rettungsdienst)", "rueckmeldung": "RICHTIG! Die 112 ist die europaweite Notrufnummer für medizinische Notfälle und Brände. Sie erreichen hier die Leitstelle, die sofort Rettungswagen und Feuerwehr entsendet.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
            {"massnahme": "110 wählen (Polizei)", "rueckmeldung": "FALSCH! Die 110 ist die Polizei. Diese würde Sie zwar weiterleiten, aber dabei gehen lebenswichtige Sekunden verloren.", "zeit": 1, "survival": -10, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
            {"massnahme": "116 117 wählen (Bereitschaftsdienst)", "rueckmeldung": "KRITISCH FALSCH! Dies ist der ärztliche Bereitschaftsdienst für nicht lebensbedrohliche Fälle. Bei einem Unfall ist dies völlig ungeeignet.", "zeit": 1, "survival": -20, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False}
        ]
    },
    2: {
        "story": "Die Leitstelle hebt ab: 'Notruf 112, wo ist der Notfallort und wer ist am Apparat?'\n\nFRAGE: Was ist Ihre erste und wichtigste Angabe in diesem Moment?",
        "choices": [
            {"massnahme": "Mein Name und meine Rückrufnummer", "rueckmeldung": "RICHTIG! Die Leitstelle muss wissen, wer anruft und wie sie Sie bei einem Verbindungsabbruch erreichen kann. Danach folgt sofort der Ort.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False},
            {"massnahme": "Den Ort des Notfalls laut schreien", "rueckmeldung": "NICHT OPTIMAL! Auch wenn der Ort wichtig ist, bewahren Sie Ruhe. Hektisches Schreien erschwert die Verständigung.", "zeit": 1, "survival": 0, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False},
            {"massnahme": "Direkt sagen, wie viele Verletzte es gibt", "rueckmeldung": "ZU FRÜH! Die Anzahl der Verletzten ist der dritte Schritt. Zuerst muss geklärt sein, WER anruft und WO es passiert ist.", "zeit": 1, "survival": -5, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False}
        ]
    },
    3: {
        "story": "Der Disponent hat den Ort notiert. Die Leitung bleibt offen.\n\nFRAGE: Was tun Sie jetzt bezüglich des Telefonats?",
        "choices": [
            {"massnahme": "Auf Rückfragen warten", "rueckmeldung": "PERFEKT! Beenden Sie das Gespräch niemals von sich aus. Die Leitstelle gibt Ihnen Anweisungen und beendet das Telefonat, wenn alle Infos da sind.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False},
            {"massnahme": "Sofort auflegen, um zu helfen", "rueckmeldung": "GEFÄHRLICH! Wenn Sie auflegen, kann die Leitstelle Ihnen keine lebenswichtigen Tipps zur Ersten Hilfe geben.", "zeit": 1, "survival": -15, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False},
            {"massnahme": "Die Angehörigen der Verletzten anrufen", "rueckmeldung": "FALSCHE PRIORITÄT! Ihre Leitung muss für die Rettungskräfte frei bleiben. Kümmern Sie sich erst um die Erstversorgung.", "zeit": 1, "survival": -10, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False}
        ]
    },
    4: {
        "story": "Während Sie am Telefon sind, verliert ein Verletzter plötzlich das Bewusstsein.\n\nFRAGE: Wie handeln Sie in dieser neuen Situation?",
        "choices": [
            {"massnahme": "Schnell die Leitstelle über die Änderung informieren", "rueckmeldung": "RICHTIG! Jede Verschlechterung des Zustands (wie Bewusstlosigkeit) muss sofort gemeldet werden, damit der Rettungsdienst die Dringlichkeit erhöhen kann.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True, "end_text": "Übung erfolgreich beendet!\n\nDu hast die Grundlagen für diesen Notfall gelernt."},
            {"massnahme": "Ich tue nichts, die Rettung kommt ja gleich", "rueckmeldung": "FATAL! Ein Bewusstloser benötigt sofortige Hilfe (stabile Seitenlage/Kontrolle), und die Leitstelle muss das wissen.", "zeit": 1, "survival": -30, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True},
            {"massnahme": "Mich um den Bewusstlosen kümmern, ohne das Telefon", "rueckmeldung": "TEILWEISE RICHTIG! Die Hilfe ist wichtig, aber Sie müssen der Leitstelle Bescheid sagen, während Sie helfen.", "zeit": 1, "survival": 10, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True}
        ]
    }
}

szenario_daten = {
    1: {
        "story": "Ein Jogger bricht im Park vor dir zusammen. Er reagiert nicht auf dein Rufen. Sein Puls am Hals fühlt sich erhöht an. Was tust du als Erstes? (Achtung: Jede Aktion kostet wertvolle Zeit!)",
        "choices": [
            {"massnahme": "Sofort eine Herzdruckmassage (REA) beginnen.", "rueckmeldung": "Falsch und lebensgefährlich! Da die Person noch selbstständig atmet, darfst du auf keinen Fall eine Herzdruckmassage durchführen. Das führt zum Herzstillstand.", "zeit": 1, "survival": -70, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True},
            {"massnahme": "Die Atmung genau überprüfen.", "rueckmeldung": "Sehr gut! Das Überprüfen der Atemwege dauert zwar einen Moment, gibt dir aber die nötige Sicherheit für die nächsten Schritte.", "zeit": 1, "survival": 10, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
            {"massnahme": "Den Patienten direkt in die stabile Seitenlage bringen.", "rueckmeldung": "Richtig gehandelt, aber hektisch! Die stabile Seitenlage sichert die Atemwege sofort, allerdings kostet das Bewegen des Patienten ohne Check etwas mehr Zeit.", "zeit": 3, "survival": 20, "tod_bonus": 5, "rtw": 0, "next": 3, "is_end": False}
        ]
    },
    2: {
        "story": "Du hast die Atmung gecheckt: Sie ist tief und regelmäßig. Der Patient liegt flach auf dem Rücken. Wie reagierst du jetzt?",
        "choices": [
            {"massnahme": "Den Jogger sofort in die stabile Seitenlage bringen.", "rueckmeldung": "Perfekt! Das Sichern der Atemwege schützt vor dem Ersticken und verschafft dem Patienten wertvolle Überlebenszeit.", "zeit": 2, "survival": 20, "tod_bonus": 5, "rtw": 0, "next": 4, "is_end": False},
            {"massnahme": "Direkt zum Handy greifen und den Notruf 112 wählen.", "rueckmeldung": "Guter Schritt, der Notruf startet den Rettungswagen! Aber Vorsicht: Solange das Telefonat läuft, liegt der Patient ungesichert flach.", "zeit": 2, "survival": 10, "tod_bonus": -2, "rtw": 12, "next": 5, "is_end": False},
            {"massnahme": "Dem Bewusstlosen vorsichtig etwas Wasser einflößen.", "rueckmeldung": "Kritischer Fehler! Das Wasser läuft direkt in die Lunge. Akute Erstickungsgefahr.", "zeit": 2, "survival": -50, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True}
        ]
    },
    3: {
        "story": "Der Patient liegt nun sicher in der stabilen Seitenlage. Seine Atemwege sind geschützt, er atmet weiterhin regelmäßig. Welchen Schritt unternimmst du als nächstes?",
        "choices": [
            {"massnahme": "Jetzt den Rettungsdienst über die 112 alarmieren.", "rueckmeldung": "Genau richtig! Da der Patient stabil liegt, kannst du in Ruhe den Notruf absetzen.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 10, "next": 6, "is_end": False},
            {"massnahme": "Die Beine des Joggers hochlagern (Schocklage).", "rueckmeldung": "Grober Fehler! Das Herumdrehen kostet Zeit und bringt den Patienten in Lebensgefahr, da du die Seitenlage auflöst.", "zeit": 3, "survival": -40, "tod_bonus": -10, "rtw": 0, "next": None, "is_end": True},
            {"massnahme": "Den Rucksack des Joggers nach Hinweisen durchsuchen.", "rueckmeldung": "Du suchst im Rucksack. Das kostet extrem viel wertvolle Zeit, in der noch kein Rettungswagen unterwegs ist!", "zeit": 4, "survival": 0, "tod_bonus": -2, "rtw": 0, "next": 7, "is_end": False}
        ]
    },
    4: {
        "story": "Der Patient liegt sicher in der Seitenlage, aber es ist noch kein Rettungsdienst alarmiert worden. Die Zeit drängt. Was tust du?",
        "choices": [
            {"massnahme": "Jetzt sofort den Notruf 112 wählen.", "rueckmeldung": "Sehr gut! Der Notruf läuft. Der RTW fährt sofort los und braucht 8 Minuten.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 8, "next": None, "is_end": True, "end_text": "Der Notruf ist durch. Das System prüft nun das Eintreffen des RTW..."},
            {"massnahme": "Den Patienten kurz alleine lassen und zum Parkeingang laufen.", "rueckmeldung": "Katastrophaler Zeitverlust! Du rennst weg, ohne dass überhaupt ein Notruf abgesetzt wurde.", "zeit": 5, "survival": -30, "tod_bonus": -8, "rtw": 0, "next": None, "is_end": True}
        ]
    },
    5: {
        "story": "Die Leitstelle hebt ab: 'Notruf 112, wo genau ist der Notfall?'. Während du telefonierst, liegt der Jogger weiterhin ungesichert flach.",
        "choices": [
            {"massnahme": "Den Patienten jetzt gemeinsam in die stabile Seitenlage drehen.", "rueckmeldung": "Sehr gut! Der Disponent leitet dich professionell an. Die Atemwege sind ab jetzt sicher.", "zeit": 3, "survival": 20, "tod_bonus": 6, "rtw": 0, "next": None, "is_end": True},
            {"massnahme": "Lautstark nach Passanten rufen, damit sie den Patienten auf die Seite drehen.", "rueckmeldung": "Hervorragende Teamarbeit! Ein Passant sichert den Patienten sofort.", "zeit": 2, "survival": 30, "tod_bonus": 8, "rtw": -2, "next": None, "is_end": True}
        ]
    },
    6: {
        "story": "Der Notruf ist erfolgreich beendet und der Rettungswagen ist unterwegs. Der Jogger befindet sich in der stabilen Seitenlage. Was unternimmst du jetzt?",
        "choices": [
            {"massnahme": "Alle 2 Minuten die Atmung überprüfen und auf ihn einreden.", "rueckmeldung": "Absolut perfekt! Das kontinuierliche Überprüfen hält den Zustand stabil.", "zeit": 2, "survival": 30, "tod_bonus": 2, "rtw": 0, "next": None, "is_end": True},
            {"massnahme": "Den Jogger mit deiner Jacke zudecken.", "rueckmeldung": "Sehr gut mitgedacht! Der Wärmeerhalt ist wichtig.", "zeit": 1, "survival": 20, "tod_bonus": 3, "rtw": 0, "next": None, "is_end": True}
        ]
    },
    7: {
        "story": "Beim Durchsuchen des Rucksacks stößt du auf eine leere Trinkflasche. Der Jogger liegt in Seitenlage, aber kein Notruf abgesetzt!",
        "choices": [
            {"massnahme": "Dehydration erkennen und sofort den Notruf 112 anrufen.", "rueckmeldung": "Sehr stark! Du wählst endlich den Notruf. Der Rettungswagen fährt sofort los.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 9, "next": None, "is_end": True}
        ]
    }
}

# --- UI IMPLEMENTIERUNG ---
RED_PRIMARY = "#b30000"

def main(page: ft.Page):
    page.title = "Erste Hilfe Trainer"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f5f5f5"
    page.padding = 0
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    
    settings = {
        "dark_mode": False, 
        "font_size": 16, 
        "show_images": True
    }
    
    game_state = {
        "is_scenario": False, 
        "node": 1, 
        "survival": 30, 
        "time_passed": 0, 
        "time_to_death": 15, 
        "rtw_arrival_time": 999, 
        "rtw_active": False, 
        "current_level_name": ""
    }

    # --- UI Komponenten ---
    header = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("ERSTE HILFE", size=22, weight="bold", color="white"), 
                ft.Text("TRAINER", size=22, weight="bold", color="white")
            ], spacing=0, alignment="center"),
            ft.Icon(ft.Icons.MONITOR_HEART, color="white", size=50)
        ], alignment="spaceBetween"),
        bgcolor=RED_PRIMARY, 
        padding=ft.Padding(25, 40, 25, 20), 
        border_radius=ft.BorderRadius(0, 0, 30, 30), 
        shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
    )

    scenarios_view = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    level_view = ft.Column(visible=False, expand=True, horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
    stats_view = ft.Column(visible=False, expand=True, horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
    settings_view = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.AUTO)

    def refresh_ui():
        bg_color = "#1a1a1a" if settings["dark_mode"] else "#f5f5f5"
        card_color = "#2d2d2d" if settings["dark_mode"] else "#ffffff"
        text_color = "#ffffff" if settings["dark_mode"] else "#000000"
        page.bgcolor = bg_color
        page.theme_mode = ft.ThemeMode.DARK if settings["dark_mode"] else ft.ThemeMode.LIGHT
        render_scenarios(card_color, text_color)
        if level_view.visible:
            render_node()
        page.update()

    def render_scenarios(card_bg, text_c):
        scenarios_view.controls.clear()
        scenarios_view.controls.append(ft.Container(ft.Text("Willkommen!", size=20, weight="bold", color=text_c), padding=20))
        
        def create_card(title, desc, action, is_scenario=False):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=70, height=70, 
                        bgcolor=RED_PRIMARY if is_scenario else "#e0e0e0", 
                        border_radius=10, 
                        content=ft.Icon(ft.Icons.PLAY_ARROW, color="white") if is_scenario else None, 
                        visible=settings["show_images"]
                    ),
                    ft.VerticalDivider(width=10, color="transparent"),
                    ft.Column([
                        ft.Text(title, size=settings["font_size"], weight="bold", color=text_c, width=200),
                        ft.Text(desc, size=settings["font_size"]-4, color="#888888", width=200, max_lines=2),
                        ft.Container(
                            content=ft.Text("Modus wählen", size=10, color="white", weight="bold"), 
                            bgcolor=RED_PRIMARY, 
                            padding=ft.Padding(10, 5, 10, 5), 
                            border_radius=15, 
                            on_click=action
                        )
                    ], spacing=5, expand=True)
                ]),
                padding=15, bgcolor=card_bg, border_radius=20, margin=ft.Margin(20, 8, 20, 8), 
                shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color="#11000000"), 
                on_click=action
            )
        scenarios_view.controls.append(create_card("#Verkehrsunfall#", "Übung: Grundlagen des Notrufs.", lambda _: start_game(False, "Übung 1")))
        scenarios_view.controls.append(create_card("Szenario: Jogger im Park", "KOMPLEX: Zeit & Überleben!", lambda _: start_game(True, "Jogger im Park"), is_scenario=True))

    story_text = ft.Text(size=18, weight="bold", text_align="center")
    feedback_text = ft.Text(size=14, color="white")
    feedback_container = ft.Container(content=feedback_text, padding=15, border_radius=15, bgcolor=ft.Colors.BLUE_GREY_700, visible=False)
    choices_col = ft.Column(spacing=10, horizontal_alignment="center")
    stats_bar_col = ft.Column([
        ft.Row([ft.Text("Überlebenschance:"), ft.Text(weight="bold")], alignment="spaceBetween"),
        ft.ProgressBar(value=0.3, color="green"),
        ft.Row([ft.Text("Zeit bis Tod:"), ft.Text(weight="bold")], alignment="spaceBetween"),
        ft.ProgressBar(value=0.5, color="red"),
    ], visible=False, width=320)

    def start_game(is_scenario, name):
        game_state["is_scenario"] = is_scenario
        game_state["node"] = 1
        game_state["survival"] = 30 if is_scenario else 100
        game_state["time_passed"] = 0
        game_state["time_to_death"] = 15
        game_state["rtw_arrival_time"] = 999
        game_state["rtw_active"] = False
        game_state["current_level_name"] = name
        
        scenarios_view.visible = False
        level_view.visible = True
        stats_bar_col.visible = is_scenario
        render_node()

    def render_node():
        data = (szenario_daten if game_state["is_scenario"] else uebung_daten)[game_state["node"]]
        story_text.value = data["story"]
        story_text.size = settings["font_size"] + 2
        story_text.color = "#ffffff" if settings["dark_mode"] else "#000000"
        feedback_container.visible = False
        choices_col.controls.clear()
        
        for choice in data["choices"]:
            choices_col.controls.append(
                ft.Container(
                    content=ft.Text(choice["massnahme"], size=settings["font_size"], weight="bold", text_align="center", color="#000000"), 
                    bgcolor="white", padding=15, border_radius=15, width=320, 
                    border=ft.Border(ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd")), 
                    on_click=lambda e, c=choice: handle_choice(c), 
                    alignment=ft.Alignment(0, 0)
                )
            )
            
        s_val = max(0, min(100, game_state["survival"]))
        d_val = max(0, game_state["time_to_death"])
        stats_bar_col.controls[1].value = s_val / 100
        stats_bar_col.controls[0].controls[1].value = f"{s_val}%"
        stats_bar_col.controls[3].value = min(1.0, d_val / 30)
        stats_bar_col.controls[2].controls[1].value = f"{d_val} Min"
        page.update()

    def handle_choice(choice):
        game_state["survival"] += choice["survival"]
        game_state["time_passed"] += choice["zeit"]
        game_state["time_to_death"] += choice["tod_bonus"] - choice["zeit"]
        
        if choice["rtw"] > 0 and not game_state["rtw_active"]:
            game_state["rtw_active"] = True
            game_state["rtw_arrival_time"] = game_state["time_passed"] + choice["rtw"]
        elif choice["rtw"] != 0:
            game_state["rtw_arrival_time"] += choice["rtw"]
            
        feedback_text.value = choice["rueckmeldung"]
        feedback_container.visible = True
        for c in choices_col.controls:
            c.disabled = True
            
        if choice["is_end"] or game_state["time_to_death"] <= 0:
            show_final_result(choice)
        else:
            choices_col.controls.append(
                ft.ElevatedButton(
                    "WEITER", 
                    on_click=lambda _: move_to_node(choice["next"]), 
                    bgcolor=RED_PRIMARY, 
                    color="white"
                )
            )
        page.update()

    def move_to_node(n):
        game_state["node"] = n
        render_node()

    def show_final_result(choice):
        success = False
        end_msg = ""
        if game_state["time_to_death"] <= 0:
            success = False
            end_msg = "LEIDER VERSTORBEN."
            game_state["survival"] = 0
        elif choice.get("is_end") and game_state["rtw_active"]:
            wait_time = game_state["rtw_arrival_time"] - game_state["time_passed"]
            if wait_time <= game_state["time_to_death"] and game_state["survival"] > 20:
                success = True
                end_msg = f"ERFOLG! Überlebenschance: {game_state['survival']}%"
            else:
                success = False
                end_msg = "KNAPP GESCHEITERT."
        else:
            end_msg = choice.get("end_text", "Einsatz beendet.")
            success = game_state["survival"] >= 50
            
        story_text.value = "ABSCHLUSS"
        choices_col.controls.clear()
        choices_col.controls.append(ft.Text(end_msg, size=16, text_align="center", weight="bold", color="green" if success else "red"))
        choices_col.controls.append(ft.ElevatedButton("MENÜ", on_click=lambda _: show_menu(), bgcolor="black", color="white"))
        save_result(game_state["current_level_name"], game_state["survival"], success)

    def show_menu():
        scenarios_view.visible = True
        level_view.visible = False
        refresh_ui()

    def build_settings():
        settings_view.controls.clear()
        text_color = "#ffffff" if settings["dark_mode"] else "#000000"
        settings_view.controls.append(ft.Container(ft.Text("Einstellungen", size=22, weight="bold", color=text_color), padding=20))
        
        def on_font_change(e):
            settings["font_size"] = 14 if "12" in e.control.value else 18
            refresh_ui()
        font_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Größe 12 (Klein)"), ft.dropdown.Option("Größe 18 (Groß)")], 
            value="Größe 12 (Klein)" if settings["font_size"] == 14 else "Größe 18 (Groß)", 
            width=150
        )
        font_dropdown.on_change = on_font_change
        
        def on_dark_change(e):
            settings["dark_mode"] = e.control.value
            refresh_ui()
        dark_switch = ft.Switch(value=settings["dark_mode"], on_change=on_dark_change)
        
        def on_img_change(e):
            settings["show_images"] = e.control.value
            refresh_ui()
        img_switch = ft.Switch(value=settings["show_images"], on_change=on_img_change)

        settings_view.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Visuell", weight="bold", color="#000000"), 
                    ft.ListTile(title=ft.Text("Dark Mode", color="#000000"), trailing=dark_switch), 
                    ft.ListTile(title=ft.Text("Schriftgröße", color="#000000"), trailing=font_dropdown), 
                    ft.ListTile(title=ft.Text("Bilder anzeigen", color="#000000"), trailing=img_switch)
                ]), 
                bgcolor="#f0f0f0", 
                border_radius=15, 
                padding=10, 
                margin=ft.Margin(20, 0, 20, 0)
            )
        )

    level_view.controls = [
        ft.Container(story_text, padding=25, bgcolor="#ffffff", border_radius=20, shadow=ft.BoxShadow(blur_radius=5, color="#dddddd"), width=350), 
        ft.Divider(height=20, color="transparent"), 
        stats_bar_col, 
        feedback_container, 
        choices_col
    ]

    def on_nav(e):
        idx = int(e.data)
        scenarios_view.visible = (idx == 1)
        stats_view.visible = (idx == 0)
        settings_view.visible = (idx == 2)
        level_view.visible = False
        
        if idx == 2:
            build_settings()
        elif idx == 0:
            s = get_stats()
            text_color = "#ffffff" if settings["dark_mode"] else "#000000"
            stats_view.controls = [
                ft.Container(ft.Text("STATISTIK", size=24, weight="bold", color=text_color), padding=20), 
                ft.Text(f"Einsätze: {s['total_games']}", size=18, color=text_color), 
                ft.Text(f"Erfolge: {s['total_wins']}", size=18, color="green"), 
                ft.Text(f"Ø Chance: {s['avg_chance']}%", size=18, color="blue"), 
                ft.ProgressBar(value=s['avg_chance']/100, width=250, color=RED_PRIMARY, height=10)
            ]
        refresh_ui()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Statistik"), 
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"), 
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings")
        ], 
        selected_index=1, 
        on_change=on_nav, 
        bgcolor="white", 
        height=70
    )
    
    page.add(
        ft.Column([
            header, 
            ft.Container(content=ft.Stack([scenarios_view, level_view, stats_view, settings_view]), expand=True)
        ], expand=True, spacing=0)
    )
    refresh_ui()

ft.app(target=main)
