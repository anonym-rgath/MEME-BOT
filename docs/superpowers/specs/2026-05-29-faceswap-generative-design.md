# Design: Face-Swap über generativen Editor (nano-banana)

## Context
`cdingram/face-swap` (inswapper) tauscht nur die innere Gesichtsregion in 128px und behält
Haare/Kopfform → altes Gesicht „scheint durch". Auf echten Fotos unbefriedigend. Umstieg auf einen
**generativen Multi-Bild-Editor** (`google/nano-banana`), der Zielbild + Gesicht + Anweisung
bekommt und das Bild **neu malt** → deutlich stärkere Identitätsübernahme.

## Scope
- **Bild-Face-Swap** nutzt künftig ein generatives Modell: `run(model, input={prompt, image_input:[ziel, gesicht]})`.
- Modell, Anweisung (Prompt) und der **Bilder-Feldname** sind **konfigurierbar** (Default
  `google/nano-banana` / `image_input`), damit Modellwechsel ohne Code gehen.
- Video-Face-Swap bleibt unverändert (weiter gated-off; alter inswapper-Pfad bleibt für später).
- Bot-Flow/Handlers **unverändert** (`swap_image(target, face)` bleibt die Schnittstelle).

## Trade-off (bewusst)
Generatives Editieren malt das Bild neu → Pose/Hintergrund können leicht abweichen; dafür ist das
alte Gesicht wirklich weg. ~4 ¢/Bild. Akzeptiert vom Nutzer.

## Komponenten
- `config.py`:
  - `image_model` Default → `google/nano-banana`.
  - neu `faceswap_prompt` (env `FACESWAP_PROMPT`) — Anweisung.
  - neu `faceswap_images_key` (env `FACESWAP_IMAGES_KEY`, Default `image_input`).
- `faceswap/provider.py`: `ReplicateProvider(client, image_model, video_model, faceswap_prompt, images_key="image_input")`.
  - `swap_image(target, face)` → `input={"prompt": prompt, images_key: [target, face]}` → `first_url`.
  - `swap_video` unverändert (alter `input_image`/`swap_image`-Pfad, gated off).
- `bot/app.py`: Provider mit `faceswap_prompt` + `images_key` aus Settings bauen.

## Prompt (Default)
„Replace the face of the person in the first image with the face of the person in the second
image. Keep the first image's pose, body, clothing, lighting, background and style unchanged.
Make it look natural and photorealistic."

## Testing
- `swap_image` sendet `prompt` + Bilder-Array (2 Einträge) ans richtige Modell; `images_key`
  konfigurierbar; List-Output → erstes Element. `swap_video` weiterhin `input_image`/`swap_image`.
- Config-Defaults/Overrides der neuen Felder.
- Bestehende faceswap-Tests auf neuen Konstruktor (faceswap_prompt) anpassen.

## Verifikation (E2E)
1. Echtes Foto + gespeichertes Gesicht → 🔁 Gesicht tauschen → altes Gesicht ersetzt, neue Identität klar.
2. Log: `predictions 201`.
3. Falls Replicate 422 „image_input"/Feldname meckert → `FACESWAP_IMAGES_KEY` in `.env` anpassen (kein Code).
4. `pytest` grün.

## Future
- Video-Face-Swap auf ein generatives/Video-fähiges Modell umstellen (separat).
