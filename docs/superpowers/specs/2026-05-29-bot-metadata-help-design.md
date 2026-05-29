# Design: Bot-Metadaten & Hilfe (Befehlsmenü, Beschreibungen, /help)

## Context
Die Befehle sollen klar dokumentiert sein und beim Start als natives **Telegram-Befehlsmenü**
(Autovervollständigung + ☰) erscheinen. Zusätzlich braucht der Bot eine **Profil-Kurzbeschreibung**
und eine **Beschreibung** (leerer Chat, „Was kann dieser Bot?"). Alles wird per API beim Start
gesetzt → im Code versioniert, kein manuelles BotFather-Klicken.

## Scope
- **`set_my_commands`**: registriert die Befehlsliste mit Kurzbeschreibungen (ohne `/skip`).
- **`set_my_short_description`**: ≤120 Zeichen, Profilseite.
- **`set_my_description`**: ≤512 Zeichen, leerer Chat vor dem Start.
- **Neuer `HELP_TEXT`**: aufgeräumt/gruppiert; von `/help` und `/start` genutzt.
- Gesetzt in einem **`post_init`-Hook** der `Application`.

## Komponenten
- `bot/handlers.py`: `HELP_TEXT` neu (gruppiert: Bearbeiten / GIFs / Sonstiges + Tipp).
- `bot/app.py`:
  - Konstanten `BOT_COMMANDS` (Liste `BotCommand`), `SHORT_DESCRIPTION`, `DESCRIPTION`.
  - `async def _post_init(app)` → `bot.set_my_commands(BOT_COMMANDS)`,
    `bot.set_my_short_description(SHORT_DESCRIPTION)`, `bot.set_my_description(DESCRIPTION)`.
  - `Application.builder().token(...).post_init(_post_init).build()`.
  - Import `BotCommand` von `telegram`.

## Inhalte
- Menü: start, help, text, face, clean, recaption, gif, meme, clearchat (siehe Wortlaut im Code).
- Kurzbeschreibung: „Meme-Werkstatt: Text auf Bild/Video/GIF, Gesicht tauschen, Text entfernen, GIFs suchen."
- Beschreibung: freundlicher Mehrzeiler mit den 4 Funktionen + Tipp auf /start.

## Fehlerbehandlung
- `set_my_*`-Aufrufe im `post_init` in try/except kapseln + warnen, damit ein Telegram-Hiccup den
  Bot-Start nicht verhindert (Befehle/Beschreibung sind nice-to-have, kein Muss zum Laufen).

## Testing
- Reiner Telegram-Metadaten-Pfad → via Import-Check + manuelles E2E (Menü/Beschreibung im Client
  sichtbar). HELP_TEXT-Inhalt unkritisch.

## Verifikation (E2E)
1. Bot neu starten → in Telegram „/" tippen → Befehlsliste mit Beschreibungen erscheint; ☰-Button da.
2. Bot-Profil → Kurzbeschreibung sichtbar.
3. Neuer/leerer Chat → Beschreibung unter „Was kann dieser Bot?".
4. `/help` und `/start` → neuer, gruppierter Text.
5. Import-Check + `pytest` grün.
