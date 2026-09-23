================================================================================
HABIT TRACKER - README
================================================================================

Video Demo: https://youtu.be/vBPw9FGHtkQ

1. PROJEKTBESCHREIBUNG
--------------------------------------------------------------------------------
Habit Tracker ist eine Web-Anwendung, mit der Nutzerinnen und Nutzer eigene
Gewohnheiten anlegen, taeglich abhaken und ihren Fortschritt ueber Serien
(Streaks), Erfolgsquoten und Diagramme verfolgen koennen. Die App richtet
sich an Menschen, die neue Gewohnheiten aufbauen oder bestehende im Blick
behalten wollen, und dient hier als Portfolio-Projekt zum Zeigen von
Full-Stack-Kenntnissen mit Python und Flask.

Jeder Nutzer hat einen eigenen Account und sieht ausschliesslich seine
eigenen Daten. Gewohnheiten lassen sich taeglich, woechentlich oder an
bestimmten Wochentagen verfolgen, in Kategorien und mit Tags ordnen und
ueber eine Volltextsuche mit Filtern wiederfinden.


2. FUNKTIONSUEBERSICHT
--------------------------------------------------------------------------------
- Registrierung, Login/Logout, "Angemeldet bleiben", Profilseite
- Gewohnheiten anlegen, bearbeiten, loeschen, archivieren/wiederherstellen
- Kategorien und Tags verwalten (eigenes CRUD)
- Taegliches Abhaken per Klick ohne Neuladen der Seite (Ajax)
- Nachtragen vergangener Tage mit optionaler Notiz
- Automatische Berechnung von aktueller Serie, laengster Serie und
  Erfolgsquote (7 / 30 / 90 Tage)
- Volltextsuche, Filter (Kategorie, Tag, Haeufigkeit, Status, heute
  erledigt/offen), Sortierung, Pagination, Live-Suche
- Statistik-Seite mit Chart.js-Diagrammen, Kalender-Heatmap und
  Meilenstein-Abzeichen (7, 30, 100 Tage)
- Taegliches Motivationszitat (externe API mit lokalem Fallback)
- Optionaler Wetter-Hinweis fuer Outdoor-Gewohnheiten (Open-Meteo)
- Dark Mode, in der Datenbank gespeichert
- Toast-Benachrichtigungen und Bestaetigungsdialog vor dem Loeschen
- Eigene 404-, 429- und 500-Fehlerseiten
- Responsives Design (Mobile First)


3. SEITEN UND BEDIENUNG
--------------------------------------------------------------------------------
Startseite (/)
  Landingpage mit kurzer Vorstellung. Angemeldete Nutzer werden direkt
  zum Dashboard weitergeleitet.

Registrierung (/registrieren) und Login (/login)
  Konto erstellen bzw. anmelden. Beim Login kann "Angemeldet bleiben"
  aktiviert werden.

Dashboard "Heute" (/heute)
  Zeigt alle heute faelligen Gewohnheiten mit grosser Checkbox zum
  Abhaken, den Tagesfortschritt als Balken, ein Tageszitat und bei
  konfiguriertem Standort einen Wetter-Hinweis.

Gewohnheiten-Liste (/habits)
  Alle eigenen Gewohnheiten mit Suche, Filtern und Sortierung. Ueber
  die Reiter im Status-Filter zwischen aktiven und archivierten
  Gewohnheiten wechseln.

Gewohnheit anlegen/bearbeiten (/habits/neu, /habits/<id>/bearbeiten)
  Formular fuer Titel, Beschreibung, Kategorie, Haeufigkeit (taeglich,
  woechentlich oder bestimmte Wochentage), Startdatum und Tags.

Gewohnheit-Detailseite (/habits/<id>)
  Aktuelle und laengste Serie, Erfolgsquoten, die letzten 14 faelligen
  Tage zum Abhaken sowie ein Formular zum Nachtragen vergangener Tage
  mit Notiz.

