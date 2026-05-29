# Design: GIPHY Teil B — GIFs beschriften

## Context
Teil A liefert GIFs (`/gif`, `/meme`). Teil B macht GIFs **bearbeitbar**: ein an den Bot
gesendetes/weitergeleitetes GIF (Telegram `animation`) durchläuft die **bestehende
Text-Overlay-Pipeline** und kommt betextet zurück. So wird aus „GIF holen" echtes „Meme machen".

## Scope (v1)
- `on_media` akzeptiert zusätzlich **`msg.animation`** (GIFs; Telegram liefert sie als `.mp4`).
- Behandlung wie Video (`is_video=True`) → **ffmpeg-Text-Overlay** (`add_text_to_video`) legt Text drauf.
- Neues Flag **`is_animation`** → Ergebnis wird per **`send_animation`** (loopendes GIF) zurückgeschickt.
- Cloud-Aktionen (Gesicht tauschen / Text entfernen) auf GIFs → **abgelehnt** wie bei Video (Guard greift über `is_video`). v1 = **GIF + Text**.
- Längen-Limit `max_video_seconds` gilt auch für GIFs.

## Komponenten
- `bot/state.py`: Feld `is_animation: bool = False`.
- `bot/handlers.py`:
  - `on_media`: neuer Zweig `elif msg.animation:` → Datei nach `.mp4`, `is_video=True`,
    `is_animation=True`, Längen-Guard. In Foto-/Video-Zweig `is_animation=False` setzen (kein Stale).
  - `_process_and_send` Ergebnis-Versand: `if sess.is_animation: send_animation` →
    `elif sess.is_video: send_video` → `else: send_photo`.
- `bot/app.py`: Medien-Filter `filters.PHOTO | filters.VIDEO | filters.ANIMATION`.

## Datenfluss
GIF an Bot (weitergeleitet/gesendet) → `on_media` lädt `.mp4`, `is_video/is_animation=True` →
Buttons/Caption/Folgebefehl → bei Text: `add_text_to_video` → Ergebnis via `send_animation`.
Cloud-Aktion auf GIF → freundliche „kommt später"-Ablehnung. Temp-Cleanup wie gehabt.

## Testing
- `state`-Feld trivial. Renderer/ffmpeg-Overlay bereits getestet. Handler/Telegram-Versand via
  manuelles E2E.

## Verifikation (E2E)
1. `/gif katze` → ein GIF weiterleiten an den Bot → 📝 Text hinzufügen → betextetes GIF (loopt).
2. Beliebiges GIF mit Caption `/text Oben | Unten` → betextetes GIF in einem Schritt.
3. GIF → 🧹/🔁 (Cloud) → „kommt später"-Ablehnung.
4. `pytest` grün; Import-Check ok.

## Future
- Cloud-Bearbeitung (Face-Swap / Text entfernen) auf GIFs, analog zur Video-Erweiterung (teuer).
