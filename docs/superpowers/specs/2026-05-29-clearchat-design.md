# Design: /clearchat — Chat aufräumen

## Context
Im Bot-Chat sammeln sich viele Nachrichten (Verarbeite-Hinweise, GIFs, Ergebnisse). Es soll
einen Befehl geben, der aufräumt. Telegram-Grenzen: Ein Bot kann im **privaten Chat** eigene
*und* Nutzer-Nachrichten löschen, aber nur **≤48h alt**; den Verlauf nicht auslesen. Da
Nachrichten-IDs fortlaufend sind, löschen wir die **letzten N per ID-Bereich** (stateless).
`/clean` ist belegt → neuer Name **`/clearchat`**.

## Scope
- `/clearchat` löscht die **letzten 100** Nachrichten (vom Befehl rückwärts), eigene + Nutzer,
  ≤48h. Einzeln löschen, Fehler ignorieren (zu alt / schon weg / Servicenachricht).
- Kurze Bestätigung „🧹 Aufgeräumt (N gelöscht).".
- Limit fix 100 (kein Config-Feld).
- Whitelist-Guard wie alle Befehle.

## Komponenten
- `bot/handlers.py`:
  - **`clearchat_ids(last_id: int, limit: int) -> list[int]`** — reine Funktion, berechnet die
    abzuarbeitenden IDs (vom letzten rückwärts, am Chat-Anfang bei 1 abgeschnitten). Unit-testbar.
  - **`on_clearchat`** — Handler: Whitelist; iteriert `clearchat_ids(msg.message_id, 100)`,
    `delete_message` je ID in try/except, zählt Erfolge, sendet Bestätigung.
  - HELP_TEXT um `/clearchat` ergänzen.
- `bot/app.py`: `CommandHandler("clearchat", handlers.on_clearchat)` registrieren.

## Testing
- `clearchat_ids(100,100) == [100..1]` (100 IDs); `clearchat_ids(5,100) == [5,4,3,2,1]`;
  `clearchat_ids(1000,50)` → 50 IDs, von 1000 bis 951.
- Handler via manuelles E2E.

## Verifikation (E2E)
1. Ein paar Nachrichten erzeugen → `/clearchat` → Chat ist (bis 48h/100) leer, Bestätigung bleibt.
2. Erneutes `/clearchat` holt ältere im Bereich nach.
3. `pytest` grün.