Kategorien (/kategorien) und Tags (/tags)
  Eigene Kategorien (Name, Farbe, Symbol) und Tags anlegen, bearbeiten
  und loeschen.

Statistiken (/statistiken)
  Diagramme zu woechentlichen Erledigungen, Erfolgsquote je Gewohnheit
  und Verteilung nach Kategorie, dazu eine Kalender-Heatmap und
  erreichte Meilensteine.

Profil (/profil)
  E-Mail und Passwort aendern, Darstellung (hell/dunkel) waehlen,
  Konto samt aller Daten loeschen.

Erste Gewohnheit anlegen und abhaken (Kurzanleitung)
  1. Registrieren und einloggen.
  2. Unter "Gewohnheiten" auf "Neue Gewohnheit" klicken.
  3. Titel eingeben, Haeufigkeit waehlen, speichern.
  4. Auf "Heute" die Checkbox der neuen Gewohnheit anklicken.


4. TECH-STACK
--------------------------------------------------------------------------------
- Python 3.11+ (getestet mit 3.13)
- Flask 3 (Application Factory + Blueprints)
- Flask-SQLAlchemy mit SQLite als Datenbank
- Flask-Login fuer Sessions und Login-Pflicht
- Flask-WTF fuer Formulare und CSRF-Schutz
- Flask-Limiter fuer Rate-Limiting bei Login und Registrierung
- Werkzeug fuer sicheres Passwort-Hashing
- python-dotenv zum Einlesen der .env-Datei
- Jinja2-Templates mit Bootstrap 5 und Bootstrap Icons (per CDN)
- Chart.js (per CDN) fuer die Diagramme auf der Statistik-Seite
- Eigenes CSS und Vanilla-JavaScript (fetch, keine Frameworks)
- ZenQuotes-API fuer das taegliche Zitat
- Open-Meteo-API fuer den optionalen Wetter-Hinweis
- pytest fuer die automatisierten Tests


5. PROJEKTSTRUKTUR
--------------------------------------------------------------------------------
project/
  app/
    __init__.py         create_app(), Fehlerseiten, Blueprint-Registrierung
    extensions.py        db, login_manager, csrf, limiter
    forms.py              alle Flask-WTF-Formulare
    models.py             Datenbankmodelle
    utils.py               owned_or_404, today_local (Zeitzone)
    auth/routes.py       Registrierung, Login/Logout, Profil
    main/routes.py       Startseite, Dashboard "Heute"
    habits/routes.py     Gewohnheiten-, Kategorien- und Tag-CRUD
    stats/routes.py      Statistik-Seite
    api/routes.py         interne JSON-Endpunkte (Suche, Abhaken, Stats)
    services/
      streaks.py           Serien-, Erfolgsquoten- und Meilenstein-Logik
      tracking.py           Abfragen und Speichern von Eintraegen
      search.py             Suche, Filter, Sortierung, Pagination
      quotes.py              Zitat-API mit Cache und Fallback
      weather.py             Wetter-API mit Cache
    static/css/style.css  eigenes Design
    static/js/app.js        Ajax-Abhaken, Live-Suche, Toasts, Dialoge
    templates/               Jinja2-Vorlagen (auth/, habits/, stats/, errors/)
  tests/                      pytest-Tests, ein File je Themenbereich
  seed.py                    legt einen Demo-Nutzer mit Beispieldaten an
  config.py                 Konfiguration (liest die .env)
  requirements.txt         Python-Abhaengigkeiten
  .env.example               Vorlage fuer die eigene .env
  pytest.ini                  pytest-Einstellungen
  README.md                 diese Datei


6. DATENBANK
--------------------------------------------------------------------------------
users
  id, username (eindeutig), email (eindeutig), password_hash,
  created_at, theme (light/dark)

categories
  id, user_id (FK), name, color, icon
  eindeutig je Nutzer: (user_id, name)

habits
  id, user_id (FK), category_id (FK, optional), title, description,
  frequency (daily/weekly/weekdays), weekdays, target_per_period,
  start_date, is_archived, created_at

