# Design: /gif schickt mehrere GIFs aus engerem Topf

## Context
`/gif <Begriff>` schickt aktuell **ein** zufälliges GIF aus den Top 25. Wunsch: **mehrere zur
Auswahl** (Default 3) und aus einem **engeren, relevanteren Topf** (Top 15 statt 25). `/meme`
bleibt unverändert (eins).

## Scope
- `GiphyClient.search(term, count=3) -> list[str]`: holt Top **15** (rating pg-13), zieht **bis zu
  `count` zufällige, verschiedene** Treffer, gibt deren URLs zurück (leere Liste = nichts gefunden).
- `/gif <Begriff>` sendet die (bis zu 3) GIFs nacheinander via `send_animation` (Telegram-Alben
  funktionieren für animierte GIFs nicht zuverlässig → einzelne Nachrichten).
- Anzahl konfigurierbar: `giphy_result_count` (env `GIPHY_RESULT_COUNT`, Default 3).
- `/meme` unverändert (eins).

## Komponenten
- `config.py`: neues Feld `giphy_result_count: int = 3`.
- `giphy/client.py`: `search` gibt jetzt eine **Liste** zurück (engerer Pool + Stichprobe via
  `random.sample`). `random_meme` unverändert.
- `bot/handlers.py`: `on_gif` ruft `search(term, self.s.giphy_result_count)` und sendet jede URL.

## Breaking change (intern)
`search` liefert künftig `list[str]` statt `str | None`. Betrifft nur den internen Aufrufer
(`on_gif`) und die GiphyClient-Tests — beide werden angepasst.

## Testing
- `search` mit einem Treffer → `["url"]`; leer → `[]`; viele Treffer → genau `count` **verschiedene**.
- Param `rating=pg-13`, `api_key`, `q` weiterhin gesetzt; `limit=15`.
- Config: `giphy_result_count` Default 3 + env-Override.
- `on_gif`: via manuelles E2E.

## Verifikation (E2E)
1. `/gif katze` → 3 (verschiedene) Katzen-GIFs.
2. Wenige Treffer (seltener Begriff) → entsprechend weniger, kein Fehler.
3. `GIPHY_RESULT_COUNT=1` → wieder nur eins.
4. `pytest` grün.
