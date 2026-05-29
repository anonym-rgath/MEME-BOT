# Design: GIPHY Teil A — GIF suchen & senden

## Context

Der Meme-Bot soll auf den großen GIF-/Meme-Fundus von GIPHY zugreifen. Teil A (dieser Spec)
deckt **GIF suchen & senden** ab: Befehle, die bei GIPHY suchen und ein passendes GIF in den
Chat schicken — als schneller Spaß und als Quelle für Vorlagen. (Teil B — GIFs beschriften —
ist ein separater, späterer Block.)

GIPHY bietet eine kostenlose API (Beta-Key, ~100 Aufrufe/Stunde, kein Geld). Das reicht für
einen privaten Bot locker. Gewünschtes Ergebnis: `/gif <Begriff>` schickt ein passendes GIF,
`/meme` ein zufälliges Meme-GIF.

## Scope (Teil A)

- ✅ `/gif <Begriff>` → ein passendes GIF (zufällig aus den Top-Treffern → Abwechslung).
- ✅ `/meme` → zufälliges Meme-GIF (GIPHY-Random, Tag „meme").
- ✅ Jugendschutz fix auf **pg-13** (kein NSFW).
- ✅ Ohne konfigurierten API-Key → freundliche Meldung (Bot startet trotzdem).
- ❌ GIFs beschriften / als Vorlage bearbeiten → Teil B.

## Komponenten

| Einheit | Aufgabe | Status |
|---|---|---|
| `config.py` | `giphy_api_key` (env `GIPHY_API_KEY`, Default ""/leer = nicht konfiguriert) | erweitern |
| `giphy/__init__.py` + `giphy/client.py` | `GiphyClient(api_key, fetch_json=…)` mit `search(term) -> str \| None` und `random_meme() -> str \| None`. Rein/testbar (HTTP über injizierbaren `fetch_json`). | **neu** |
| `bot/handlers.py` | `/gif <Begriff>` und `/meme` Handler; Key-fehlt-Meldung; HELP_TEXT erweitern | erweitern |
| `bot/app.py` | `GiphyClient` bauen + an `Handlers` injizieren; CommandHandler registrieren | erweitern |

### `GiphyClient`

- `search(term)`: ruft GIPHY Search (`/v1/gifs/search`, `q=term`, `limit=25`, `rating=pg-13`),
  wählt einen **zufälligen** Treffer, liefert dessen GIF-URL (`images.original.url` bzw.
  MP4-Variante). `None`, wenn keine Treffer.
- `random_meme()`: ruft GIPHY Random (`/v1/gifs/random`, `tag=meme`, `rating=pg-13`), liefert die
  GIF-URL. `None` bei Fehlern/leer.
- **HTTP:** Standard-`urllib` (keine neue Abhängigkeit). Für Tests wird `fetch_json(url, params)`
  injiziert (Default: echte urllib-Implementierung) → Unit-Tests ohne Netzwerk.
- **Randomness-Hinweis:** Die Zufallswahl darf `Math.random`-Äquivalente nutzen
  (`random.choice`); im Bot-Kontext unkritisch (kein Resume-Determinismus nötig).

## Datenfluss

1. `/gif <Begriff>` → `on_gif`: kein Key → Meldung; kein Begriff → Usage; sonst
   `client.search(term)` → URL → `ctx.bot.send_animation(chat_id, url)`; keine Treffer → „nichts
   gefunden".
2. `/meme` → `on_meme`: kein Key → Meldung; sonst `client.random_meme()` → `send_animation`.
3. GIPHY-Calls laufen synchron+schnell; zur Sicherheit (Event-Loop) in `asyncio.to_thread`.

## Fehlerbehandlung

- Kein `GIPHY_API_KEY` → „🎬 GIPHY ist nicht konfiguriert (API-Key fehlt)."
- `/gif` ohne Begriff → „Usage: /gif <Begriff>".
- Keine Treffer / GIPHY-Fehler → „🤷 Nichts gefunden, versuch's anders." (Exceptions abfangen.)

## Testing

- Unit-Tests `giphy/client.py` mit **gefaktem** `fetch_json` (kein Netzwerk):
  - `search` extrahiert eine URL aus einer Beispiel-GIPHY-Antwort.
  - `search` mit leerer `data`-Liste → `None`.
  - `random_meme` extrahiert die URL aus der Random-Antwort.
  - Übergebene Parameter enthalten `rating=pg-13` und den API-Key.
- Handler-/Wiring via manuelles E2E.

## Offene Punkte

- **GIPHY-API-Key** muss einmalig auf developers.giphy.com geholt und in die `.env` eingetragen werden.

## Verifikation (E2E)

1. `/gif katze` → ein Katzen-GIF kommt zurück; nochmal → (idealerweise) ein anderes.
2. `/meme` → ein zufälliges Meme-GIF.
3. `/gif` ohne Begriff → Usage-Meldung.
4. Ohne Key in der `.env` → „GIPHY nicht konfiguriert".
5. `pytest` grün (neue GiphyClient-Tests + Bestand).

## Future (Teil B)

- GIFs/Animationen als Eingabe-Medium akzeptieren und über die bestehende Text-Overlay-Pipeline
  beschriften (`send_animation` zurück). Verbindet sich mit Teil A (gesendetes GIF weiterleiten →
  betexten).
