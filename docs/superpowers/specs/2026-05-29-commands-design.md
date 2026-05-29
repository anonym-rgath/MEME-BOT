# Design: Befehle zusätzlich zu Buttons

## Context

Der Meme-Bot wird aktuell rein über Inline-Buttons bedient (Bild schicken → Buttons → mehrere
Schritte). Für schnellere Bedienung sollen **Befehle** hinzukommen — **ergänzend**, die Buttons
bleiben. Beispiel: statt durch Buttons zu tippen, direkt `/text Oben | Unten`.

Gewünschtes Ergebnis: Power-User können eine Aktion in **einem** Schritt auslösen — entweder als
**Bildunterschrift** beim Senden oder als **Folgenachricht** zum zuletzt gesendeten Bild — während
Gelegenheitsnutzer weiterhin die Buttons nutzen.

## Scope

- Befehle **ergänzen** die Buttons (kein Ersatz).
- Befehlssatz (Englisch):
  - `/text Oben | Unten` — Meme-Text hinzufügen.
  - `/face <Name>` — Gesicht tauschen mit gespeichertem Gesicht (nur Bild).
  - `/clean` — Text entfernen (nur Bild).
  - `/recaption Oben | Unten` — säubern + neu betexten (nur Bild).
  - `/help` — Befehlsübersicht; `/start` erwähnt die Befehle zusätzlich.
- **Bildbezug:** sowohl **Bildunterschrift** (Befehl in der Caption des Bildes) als auch
  **Folgenachricht** (Befehl als Textnachricht, nutzt das zuletzt gesendete Bild aus der Session).
- Wiederverwendung der bestehenden Pipeline (`_process_and_send`) inkl. Video-Guard & Temp-Cleanup.

## Text-Parsing-Regeln

- Trenner ist das erste `|`: `top` = links (gestrippt), `bottom` = rechts (gestrippt).
- Kein `|` → `top` = Rest, `bottom` = None.
- `/text` und `/recaption` ohne jeglichen Text → Fehlermeldung mit Kurz-Usage.
- `/face` ohne Namen → Fehlermeldung mit Kurz-Usage; Name ist der komplette Rest (darf Leerzeichen
  enthalten), wird über die bestehende `FaceLibrary`-Sanitisierung aufgelöst.
- `/clean` nimmt keine Argumente.

## Komponenten

| Einheit | Aufgabe | Status |
|---|---|---|
| `bot/commands.py` | **Reine** Funktion `parse_command(raw) -> ParsedCommand \| None`. Zerlegt eine Befehlszeile in Aktion + Argumente (top/bottom/face). Kein Telegram-Import → voll unit-testbar. Gibt `None` zurück, wenn der Text kein bekannter Befehl ist. | **neu** |
| `bot/handlers.py` | `on_media` erkennt eine Caption mit führendem `/` → parst & führt aus statt Buttons. Vier `CommandHandler` (text/face/clean/recaption) für Folgenachrichten → nutzen `sess.media_path`. Beide Wege rufen eine gemeinsame `_run_command(...)`, die die Session befüllt und `_process_and_send` startet. `/help` + erweiterte `/start`-Nachricht. | erweitern |
| `bot/app.py` | Vier neue `CommandHandler` + `/help` registrieren. | erweitern |

### `ParsedCommand`

Ein kleiner Datencontainer (dataclass) mit Feldern:
- `action: str` — einer von `"text" | "face" | "clean" | "recaption"`.
- `top: str | None`, `bottom: str | None` — für `text`/`recaption`.
- `face: str | None` — für `face`.
- `error: str | None` — gesetzt, wenn der Befehl erkannt, aber unvollständig ist (z.B. `/text`
  ohne Inhalt). Trägt eine fertige Usage-Meldung für den Nutzer.

`parse_command` gibt `None` zurück, wenn die Zeile kein bekannter Befehl ist (dann normaler
Button-/Text-Flow). Bei bekanntem Befehl mit fehlenden Pflichtargumenten kommt ein
`ParsedCommand` mit gesetztem `error`.

## Datenfluss

1. **Caption-Modus:** Bild mit Caption `/text A | B` → `on_media` lädt das Bild, sieht die Caption
   (führendes `/`) → `parse_command` → bei Erfolg `_run_command` → Session befüllen → Pipeline.
   Bei Caption ohne führenden `/` → bisheriges Button-Verhalten.
2. **Folgenachricht-Modus:** `/text A | B` als Textnachricht → zugehöriger `CommandHandler` →
   prüft `sess.media_path` (kein Bild → „📷 Schick mir zuerst ein Bild.") → `parse_command` →
   `_run_command` → Pipeline.
3. **`_run_command`** setzt `sess.action`, `sess.top_text`, `sess.bottom_text`, `sess.chosen_face`
   gemäß `ParsedCommand`, übernimmt `sess.is_video`/`sess.media_path` aus der Session/dem Caption-
   Bild, wendet den **bestehenden Video-Guard** an (Cloud-Aktionen `face`/`clean`/`recaption` auf
   Video → freundliche Ablehnung) und ruft `_process_and_send`. `/text` auf Video ist erlaubt.

## Fehlerbehandlung

- Unbekannter Befehl als Folgenachricht: keine Reaktion nötig (oder kurzer Hinweis via `/help`).
- Bekannter Befehl, fehlende Argumente → `ParsedCommand.error` mit Usage; Bot sendet diese.
- `/face <Name>` nicht in der Bibliothek → bestehende „Gesicht nicht gefunden"-Meldung der Pipeline.
- Kein Bild bei Folgebefehl → „📷 Schick mir zuerst ein Bild."
- Cloud-Befehl auf Video → bestehende „kommt später"-Meldung.

## Testing

- **Unit-Tests `bot/commands.py`** ausgiebig: jeder Befehl; `|`-Trennung (mit/ohne, Whitespace);
  `/face` mit/ohne Namen; `/clean` ohne Args; unbekannter Text → `None`; fehlende Pflichtargumente
  → `error` gesetzt.
- Handler-/CommandHandler-Verdrahtung via manuelles E2E (wie gehabt).

## Offene Punkte

- Keine — nutzt vorhandene Provider/Pipeline; keine neuen externen Abhängigkeiten.

## Verifikation (E2E)

1. Bild mit Caption `/text Oben | Unten` → Meme mit Text zurück (ein Schritt).
2. Bild schicken, dann Folgenachricht `/clean` → Text entfernt (nutzt das gesendete Bild).
3. `/face <Name>` (Caption oder Folgenachricht) → Gesicht getauscht; unbekannter Name → Fehlermeldung.
4. `/recaption Oben | Unten` → Text entfernt + neuer Text drauf.
5. `/text` ohne Inhalt → Usage-Meldung. `/clean` ohne vorheriges Bild (Folgenachricht) → „zuerst Bild".
6. Cloud-Befehl auf Video → „kommt später"; `/text` auf Video → funktioniert.
7. Buttons funktionieren unverändert weiter.
8. `pytest` grün (neue `commands`-Tests + Bestand).

## Future

- Kombi-Befehl (Gesicht + Text in einem Befehl), falls gewünscht.
- Befehls-Autovervollständigung über die BotFather-Befehlsliste (`setMyCommands`).