habit_logs
  id, habit_id (FK), date, completed, note
  eindeutig: (habit_id, date)

tags
  id, user_id (FK), name
  eindeutig je Nutzer: (user_id, name)

habit_tags
  Zuordnungstabelle zwischen habits und tags (n zu m)

goals
  id, habit_id (FK), target_streak, deadline, achieved
  Tabelle ist vorbereitet, wird aktuell aber noch nicht ueber die
  Oberflaeche verwendet (siehe Abschnitt WEITERENTWICKLUNG).

Beziehungen
  users        1 --- n  categories
  users        1 --- n  habits
  users        1 --- n  tags
  categories   1 --- n  habits          (Kategorie loeschen: category_id
                                          wird bei den Habits auf NULL
                                          gesetzt, Habits bleiben erhalten)
  habits       1 --- n  habit_logs      (Loeschen kaskadiert)
  habits       1 --- n  goals           (Loeschen kaskadiert)
  habits       n --- m  tags            (ueber habit_tags, Loeschen
                                          kaskadiert auf beiden Seiten)

Beim Loeschen eines Nutzers werden alle seine Kategorien, Gewohnheiten,
Eintraege, Tags und Ziele automatisch mitgeloescht (Cascade).


7. ROUTENUEBERSICHT
--------------------------------------------------------------------------------
Methode  URL                              Zweck                    Login
--------------------------------------------------------------------------------
GET      /                                Startseite               nein
GET      /heute                           Dashboard "Heute"        ja
GET/POST /registrieren                    Registrierung            nein
GET/POST /login                           Anmelden                 nein
POST     /logout                          Abmelden                 ja
GET      /profil                          Profilseite              ja
POST     /profil/email                    E-Mail aendern           ja
POST     /profil/passwort                 Passwort aendern         ja
POST     /profil/theme                    Darstellung speichern    ja
POST     /profil/loeschen                 Konto loeschen           ja
GET      /habits                          Gewohnheiten-Liste       ja
GET/POST /habits/neu                      Gewohnheit anlegen       ja
GET      /habits/<id>                     Gewohnheit-Details       ja
POST     /habits/<id>/eintrag             Eintrag nachtragen       ja
GET/POST /habits/<id>/bearbeiten          Gewohnheit bearbeiten    ja
POST     /habits/<id>/loeschen            Gewohnheit loeschen      ja
POST     /habits/<id>/archivieren         Archivieren/Wiederherst. ja
GET/POST /kategorien                      Kategorien-Liste/Anlegen ja
GET/POST /kategorien/<id>/bearbeiten      Kategorie bearbeiten     ja
POST     /kategorien/<id>/loeschen        Kategorie loeschen       ja
GET/POST /tags                            Tag-Liste/Anlegen        ja
GET/POST /tags/<id>/bearbeiten            Tag bearbeiten           ja
POST     /tags/<id>/loeschen              Tag loeschen             ja
GET      /statistiken                     Statistik-Seite          ja
GET      /api/habits/suche                interne Suche (JSON)     ja
POST     /api/habits/<id>/log             Abhaken/Eintrag (JSON)   ja
GET      /api/stats/uebersicht            Diagrammdaten (JSON)     ja


