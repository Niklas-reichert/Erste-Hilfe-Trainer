import flet as ft
import sqlite3
import datetime
import os
import threading
import time

# datenbank setup
DB_PATH = os.path.join(os.path.dirname(__file__), "rettungssimulator.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ergebnisse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            datum TEXT,
            level TEXT,
            chance INTEGER,
            erfolg INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_result(username, level, chance, erfolg):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    datum = datetime.datetime.now().strftime("%d.%m.")
    cursor.execute("INSERT INTO ergebnisse (username, datum, level, chance, erfolg) VALUES (?, ?, ?, ?, ?)", 
                   (username, datum, level, chance, 1 if erfolg else 0))
    conn.commit()
    conn.close()

def get_general_stats(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(chance), COUNT(*), SUM(erfolg) FROM ergebnisse WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    avg_chance = row[0] if row and row[0] is not None else 0
    total_games = row[1] if row and row[1] is not None else 0
    total_wins = row[2] if row and row[2] is not None else 0
    return {"avg_chance": round(avg_chance, 1), "total_games": total_games, "total_wins": total_wins}

def get_last_games(username, limit):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT level, chance, datum FROM ergebnisse WHERE username = ? ORDER BY id DESC LIMIT ?", (username, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows[::-1]

def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, MAX(chance) as max_chance FROM ergebnisse GROUP BY username ORDER BY max_chance DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()

# Szenarien und Übungen
uebung_daten = {
    1: {
        "story": "Du stößt auf einen schweren Verkehrsunfall auf der Landstraße. Rauch steigt auf, Trümmer liegen überall.\n\nWelche Notrufnummer wählst du jetzt sofort, um Hilfe zu holen?",
        "choices": [
            {"massnahme": "112", "rueckmeldung": "RICHTIG! Die 112 ist die europaweite Notrufnummer für medizinische Notfälle und Brände. Du erreichst hier die Leitstelle, die sofort Rettungswagen und Feuerwehr entsendet.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
            {"massnahme": "110", "rueckmeldung": "FALSCH! Die 110 ist die Polizei. Diese leitet dich zwar an die 112 weiter, aber dabei gehen lebenswichtige Sekunden verloren.", "zeit": 1, "survival": -10, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
            {"massnahme": "116 117", "rueckmeldung": "KRITISCH FALSCH! Dies ist der ärztliche Bereitschaftsdienst für nicht lebensbedrohliche Fälle. Bei einem Unfall ist dies völlig ungeeignet. Der Bereitschaftsdienst leitet dich verzögert weiter.", "zeit": 1, "survival": -20, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False}
        ]
    },
    2: {
        "story": "Die Leitstelle hebt ab: 'Notruf 112, wo ist der Notfallort und wer ist am Apparat?'\n\nWas ist deine erste und wichtigste Angabe in diesem Moment?",
        "choices": [
            {"massnahme": "Mein Name und meine Rückrufnummer", "rueckmeldung": "NICHT OPTIMAL! Obwohl diese Information für eventuelle Rückfragen wichtig ist, solltest du für eine schnelle Rettung zuerst den Ort des Notfalls angeben.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False},
            {"massnahme": "Den Ort des Notfalls", "rueckmeldung": "RICHTIG! Für die Verletzten ist schnelle Hilfe lebensrettend. Durch den Ort des Notfalls weiß die Rettung sofort, wo sie hin muss.", "zeit": 1, "survival": 0, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False},
            {"massnahme": "Direkt sagen, wie viele Verletzte es gibt", "rueckmeldung": "ZU FRÜH! Diese Information ist zwar entscheidend für die Anzahl der benötigten Fahrzeuge, jedoch ist der Ort des Notfalls wichtiger, damit überhaupt jemand losfahren kann.", "zeit": 1, "survival": -5, "tod_bonus": 0, "rtw": 0, "next": 3, "is_end": False}
        ]
    },
    3: {
        "story": "Der Disponent hat den Ort notiert. Die Leitung bleibt offen.\n\nWas tust du jetzt bezüglich des Telefonats?",
        "choices": [
            {"massnahme": "Auf Rückfragen warten", "rueckmeldung": "PERFEKT! Beende das Gespräch niemals von dir aus. Die Leitstelle gibt dir präzise Anweisungen und beendet das Telefonat, wenn alle Infos da sind.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False},
            {"massnahme": "Sofort auflegen, um zu helfen", "rueckmeldung": "GEFÄHRLICH! Wenn du auflegst, kann die Leitstelle dir keine lebenswichtigen Tipps zur Ersten Hilfe geben. Bleib lieber dran und warte auf Rückfragen.", "zeit": 1, "survival": -15, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False},
            {"massnahme": "Die Angehörigen der Verletzten anrufen", "rueckmeldung": "FALSCHE PRIORITÄT! Deine Leitung muss für die Rettungskräfte frei bleiben. Kümmer dich erst um die Erstversorgung und warte auf Rückfragen der Leitstelle.", "zeit": 1, "survival": -10, "tod_bonus": 0, "rtw": 0, "next": 4, "is_end": False}
        ]
    },
    4: {
        "story": "Während du am Telefon bist, verliert ein Verletzter plötzlich das Bewusstsein.\n\nWie handelst du in dieser neuen Situation?",
        "choices": [
            {"massnahme": "Schnell die Leitstelle über die Änderung informieren", "rueckmeldung": "RICHTIG! Jede Verschlechterung des Zustands (wie Bewusstlosigkeit) musst du sofort melden, damit der Rettungsdienst die Dringlichkeit erhöhen kann.", "zeit": 1, "survival": 25, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True, "end_text": "Übung beendet!\n\nDu hast die Grundlagen für das Absetzen eines Notrufs erfolgreich trainiert."},
            {"massnahme": "Ich tue nichts, die Rettung kommt ja gleich", "rueckmeldung": "FATAL! Ein Bewusstloser benötigt sofortige Hilfe (stabile Seitenlage/Atemkontrolle), und die Leitstelle muss das zwingend wissen.", "zeit": 1, "survival": -30, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True, "end_text": "Übung beendet!\n\nDu hast die Grundlagen zwar gesehen, solltest den Notruf aber ruhig noch einmal üben."},
            {"massnahme": "Mich um den Bewusstlosen kümmern, ohne das Telefon", "rueckmeldung": "TEILWEISE RICHTIG! Die direkte Hilfe vor Ort ist wichtig, aber du musst der Leitstelle parallel Bescheid sagen, während du hilfst (z. B. über Lautsprecher).", "zeit": 1, "survival": 10, "tod_bonus": 0, "rtw": 0, "next": None, "is_end": True, "end_text": "Übung beendet!\n\nDas war okay, aber denke nächstes Mal daran, die Verbindung zur Leitstelle zu halten."}
        ]
    }
}

szenarien_sammlung = {
    "jogger": {
        1: {
            "story": "Ein Jogger bricht im Park vor dir zusammen. Er reagiert nicht auf dein Rufen. Sein Puls am Hals fühlt sich erhöht an. Was tust du als Erstes? (Achtung: Jede Aktion kostet wertvolle Zeit!)",
            "choices": [
                {"massnahme": "Sofort eine Herzdruckmassage (REA) beginnen.", "rueckmeldung": "Falsch und lebensgefährlich! Da die Person noch selbstständig atmet, darfst du auf keinen Fall eine Herzdruckmassage durchführen. Das kann zu einem echten Herzstillstand führen.", "zeit": 1, "survival": -70, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Die Atmung genau überprüfen.", "rueckmeldung": "Sehr gut! Das Überprüfen der Atemwege dauert zwar einen Moment, gibt dir aber die nötige Sicherheit für die nächsten Schritte.", "zeit": 1, "survival": 10, "tod_bonus": 0, "rtw": 0, "next": 2, "is_end": False},
                {"massnahme": "Den Patienten direkt in die stabile Seitenlage bringen.", "rueckmeldung": "Richtig gehandelt, aber etwas hektisch! Die stabile Seitenlage sichert die Atemwege sofort, allerdings kostet das Bewegen des Patienten ohne vorherigen Check wertvolle Zeit.", "zeit": 3, "survival": 20, "tod_bonus": 5, "rtw": 0, "next": 3, "is_end": False}
            ]
        },
        2: {
            "story": "Du hast die Atmung gecheckt: Sie ist tief und regelmäßig. Der Patient liegt flach auf dem Rücken. Wie reagierst du jetzt?",
            "choices": [
                {"massnahme": "Den Jogger sofort in die stabile Seitenlage bringen.", "rueckmeldung": "Perfekt! Das Sichern der Atemwege schützt vor dem Ersticken an der eigenen Zunge oder Erbrochenem und verschafft dem Patienten wertvolle Überlebenszeit.", "zeit": 2, "survival": 20, "tod_bonus": 5, "rtw": 0, "next": 4, "is_end": False},
                {"massnahme": "Direkt zum Handy greifen und den Notruf 112 wählen.", "rueckmeldung": "Guter Schritt, der Notruf startet den Rettungswagen! Aber Vorsicht: Solange das Telefonat läuft, liegt der Patient ungesichert flach auf dem Rücken und droht zu ersticken.", "zeit": 2, "survival": 10, "tod_bonus": -2, "rtw": 12, "next": 5, "is_end": False},
                {"massnahme": "Dem Bewusstlosen vorsichtig etwas Wasser einflößen.", "rueckmeldung": "Kritischer Fehler! Da er bewusstlos ist, fehlen alle Schutzreflexe. Das Wasser läuft direkt in die Lunge. Es besteht akute Erstickungsgefahr.", "zeit": 2, "survival": -50, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        3: {
            "story": "Der Patient liegt nun sicher in der stabilen Seitenlage. Seine Atemwege sind geschützt, er atmet weiterhin regelmäßig. Welchen Schritt unternimmst du als nächstes?",
            "choices": [
                {"massnahme": "Jetzt den Rettungsdienst über die 112 alarmieren.", "rueckmeldung": "Genau richtig! Da der Patient stabil und sicher liegt, kannst du nun in Ruhe den Notruf absetzen.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 10, "next": 6, "is_end": False},
                {"massnahme": "Die Beine des Joggers hochlagern (Schocklage).", "rueckmeldung": "Grober Fehler! Das Herumdrehen kostet Zeit und bringt den Patienten in Lebensgefahr, da du dafür die schützende Seitenlage wieder auflösen musst.", "zeit": 3, "survival": -40, "tod_bonus": -10, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Den Rucksack des Joggers nach Hinweisen durchsuchen.", "rueckmeldung": "Du suchst im Rucksack. Das kostet extrem viel wertvolle Zeit, in der noch überhaupt kein Rettungswagen alarmiert wurde!", "zeit": 4, "survival": 0, "tod_bonus": -2, "rtw": 0, "next": 7, "is_end": False}
            ]
        },
        4: {
            "story": "Der Patient liegt sicher in der Seitenlage, aber es ist noch kein Rettungsdienst alarmiert worden. Die Zeit drängt. Was tust du?",
            "choices": [
                {"massnahme": "Jetzt sofort den Notruf 112 wählen.", "rueckmeldung": "Sehr gut! Der Notruf läuft. Der RTW fährt sofort los und braucht 8 Minuten.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 8, "next": None, "is_end": True, "end_text": "Der Notruf ist durch. Das System prüft nun das Eintreffen des RTW..."},
                {"massnahme": "Den Patienten kurz alleine lassen und zum Parkeingang laufen.", "rueckmeldung": "Katastrophaler Zeitverlust! Du rennst weg, ohne dass überhaupt ein Notruf abgesetzt wurde. Niemand weiß, dass hier Hilfe gebraucht wird.", "zeit": 5, "survival": -30, "tod_bonus": -8, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        5: {
            "story": "Die Leitstelle hebt ab: 'Notruf 112, wo genau ist der Notfall?'. Während du telefonierst, liegt der Jogger weiterhin ungesichert flach.",
            "choices": [
                {"massnahme": "Den Patienten jetzt parallel in die stabile Seitenlage drehen.", "rueckmeldung": "Sehr gut! Der Disponent leitet dich professionell per Telefon an. Die Atemwege sind ab jetzt gesichert.", "zeit": 3, "survival": 20, "tod_bonus": 6, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Lautstark nach Passanten rufen, damit sie den Patienten auf die Seite drehen.", "rueckmeldung": "Hervorragende Teamarbeit! Ein Passant eilt herbei und sichert den Patienten sofort in der Seitenlage, während du weitertelefonierst.", "zeit": 2, "survival": 30, "tod_bonus": 8, "rtw": -2, "next": None, "is_end": True}
            ]
        },
        6: {
            "story": "Der Notruf ist erfolgreich beendet und der Rettungswagen ist unterwegs. Der Jogger befindet sich in der stabilen Seitenlage. Was unternimmst du jetzt?",
            "choices": [
                {"massnahme": "Alle 2 Minuten die Atmung überprüfen und auf ihn einreden.", "rueckmeldung": "Absolut perfekt! Das kontinuierliche Überprüfen stellt sicher, dass du ein Aussetzen der Atmung sofort bemerkst.", "zeit": 2, "survival": 30, "tod_bonus": 2, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Den Jogger mit deiner Jacke zudecken.", "rueckmeldung": "Sehr gut mitgedacht! Der Wärmeerhalt schützt den Körper vor dem Auskühlen und stabilisiert den Kreislauf.", "zeit": 1, "survival": 20, "tod_bonus": 3, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        7: {
            "story": "Beim Durchsuchen des Rucksacks stößt du nur auf eine leere Trinkflasche. Der Jogger liegt in Seitenlage, aber es ist immer noch kein Notruf abgesetzt!",
            "choices": [
                {"massnahme": "Mögliche Dehydration erkennen und sofort den Notruf 112 anrufen.", "rueckmeldung": "Endlich! Du wählst den Notruf. Der Rettungswagen fährt sofort los und braucht 9 Minuten.", "zeit": 2, "survival": 20, "tod_bonus": 0, "rtw": 9, "next": None, "is_end": True}
            ]
        }
    },
    "sturz": {
        1: {
            "story": "Du befindest dich auf einer Baustelle, als ein ohrenbetäubender Knall die Stille bricht. Ein Heimwerker ist aus circa zwei Metern Höhe von einer Aluminiumleiter gestürzt. Als du herbeieilst, sitzt er zusammengesackt da. Er hält sich krampfhaft die rechte Brusthälfte und ringt sichtlich nach Luft. Wie reagierst du?",
            "choices": [
                {"massnahme": "Den Betroffenen vorsichtig flach auf den Rücken betten und die Beine etwa 30 Zentimeter hochlagern.", "rueckmeldung": "Kritischer Fehler! Bei dieser schweren Atemnot drückt die Flachlage die Bauchorgane gegen das Zwerchfell. Die kollabierte Lunge wird komplett komprimiert – der Mann gerät in akute Todesangst und droht zu ersticken.", "zeit": 2, "survival": -60, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Dein Smartphone zücken und die europäische Notrufnummer 112 wählen.", "rueckmeldung": "Sehr gut! Ein Sturz aus dieser Höhe gekoppelt mit massiver Atemnot ist ein kritischer Notfall. Du leitest die professionelle Rettungskette sofort ein.", "zeit": 2, "survival": +20, "tod_bonus": -2, "rtw": 12, "next": 2, "is_end": False},
                {"massnahme": "Den Oberkörper des Mannes vorsichtig anheben und ihn in einer sitzenden Position an der Wand anlehnen.", "rueckmeldung": "Fachlich absolut perfekt! Das entlastet die Lungen und der Patient kann seine Atemhilfsmuskulatur besser einsetzen. Du hast wegen einer möglichen Wirbelsäulenverletzung maximal vorsichtig agiert.", "zeit": 2, "survival": +30, "tod_bonus": +5, "rtw": 0, "next": 3, "is_end": False}
            ]
        },
        2: {
            "story": "Das Gespräch mit der Leitstelle läuft. Seine Atmung wird trotz aller Bemühungen immer flacher. Du bemerkst entsetzt, dass sich seine Lippen blau verfärben. Zudem treten die großen Halsvenen prall hervor (Spannungspneumothorax!). Was unternimmst du parallel?",
            "choices": [
                {"massnahme": "Die enge Arbeitskleidung und den Kragen am Hals öffnen, den Oberkörper aufrecht halten.", "rueckmeldung": "Großartig! Das Öffnen der engen Kleidung nimmt den mechanischen Druck. Durch deine ruhige Stimme senkst du seine Panik und damit den akuten Sauerstoffverbrauch.", "zeit": 2, "survival": +25, "tod_bonus": +3, "rtw": 0, "next": 4, "is_end": False},
                {"massnahme": "Ihm dabei helfen, sich auf die linke, völlig schmerzfreie Körperseite zu legen.", "rueckmeldung": "Kritischer Fehler! Indem du ihn auf die gesunde (linke) Seite legst, drückt sein gesamtes Körpergewicht diese intakte Lunge ab. Da die rechte Lunge ohnehin versagt, bekommt er gar keinen Sauerstoff mehr.", "zeit": 2, "survival": -50, "tod_bonus": -12, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Ihn flach hinlegen und sofort mit einer kräftigen Mund-zu-Mund-Beatmung beginnen.", "rueckmeldung": "Ein fataler Fehler! Durch den Beatmungs-Überdruck presst du noch mehr Luft durch den Riss in der Lunge in den Brustkorb. Der Druck auf das Herz wird so groß, dass es sofort aufhört zu schlagen.", "zeit": 1, "survival": -70, "tod_bonus": -20, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        3: {
            "story": "Der Mann lehnt aufrecht an der Wand. Doch plötzlich verdreht er die Augen und sackt kraftlos zur Seite weg. Er reagiert nicht mehr. Bei der Atemkontrolle spürst du einen minimalen, extrem flachen Luftstrom. Er ist tief bewusstlos. Wie reagierst du?",
            "choices": [
                {"massnahme": "Das Smartphone herausnehmen, die 112 wählen und der Leitstelle die Bewusstlosigkeit melden.", "rueckmeldung": "Falsche Priorität! Während du wählst, liegt der Bewusstlose ungesichert am Boden. Seine Zunge erschlafft, fällt nach hinten und verschließt die Atemwege komplett. Er erstickt, bevor du fertig telefoniert hast.", "zeit": 2, "survival": +10, "tod_bonus": -5, "rtw": 10, "next": 5, "is_end": False},
                {"massnahme": "Den leblosen Körper sofort in die stabile Seitenlage bringen, gedreht auf seine rechte, verletzte Seite.", "rueckmeldung": "Medizinisches Meisterstück! Da du ihn auf die verletzte (rechte) Seite legst, bleibt die linke, gesunde Lungenhälfte oben frei von Druck und kann maximal belüftet werden. Das sichert sein Überleben.", "zeit": 2, "survival": +40, "tod_bonus": +6, "rtw": 0, "next": 6, "is_end": False},
                {"massnahme": "Hinter den Patienten setzen, seinen Kopf sanft nach hinten überstrecken und versuchen, ihn im Sitzen zu halten.", "rueckmeldung": "Das ist extrem gefährlich. Ein tief Bewusstloser hat keinerlei Muskeltonus mehr. Es ist unmöglich, eine völlig schlaffe Person sicher im Sitzen zu halten – die Atemwege kollabieren.", "zeit": 1, "survival": -40, "tod_bonus": -8, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        4: {
            "story": "Du kniest neben dem sitzenden Mann. Seine Halsvenen sind dick wie Strohhalme, aber er bleibt dank deiner Hilfe bei Bewusstsein. Plötzlich hörst du in der Ferne das erlösende Martinshorn. Die allerletzte Minute bricht an. Was tust du?",
            "choices": [
                {"massnahme": "Ununterbrochen im Sekundentakt das Bewusstsein und die Atembewegungen überwachen, bis das Team vor dir steht.", "rueckmeldung": "Absolut lehrbuchmäßig! Bei einem Spannungspneumothorax kann das Herz-Kreislauf-System sekündlich versagen. Du überwachst ihn lückenlos und übergibst einen lebenden Patienten.", "zeit": 1, "survival": +30, "tod_bonus": +2, "rtw": 0, "next": None, "is_end": True, "end_text": "PERFEKTES ENDE: Der Rettungsdienst trifft ein. Der Notarzt führt sofort eine Entlastungspunktion der Brust durch. Der Mann überlebt!"},
                {"massnahme": "Ihm kräftig auf den Rücken klopfen und ihn auffordern, tiefe Kniebeugen zu machen, um den Kreislauf zu fordern.", "rueckmeldung": "Ein katastrophaler Fehler im allerletzten Moment. Durch die körperliche Belastung schießt der Sauerstoffbedarf in die Höhe. Die kollabierte Lunge kapituliert – Kreislaufkollaps kurz vor Ankunft des Arztes.", "zeit": 1, "survival": -60, "tod_bonus": -15, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Die Baustelle verlassen und zur Hauptstraße rennen, um den Rettungswagen einzuweisen, da der Weg schwer zu finden ist.", "rueckmeldung": "Gefährliche Fehlentscheidung! Du darfst einen Patienten mit akutem Spannungspneumothorax in dieser kritischen Phase niemals allein lassen. Während deiner Abwesenheit verliert er das Bewusstsein und erstickt.", "zeit": 3, "survival": -45, "tod_bonus": -10, "rtw": 0, "next": None, "is_end": True, "end_text": "KRITISCHES ENDE: Du hast den Patienten in der verletzlichsten Phase allein gelassen. Hilfe kam zu spät."}
            ]
        },
        5: {
            "story": "Der Notruf ist beendet, dein Handy liegt auf dem Boden. Doch die Situation ist eskaliert: Der Handwerker liegt flach ausgestreckt auf dem Rücken. Er bewegt sich nicht mehr und aus seinem Mund ist ein bedrohliches, rasselndes Geräusch zu hören. Jede Sekunde zählt. Deine Handlung?",
            "choices": [
                {"massnahme": "Den Körper unverzüglich in die stabile Seitenlage bringen und ihn dabei auf die rechte, verletzte Seite drehen.", "rueckmeldung": "Gerade noch rechtzeitig geschaltet! Die stabile Seitenlage befreit die Atemwege. Dadurch, dass die gesunde Seite oben liegt, kann sie frei arbeiten und Sauerstoff aufnehmen.", "zeit": 2, "survival": +30, "tod_bonus": +4, "rtw": 0, "next": None, "is_end": True, "end_text": "GUTES ENDE: Der Rettungsdienst übernimmt den Patienten. Die stabile Seitenlage auf der verletzten Seite hat sein Leben in letzter Sekunde gerettet."},
                {"massnahme": "In dieser Position verharren, seine Hand halten und warten, bis der alarmierte Rettungswagen eintrifft.", "rueckmeldung": "Fataler Ausgang. In Rückenlage hat der Bewusstlose keine Schutzreflexe mehr. Die Zunge verschließt den Kehlkopf komplett. Der Mann erstickt innerhalb von zwei Minuten.", "zeit": 2, "survival": -50, "tod_bonus": -10, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Den Patienten in die stabile Seitenlage auf die linke, unverletzte Seite drehen, um die schmerzende Stelle zu schonen.", "rueckmeldung": "Medizinischer Fehler! Wenn du ihn auf die gesunde (linke) Seite legst, drückt sein Körpergewicht die einzig noch funktionierende Lunge ab. Da die rechte Lunge kollabiert ist, bekommt er gar keine Luft mehr.", "zeit": 2, "survival": -55, "tod_bonus": -12, "rtw": 0, "next": None, "is_end": True}
            ]
        },
        6: {
            "story": "Der verletzte Mann liegt in der stabilen Seitenlage auf seiner rechten Körperhälfte. Seine Atemwege sind frei. Die Baustelle ist jedoch menschenleer. Du schaust auf die Uhr: Die Minuten verstreichen, aber es ist kein Sirenengeäusch zu hören. Was ist dein nächster Schritt?",
            "choices": [
                {"massnahme": "Das Handy nehmen, die 112 wählen, den Lautsprecher aktivieren und parallel die Atmung des Mannes überwachen.", "rueckmeldung": "Richtig! Du bemerkst, dass bisher noch gar keine Rettungskräfte alarmiert waren. Der RTW wird sofort mit höchster Dringlichkeit losgeschickt und braucht 8 Minuten.", "zeit": 2, "survival": +25, "tod_bonus": 0, "rtw": 8, "next": None, "is_end": True, "end_text": "KNAPPES ENDE: Der Rettungsdienst trifft ein. Dank der korrekten Seitenlage auf der verletzten Seite hat die gesunde Lunge den Patienten gerade so stabil gehalten."},
                {"massnahme": "Den Mann vorsichtig wieder zurück auf den Rücken drehen, um seine Jacke zu öffnen und nach sichtbaren Verformungen zu suchen.", "rueckmeldung": "Ein schwerer Fehler! Das Zurückdrehen hebt die Atemwegssicherung auf. Kosmetische Wundschau hat bei einem internen Lungenkollaps absolut keine Priorität und kostet das Leben.", "zeit": 2, "survival": -60, "tod_bonus": -12, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Den Bewusstlosen in dieser Position liegen lassen und schnell selbst mit dem Auto zum nächsten Krankenhaus fahren, um einen Arzt zu holen.", "rueckmeldung": "Völliger Fehlweg! Einen bewusstlosen Patienten mit akutem Pneumothorax lässt man niemals allein. Die Fahrt dauert viel zu lange. Bei deiner Rückkehr ist der Patient bereits verstorben.", "zeit": 10, "survival": -80, "tod_bonus": -25, "rtw": 0, "next": None, "is_end": True}
            ]
        }
    },
    "diabetes": {
        1: {
            "story": "Du sitzt in der Mittagspause im Pausenraum, als dir ein Kollege auffällt. Er wirkt plötzlich extrem unruhig, zittert an den Händen und auf seiner Stirn steht kalter Schweiß. Als du ihn ansprichst, antwortet er nur lallend und unzusammenhängend. Du weißt jedoch, dass er Diabetiker ist. Er ist noch bei Bewusstsein, wirkt aber zunehmend weggetreten. Wie handelst du?",
            "choices": [
                {"massnahme": "Ihm sofort zwei Plättchen Traubenzucker oder ein Glas zuckerhaltige Cola verabreichen.", "rueckmeldung": "Hervorragend und lebensrettend! Bei einer Unterzuckerung zählt jede Sekunde, da das Gehirn Glukose braucht, um zu funktionieren. Da der Patient noch schlucken kann, ist die sofortige Zuckerzufuhr genau richtig.", "zeit": 1, "survival": +40, "tod_bonus": +10, "rtw": 0, "next": 2, "is_end": False},
                {"massnahme": "Sein Diabetes-Medikament (Insulin) aus der Tasche suchen und ihm eine Dosis spritzen.", "rueckmeldung": "Fataler und tödlicher Fehler! Insulin senkt den Blutzuckerspiegel noch weiter ab. Da der Patient ohnehin schon im kritischen Minusbereich (Unterzucker) ist, raubst du dem Gehirn den allerletzten Rest Zucker. Der Patient fällt sofort ins Koma und stirbt.", "zeit": 2, "survival": -80, "tod_bonus": -30, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Sofort den Notruf 112 wählen, um einen Rettungswagen anzufordern.", "rueckmeldung": "Der Notruf ist zwar wichtig, da sich der Zustand schnell verschlechtern kann. Allerdings verstreicht wertvolle Zeit mit Telefonieren, während der Blutzuckerspiegel des Kollegen im Sekundentakt weiter in den Keller rauscht.", "zeit": 2, "survival": +10, "tod_bonus": -4, "rtw": 10, "next": 3, "is_end": False}
            ]
        },
        2: {
            "story": "Der Kollege hat den Traubenzucker mühsam heruntergeschluckt. Du sitzt neben ihm und wartest. Nach ein paar Minuten merkst du, dass das Zittern leicht nachlässt, er dich wieder fokussiert anblickt und seine Sprache klarer wird. Er ist aber nach wie vor extrem schwach und zittrig. Es wurde bisher noch kein Rettungsdienst verständigt. Was ist dein nächster Schritt?",
            "choices": [
                {"massnahme": "Ihm eine Decke bringen, ihn bitten sich flach hinzulegen und den Raum verlassen, um ihn schlafen zu lassen.", "rueckmeldung": "Sehr gefährlich! Nach einer schweren Unterzuckerung kann der Blutzuckerspiegel jederzeit wieder abfallen. Wenn du ihn jetzt alleine schlafen lässt, merkst du nicht, wenn er ins Koma rutscht. Eine Überwachung ist zwingend erforderlich.", "zeit": 3, "survival": -40, "tod_bonus": -8, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Die 112 anrufen, den Vorfall schildern und den Kollegen bis zum Eintreffen der Retter engmaschig überwachen.", "rueckmeldung": "Völlig richtig! Auch wenn es ihm besser geht, ist eine schwere Unterzuckerung ein medizinischer Notfall, der von Fachpersonal untersucht werden muss. Du sicherst ihn perfekt ab.", "zeit": 2, "survival": +30, "tod_bonus": +5, "rtw": 8, "next": None, "is_end": True, "end_text": "PERFEKTES ENDE: Der Rettungsdienst trifft ein. Dank deiner schnellen Zuckerzufuhr konntest du eine Bewusstlosigkeit verhindern. Die Sanitäter loben dein schnelles Handeln!"},
                {"massnahme": "Ihm eine Tasse starken, ungesüßten schwarzen Kaffee geben, damit sein Kreislauf wieder in Schwung kommt.", "rueckmeldung": "Nutzlos und zeitraubend. Schwarzer Kaffee enthält keinerlei Kohlenhydrate (Zucker). Der Kreislauf braucht Energie (Glukose), kein Koffein. Der Blutzucker sinkt kurz darauf wieder gefährlich tief.", "zeit": 4, "survival": -20, "tod_bonus": -6, "rtw": 0, "next": None, "is_end": True, "end_text": "WEITERES ENDE: Du hast wertvolle Zeit mit Kaffeekochen verschwendet. Der Zucker-Effekt verpuffte und der Patient erlitt einen schweren Rückfall."}
            ]
        },
        3: {
            "story": "Während du noch mit dem Disponenten der Leitstelle sprichst, bricht die Kommunikation zum Kollegen komplett ab. Seine Augen verdrehen sich, er sackt vom Stuhl und bleibt reglos auf dem Boden liegen. Du legst sofort dein Ohr über seinen Mund: Er atmet regelmäßig, reagiert aber überhaupt nicht mehr. Er ist nun tief bewusstlos im sogenannten 'Zuckerschock'. Wie reagierst du?",
            "choices": [
                {"massnahme": "Ihm flüssigen Cola-Sirup oder eine aufgelöste Traubenzucker-Lösung direkt in den Mund gießen.", "rueckmeldung": "Katastrophaler, lebensgefährlicher Fehler! Ein bewusstloser Mensch hat keinerlei Schluck- oder Schutzreflexe mehr. Die Flüssigkeit läuft ungehindert in die Luftröhre und blockiert die Lunge. Der Patient erstickt qualvoll an der flüssigen Zuckermischung.", "zeit": 1, "survival": -70, "tod_bonus": -20, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Den bewusstlosen Kollegen sofort in die stabile Seitenlage bringen, um seine Atemwege zu sichern.", "rueckmeldung": "Großartig! Da der Patient bewusstlos ist, droht er an seiner Zunge oder Erbrochenem zu ersticken. Die stabile Seitenlage hat jetzt oberste Priorität, um sein Überleben zu sichern. Zucker darfst du ihm jetzt ohnehin nicht mehr in den Mund geben.", "zeit": 2, "survival": +40, "tod_bonus": +6, "rtw": 0, "next": 4, "is_end": False}
            ]
        },
        4: {
            "story": "Der Kollege liegt in der stabilen Seitenlage auf dem Boden. Seine Atemwege sind frei. Der Notruf wurde vorhin abgesetzt, aber durch die Verzögerung ist der Rettungswagen noch nicht da. Du hörst draußen noch keine Sirenen. Was tust du in dieser kritischen Wartezeit?",
            "choices": [
                {"massnahme": "Seine Atmung ununterbrochen alle zwei Minuten kontrollieren und den Puls am Handgelenk fühlen.", "rueckmeldung": "Perfekt! Bei einem tiefen Insulinschock kann der Kreislauf jederzeit versagen. Durch deine kontinuierliche Überwachung bist du auf jede Veränderung vorbereitet, bis die Profis übernehmen.", "zeit": 2, "survival": +30, "tod_bonus": +2, "rtw": 0, "next": None, "is_end": True, "end_text": "GUTES ENDE: Der Rettungswagen trifft ein. Der Notarzt spritzt dem bewusstlosen Patienten sofort eine Glukoselösung direkt in die Vene. Dank deiner stabilen Seitenlage ist der Patient während der Bewusstlosigkeit sicher aufgehoben gewesen."},
                {"massnahme": "Ihn wieder auf den Rücken drehen und versuchen, ihm den Mund aufzuhalten, um zu sehen, ob er Traubenzucker-Reste verschluckt hat.", "rueckmeldung": "Schwerer Fehler! Das Auflösen der Seitenlage bringt ihn wieder in akute Erstickungsgefahr. Das Herumwühlen im Mund eines Bewusstlosen ist nutzlos und gefährlich. Du hast eine sichere Position ohne Grund aufgegeben.", "zeit": 2, "survival": -50, "tod_bonus": -10, "rtw": 0, "next": None, "is_end": True},
                {"massnahme": "Mühsam versuchen, seinen Kiefer aufzuhebeln, um ihm eine Tube Flüssigzucker (Flüssig-Traubenzucker) direkt in den Rachen zu pressen.", "rueckmeldung": "Lebensgefährlich! Ein tief Bewusstloser kann nicht schlucken. Die zähe Flüssigkeit läuft direkt in die Luftwege und verklebt die Lunge. Du hast den Patienten im allerletzten Schritt erstickt.", "zeit": 2, "survival": -75, "tod_bonus": -20, "rtw": 0, "next": None, "is_end": True}
            ]
        }
    }
}

RED_PRIMARY = "#b30000"
safe_border = ft.Border(ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd"), ft.BorderSide(1, "#dddddd"))

def main(page: ft.Page):
    page.title = "Erste Hilfe Trainer"
    page.padding = 0
    page.window_width = 420
    page.window_height = 850
    page.scroll = ft.ScrollMode.AUTO
    
    page.theme_mode = ft.ThemeMode.LIGHT
    
    settings = {
        "dark_mode": False, 
        "font_size": 14, 
        "show_images": True,
        "sound_effects": True,
        "stress_mode": False
    }
    
    game_state = {
        "username": "User", 
        "is_scenario": False, 
        "scenario_key": "",
        "node": 1, 
        "survival": 30, 
        "time_passed": 0, 
        "time_to_death": 180, 
        "timer_running": False,
        "current_level_name": ""
    }

    scenarios_view = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    level_view = ft.Column(visible=False, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
    stats_view = ft.Column(visible=False, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
    settings_view = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.AUTO)
    login_view = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def refresh_ui():
        render_scenarios()
        if level_view.visible:
            render_node()
        page.update()

    # Live-Timer (noch nd sichtbar)
    def start_live_timer():
        game_state["timer_running"] = True
        def timer_loop():
            while game_state["timer_running"]:
                time.sleep(1)
                if not game_state["timer_running"]:
                    break
                
                game_state["time_passed"] += 1
                game_state["time_to_death"] -= 1
                
                p_min = game_state["time_passed"] // 60
                p_sec = game_state["time_passed"] % 60
                d_min = max(0, game_state["time_to_death"]) // 60
                d_sec = max(0, game_state["time_to_death"]) % 60
                
                time_text.value = f"Vergangene Zeit: {p_min} Min. {p_sec} Sek. | Zeit bis Kritisch: {d_min} Min. {d_sec} Sek."
                
                # wenn Zeit = 0, Szenarioabbruch
                if game_state["time_to_death"] <= 0:
                    game_state["timer_running"] = False
                    show_timeout()
                    
                page.update()
                
        threading.Thread(target=timer_loop, daemon=True).start()

    # Szenario-Karten
    def render_scenarios():
        scenarios_view.controls.clear()
        scenarios_view.controls.append(
            ft.Container(
                ft.Text(f"Hallo {game_state['username']}!\nWählen Sie ein Szenario:", size=16, weight="bold"), 
                padding=ft.Padding(20, 15, 20, 5)
            )
        )
        
        def create_card(title, desc, emoji, action):
            card_elements = []
            if settings["show_images"]:
                card_elements.append(
                    ft.Container(
                        width=60, height=60, 
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, 
                        border_radius=12, 
                        content=ft.Container(content=ft.Text(emoji, size=28), alignment=ft.alignment.Alignment(0, 0))
                    )
                )
                card_elements.append(ft.VerticalDivider(width=10, color="transparent"))

            card_elements.append(
                ft.Column([
                    ft.Text(title, size=settings["font_size"], weight="bold", width=210),
                    ft.Text(desc, size=settings["font_size"]-3, color="#888888", width=210, max_lines=2),
                    ft.Container(
                        content=ft.Text("Starten", size=10, color="white", weight="bold"), 
                        bgcolor=RED_PRIMARY, padding=ft.Padding(10, 4, 10, 4), border_radius=8, 
                        on_click=action
                    )
                ], spacing=4, expand=True)
            )

            return ft.Container(
                content=ft.Row(card_elements),
                padding=12, border_radius=18, margin=ft.Margin(20, 6, 20, 6), 
                shadow=ft.BoxShadow(blur_radius=6, color="#05000000"), 
                on_click=action, bgcolor=ft.Colors.SURFACE
            )
        
        scenarios_view.controls.append(create_card("Übung: Der perfekte Notruf", "Lerne das richtige Verhalten am Telefon.", "📱", lambda _: start_game("uebung", "Notruf Übung")))
        scenarios_view.controls.append(create_card("Bewusstlose Person im Park", "Bei einem Spaziergang siehst du eine Person.", "🏃", lambda _: start_game("jogger", "Jogger")))
        scenarios_view.controls.append(create_card("Person im Kaufhaus gestürzt", "Beim Einkaufen hörst du einen Schrei.", "🪜", lambda _: start_game("sturz", "Sturz von Leiter")))
        scenarios_view.controls.append(create_card("Die Diabetes-Krise", "Deinem Kollegen geht es plötzlich komisch.", "🩸", lambda _: start_game("diabetes", "Zuckerschock")))

    story_text = ft.Text(size=16, weight="bold", text_align=ft.TextAlign.CENTER)
    time_text = ft.Text(size=13, color="#888888", weight="bold") 
    feedback_text = ft.Text(size=14, color="white")
    feedback_container = ft.Container(content=feedback_text, padding=15, border_radius=15, bgcolor=ft.Colors.BLUE_GREY_700, visible=False)
    choices_col = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    stats_bar_col = ft.Column([
        ft.Row([ft.Text("Überlebenschance:"), ft.Text(weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.ProgressBar(value=0.3, color="green"),
    ], visible=False, width=320)

    def start_game(scenario_key, name):
        game_state["is_scenario"] = (scenario_key != "uebung")
        game_state["scenario_key"] = scenario_key
        game_state["node"] = 1
        game_state["survival"] = 30 if game_state["is_scenario"] else 100
        game_state["time_passed"] = 0
        game_state["time_to_death"] = 180 
        game_state["current_level_name"] = name
        
        scenarios_view.visible = False
        level_view.visible = True
        stats_bar_col.visible = game_state["is_scenario"]
        
        render_node()
        start_live_timer()

    def render_node():
        if game_state["is_scenario"]:
            data = szenarien_sammlung[game_state["scenario_key"]][game_state["node"]]
        else:
            data = uebung_daten[game_state["node"]]
            
        story_text.value = data["story"]
        feedback_container.visible = False
        choices_col.controls.clear()
        
        for choice in data["choices"]:
            choices_col.controls.append(
                ft.Container(
                    content=ft.Row([ft.Text(choice["massnahme"], size=settings["font_size"], weight="bold", text_align=ft.TextAlign.CENTER, color=RED_PRIMARY)], alignment="center"), 
                    padding=12, border_radius=10, width=320, 
                    border=ft.Border(ft.BorderSide(1.5, RED_PRIMARY), ft.BorderSide(1.5, RED_PRIMARY), ft.BorderSide(1.5, RED_PRIMARY), ft.BorderSide(1.5, RED_PRIMARY)), 
                    on_click=lambda e, c=choice: handle_choice(c), bgcolor=ft.Colors.SURFACE
                )
            )
            
        s_val = max(0, min(99, game_state["survival"]))
        stats_bar_col.controls[1].value = s_val / 100
        stats_bar_col.controls[0].controls[1].value = f"{s_val}%"
        page.update()

    def handle_choice(choice):
        game_state["survival"] += choice["survival"]
        game_state["time_passed"] += choice["zeit"]
        game_state["time_to_death"] += choice["tod_bonus"] - choice["zeit"]
        
        feedback_text.value = choice["rueckmeldung"]
        feedback_container.visible = True
        
        choices_col.controls.clear()
        
        if choice["is_end"]:
            game_state["timer_running"] = False
            choices_col.controls.append(
                ft.ElevatedButton("Szenario abschließen", on_click=lambda _: show_final_result(choice), bgcolor="green", color="white", width=250)
            )
        elif game_state["time_to_death"] <= 0:
            game_state["timer_running"] = False
            show_timeout()
        else:
            choices_col.controls.append(
                ft.ElevatedButton("Weiter >", on_click=lambda _: move_to_node(choice["next"]), bgcolor=RED_PRIMARY, color="white", width=250)
            )
        page.update()

    def move_to_node(n):
        game_state["node"] = n
        render_node()

    def show_final_result(choice):
        final_survival = max(0, min(99, game_state["survival"]))
        success = final_survival >= 50
        end_msg = choice.get("end_text", "Einsatz beendet.")
        
        story_text.value = "ABSCHLUSS"
        choices_col.controls.clear()
        choices_col.controls.append(ft.Text(end_msg, size=15, text_align=ft.TextAlign.CENTER, weight="bold", color="green" if success else "red"))
        choices_col.controls.append(ft.ElevatedButton("ZURÜCK ZUM MENÜ", on_click=lambda _: show_menu(), bgcolor="black", color="white", width=250))
        
        save_result(game_state["username"], game_state["current_level_name"], final_survival, success)
        page.update()

    def show_timeout():
        story_text.value = "ZEIT ABGELAUFEN!"
        choices_col.controls.clear()
        choices_col.controls.append(ft.Text("Du warst leider zu langsam! Der Zustand ist kritisch.", size=15, text_align=ft.TextAlign.CENTER, weight="bold", color="red"))
        choices_col.controls.append(ft.ElevatedButton("ZURÜCK ZUM MENÜ", on_click=lambda _: show_menu(), bgcolor="black", color="white", width=250))
        save_result(game_state["username"], game_state["current_level_name"], 0, False)
        page.update()

    def show_menu():
        game_state["timer_running"] = False
        scenarios_view.visible = True
        level_view.visible = False
        refresh_ui()

    # Settings
    def build_settings():
        settings_view.controls.clear()
        
        dp_mode = ft.Dropdown(label="Mode", options=[ft.dropdown.Option("Light Mode"), ft.dropdown.Option("Dark Mode")], value="Dark Mode" if settings["dark_mode"] else "Light Mode")
        dp_font = ft.Dropdown(label="Schrift", options=[ft.dropdown.Option("Größe 12"), ft.dropdown.Option("Größe 14"), ft.dropdown.Option("Größe 16")], value=f"Größe {settings['font_size']}")
        dp_images = ft.Dropdown(label="Bilder", options=[ft.dropdown.Option("An"), ft.dropdown.Option("Aus")], value="An" if settings["show_images"] else "Aus")
        dp_sound = ft.Dropdown(label="Soundeffekte", options=[ft.dropdown.Option("An"), ft.dropdown.Option("Aus")], value="An" if settings["sound_effects"] else "Aus")
        dp_stress = ft.Dropdown(label="Stress", options=[ft.dropdown.Option("An"), ft.dropdown.Option("Aus")], value="An" if settings["stress_mode"] else "Aus")

        def save_settings_click(e):
            settings["dark_mode"] = (dp_mode.value == "Dark Mode")
            settings["font_size"] = int(dp_font.value.split()[1])
            settings["show_images"] = (dp_images.value == "An")
            settings["sound_effects"] = (dp_sound.value == "An")
            settings["stress_mode"] = (dp_stress.value == "An")
            
            page.theme_mode = ft.ThemeMode.DARK if settings["dark_mode"] else ft.ThemeMode.LIGHT
            refresh_ui()

        visuell_content = ft.Column([
            ft.Text("Visuell", weight="bold", size=16),
            dp_mode, dp_font, dp_images
        ], spacing=15)

        audio_content = ft.Column([
            ft.Text("Audio", weight="bold", size=16),
            dp_sound, dp_stress
        ], spacing=15)

        settings_view.controls.append(
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Einstellungen", size=22, weight="bold"),
                    ft.Container(content=visuell_content, padding=20, border_radius=15, border=safe_border, bgcolor=ft.Colors.SURFACE),
                    ft.Container(content=audio_content, padding=20, border_radius=15, border=safe_border, bgcolor=ft.Colors.SURFACE),
                    ft.ElevatedButton("Änderungen speichern & übernehmen", on_click=save_settings_click, bgcolor=RED_PRIMARY, color="white", width=320)
                ], spacing=20)
            )
        )

    level_view.controls = [
        ft.Container(story_text, padding=25, border_radius=20, shadow=ft.BoxShadow(blur_radius=5, color="#dddddd"), width=350, bgcolor=ft.Colors.SURFACE), 
        ft.Divider(height=10, color="transparent"), 
        time_text, 
        stats_bar_col, 
        feedback_container, 
        choices_col
    ]

    #Statistik
    history_list = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def update_history_list(limit_val):
        games = get_last_games(game_state["username"], limit_val)
        history_list.controls.clear()
        
        if not games:
            history_list.controls.append(ft.Text("Noch keine Daten vorhanden.", color="#888888"))
            return

        for level_name, chance, datum in games:
            color_text = "green" if chance >= 50 else RED_PRIMARY
            history_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{datum}", size=12, color="#888888"),
                        ft.Text(f"{level_name}", size=13, weight="bold", expand=True),
                        ft.Text(f"{chance}% Chance", size=13, weight="bold", color=color_text)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10, border_radius=8, border=safe_border, width=320, bgcolor=ft.Colors.SURFACE
                )
            )

    def build_stats_view(limit_default=4):
        s = get_general_stats(game_state["username"])
        filter_dropdown = ft.Dropdown(options=[ft.dropdown.Option("3"), ft.dropdown.Option("4"), ft.dropdown.Option("5")], value=str(limit_default), width=70)
        filter_dropdown.on_change = lambda e: build_stats_view(int(e.control.value))
        update_history_list(limit_default)

        leaderboard_data = get_leaderboard()
        table_rows = []
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, row in enumerate(leaderboard_data):
            table_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(emojis[i])), 
                    ft.DataCell(ft.Text(row[0])), 
                    ft.DataCell(ft.Text(f"{row[1]}%"))
                ])
            )
        
        if not table_rows:
            table_rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("Keine Daten")), ft.DataCell(ft.Text("-"))]))

        friends_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Rang", size=12, weight="bold")),
                ft.DataColumn(ft.Text("Username", size=12, weight="bold")),
                ft.DataColumn(ft.Text("Bestwert", size=12, weight="bold")),
            ],
            rows=table_rows, heading_row_height=35, data_row_max_height=30
        )

        stats_view.controls = [
            ft.Container(ft.Column([
                ft.Text("Statistiken", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
                ft.Text(f"Konto: {game_state['username']}", size=14, color="#666666", text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10),
            ft.Text("Verlauf der letzten Runden:", weight="bold", size=14),
            history_list,
            ft.Text(f"Durchschnittsquote: {s['avg_chance']}%", size=14, weight="bold"),
            ft.Row([ft.Text("Zeige letzte"), filter_dropdown, ft.Text("Szenarien.")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=20),
            ft.Text("Globale Rangliste (Top 5)", weight="bold", size=15),
            ft.Container(content=friends_table, border_radius=10, padding=5, border=safe_border, bgcolor=ft.Colors.SURFACE)
        ]

    def on_nav(e):
        idx = int(e.data)
        scenarios_view.visible = (idx == 1)
        stats_view.visible = (idx == 0)
        settings_view.visible = (idx == 2)
        level_view.visible = False
        
        if idx == 2: build_settings()
        elif idx == 0: build_stats_view()
        refresh_ui()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Statistik"), 
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Szenarien"), 
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings")
        ], 
        selected_index=1, on_change=on_nav, height=70, visible=False
    )

    def login_click(e):
        if name_input.value.strip():
            game_state["username"] = name_input.value.strip()
            login_view.visible = False
            page.navigation_bar.visible = True
            app_layout.visible = True
            refresh_ui()

    name_input = ft.TextField(label="Dein Username", width=280, on_submit=login_click)
    login_view.controls = [
        ft.Divider(height=40, color="transparent"),
        ft.Container(
            content=ft.Column([
                ft.Text("Bitte erstelle ein Profil", size=18, weight="bold", text_align=ft.TextAlign.CENTER),
                ft.Text("Deine Spielstände werden dauerhaft in der SQLite-Datenbank gesichert.", size=12, color="#666666", text_align=ft.TextAlign.CENTER),
                name_input,
                ft.ElevatedButton("Starten", on_click=login_click, bgcolor=RED_PRIMARY, color="white", width=200)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            padding=25, border_radius=20, border=safe_border, width=340, bgcolor=ft.Colors.SURFACE
        )
    ]

    header = ft.Container(
        content=ft.Row([
            ft.Column([ft.Text("ERSTE HILFE", size=22, weight="bold", color="white"), ft.Text("TRAINER", size=22, weight="bold", color="white")], spacing=0, alignment="center"),
            ft.Icon(ft.Icons.MONITOR_HEART, color="white", size=50)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=RED_PRIMARY, padding=ft.Padding(25, 40, 25, 20), border_radius=ft.BorderRadius(0, 0, 30, 30), shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
    )

    app_layout = ft.Column([
        header, 
        ft.Container(content=ft.Stack([scenarios_view, level_view, stats_view, settings_view]), expand=True)
    ], expand=True, spacing=0, visible=False)
    
    page.add(login_view, app_layout)

if __name__ == "__main__":
    ft.app(target=main)