8. EXTERNE API
--------------------------------------------------------------------------------
Zitat-API (ZenQuotes, https://zenquotes.io)
  Liefert das taegliche Motivationszitat auf dem Dashboard. Die Anfrage
  hat ein Timeout von 5 Sekunden. Das Ergebnis wird 6 Stunden lang im
  Arbeitsspeicher zwischengespeichert (Cache), damit nicht bei jedem
  Seitenaufruf neu angefragt wird. Schlaegt die Anfrage fehl (Timeout,
  kein Netz, ungueltige Antwort), wird automatisch eines von acht fest
  hinterlegten deutschen Zitaten angezeigt. Die Seite funktioniert in
  diesem Fall ganz normal weiter.

Wetter-API (Open-Meteo, https://open-meteo.com, kein API-Key noetig)
  Zeigt einen kurzen Wetter-Hinweis auf dem Dashboard, gedacht als
  Anhaltspunkt fuer Outdoor-Gewohnheiten. Ort wird ueber WEATHER_LAT
  und WEATHER_LON in der .env festgelegt; ohne eigene Angabe wird
  automatisch Stuttgart verwendet. Timeout 5 Sekunden, Cache 30
  Minuten. Schlaegt die Anfrage fehl, wird die Wetterkarte einfach
  nicht angezeigt, es gibt keine Fehlermeldung auf der Seite.


9. SICHERHEIT
--------------------------------------------------------------------------------
Passwort-Hashing
  Passwoerter werden nie im Klartext gespeichert. Werkzeug erzeugt
  beim Speichern automatisch einen zufaelligen Salt, dieselben
  Passwoerter ergeben deshalb unterschiedliche Hashes.

CSRF-Schutz
  Flask-WTF prueft bei jedem POST-Request ein Sicherheits-Token, auch
  bei den Ajax-Anfragen zum Abhaken und bei der Live-Suche (Token wird
  dort ueber einen Header mitgeschickt).

Ownership-Checks
  Jede Route, die eine bestimmte Gewohnheit, Kategorie oder einen Tag
  laedt, prueft zuerst, ob der Datensatz dem angemeldeten Nutzer
  gehoert. Gehoert er einem anderen Nutzer, liefert die Seite bewusst
  "404 Nicht gefunden" statt "403 Verboten" zurueck, damit niemand von
  aussen erfaehrt, ob eine bestimmte ID ueberhaupt existiert.

SECRET_KEY und Konfiguration
  Der SECRET_KEY und alle anderen Einstellungen kommen ausschliesslich
  aus der .env-Datei, nie direkt aus dem Code. Ohne gesetzten
  SECRET_KEY startet die App gar nicht erst.

Sichere Cookies und Weiterleitungen
  Sitzungs-Cookies sind HttpOnly und SameSite=Lax gesetzt. Nach dem
  Login wird nur auf Adressen der eigenen Website weitergeleitet, eine
  manipulierte "next"-Adresse zu einer fremden Seite wird abgelehnt.

Rate-Limiting
  Login ist auf 10 Versuche pro Minute begrenzt, die Registrierung auf
  5 pro Minute, um automatisiertes Ausprobieren zu erschweren.

Datenbankzugriffe
  Alle Datenbankabfragen laufen ueber SQLAlchemy (ORM), es wird nie
  SQL per String-Verkettung gebaut. Jinja2 escaped alle ausgegebenen
  Werte automatisch gegen Cross-Site-Scripting.


10. INSTALLATION UND START
--------------------------------------------------------------------------------
Voraussetzung: Python 3.11 oder neuer ist installiert.

Windows (PowerShell)
  1. python --version               (pruefen, ob Python installiert ist)
  2. cd project
  3. python -m venv venv
  4. .\venv\Scripts\Activate.ps1
     (bei Fehlermeldung zur Skriptausfuehrung einmalig:
      Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
  5. pip install -r requirements.txt
  6. copy .env.example .env
  7. In der .env einen SECRET_KEY eintragen, erzeugbar mit:
     python -c "import secrets; print(secrets.token_hex(32))"
  8. python seed.py               (optional: Demo-Daten anlegen)
  9. flask run
  10. Im Browser http://127.0.0.1:5000 oeffnen

macOS
  1. python3 --version
  2. cd project
  3. python3 -m venv venv
  4. source venv/bin/activate
  5. pip install -r requirements.txt
  6. cp .env.example .env
  7. SECRET_KEY wie oben erzeugen und in .env eintragen
  8. python seed.py               (optional)
  9. flask run
  10. Im Browser http://127.0.0.1:5000 oeffnen

Linux
  Gleiche Schritte wie macOS. Falls "python3" fehlt, "python" nutzen.
  In manchen Umgebungen (z. B. Codespaces) heisst die Aktivierung
  ebenfalls "source venv/bin/activate", auch unter Windows-Hosts.

Die SQLite-Datenbank wird beim ersten Start automatisch im Ordner
"instance/" angelegt, ein manuelles Initialisieren ist nicht noetig.


11. DEMO-ZUGANGSDATEN
--------------------------------------------------------------------------------
Nach dem Ausfuehren von "python seed.py":
  Benutzername: demo
  Passwort:     demo1234

Der Demo-Nutzer hat drei Kategorien, zwei Tags und drei Gewohnheiten
mit rund 40 Tagen an Eintraegen, damit Dashboard und Statistiken
gleich mit echten Daten gefuellt sind.


12. TESTS
--------------------------------------------------------------------------------
Ausfuehren (venv muss aktiv sein):
  pytest

Die Tests sind nach Themen aufgeteilt:
  test_auth.py           Registrierung, Login, Passwort-Hashing, Profil
  test_habits.py         Habit-CRUD, Ownership-Checks
  test_categories_tags.py Kategorien- und Tag-CRUD
  test_tracking.py       Streak-Berechnung, Abhaken-API, Dashboard
  test_search.py         Suche, Filter, Sortierung, Pagination
  test_stats.py          Statistik-Endpunkt
  test_quotes.py         Zitat-API inkl. Fallback (ohne echten Netzzugriff)
  test_weather.py        Wetter-API inkl. Fallback (ohne echten Netzzugriff)
  test_rate_limit.py     Rate-Limiting bei Login und Registrierung

Alle Tests laufen gegen eine eigene In-Memory-Datenbank und greifen
nicht auf das echte Internet zu (externe APIs werden in den Tests
durch Platzhalter ersetzt).


13. HAEUFIGE PROBLEME
--------------------------------------------------------------------------------
1. ModuleNotFoundError: No module named 'app.xxx'
   Eine Datei oder ein Ordner unter app/ fehlt oder ist falsch benannt.
   Mit "find app -type f | sort" pruefen, welche Datei fehlt.

2. venv laesst sich nicht aktivieren
   Unter Linux/macOS: source venv/bin/activate
   Unter Windows (PowerShell): .\venv\Scripts\Activate.ps1
   Bei "Ausfuehrung von Skripts deaktiviert": einmalig
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned ausfuehren.

3. RuntimeError: SECRET_KEY fehlt
   Die .env-Datei fehlt oder der SECRET_KEY ist darin leer. .env aus
   .env.example erstellen und einen Wert eintragen.

4. Port 5000 ist bereits belegt
   Mit "flask run --port 5001" einen anderen Port verwenden oder den
   Prozess beenden, der Port 5000 blockiert.

5. "no such table" beim Registrieren
   Die Tabellen werden normalerweise beim Start automatisch angelegt.
   Tritt der Fehler trotzdem auf, den Ordner "instance/" loeschen und
   die App neu starten.

6. Zitat oder Wetter erscheinen nicht wie erwartet
   Kein Fehler: Ist die Zitat-API nicht erreichbar, erscheint
   automatisch ein lokales Zitat. Ist keine Wetter-Koordinate gesetzt
   oder die Wetter-API nicht erreichbar, bleibt die Wetterkarte
   einfach weg.


14. WEITERENTWICKLUNG
--------------------------------------------------------------------------------
- Ziele (goals) ueber eine eigene Oberflaeche nutzbar machen (Tabelle
  ist in der Datenbank bereits vorbereitet)
- E-Mail-Erinnerungen fuer noch offene Gewohnheiten
- Passwort-Reset per E-Mail
- REST-API mit Token-Authentifizierung fuer mobile Clients
- Progressive Web App (Offline-Faehigkeit, Installierbarkeit)
- Mehrsprachigkeit (aktuell nur Deutsch)
- Deployment z. B. mit Gunicorn und Nginx oder als Docker-Container


15. AUTOR
--------------------------------------------------------------------------------
Autor:  Eric Esaulkov
Kontakt: esaulkoveric@gmail.com
================================================================================
