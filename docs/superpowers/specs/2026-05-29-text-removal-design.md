# Design: KI-Textentfernung (Text-Removal)

## Context

Der Meme-Bot kann bereits Text *hinzufügen* (Bild + Video) und Gesichter tauschen (Bild).
Neuer Wunsch: **Text aus Bildern entfernen** — zwei Anwendungsfälle, die technisch dieselbe
Operation sind:
- Eine vorhandene Meme-Vorlage **säubern** (eingebrannten Text wegretuschieren).
- Beliebigen Text/Wasserzeichen aus Fotos entfernen.

(Der dritte ursprünglich genannte Fall „meinen gerade gesetzten Text zurücknehmen" braucht
**keinen Code** — der Bot zerstört das Original nie, der Nutzer behält es. YAGNI.)

Technisch ist Entfernen schwerer als Hinzufügen: man muss Textbereiche erkennen und die Stelle
plausibel **auffüllen (Inpainting)**. Wie beim Face-Swap übernimmt das die **Cloud (Replicate)**,
weil der Pi dafür zu schwach ist. Erwünschtes Ergebnis: Nutzer schickt ein Bild, wählt per Button
„Text entfernen" (oder „Vorlage neu betexten"), und bekommt das bereinigte (ggf. neu betextete)
Bild zurück.

## Scope (v1)

- ✅ **Text entfernen** (`clean`): Bild → bereinigtes Bild.
- ✅ **Vorlage neu betexten** (`recaption`): Bild → Text entfernen → neuen Ober-/Untertext drauf.
- ✅ **Nur Bilder.** Video-Textentfernung wird — wie Video-Face-Swap — abgelehnt („kommt später");
  der Provider wird so gebaut, dass Video später ein kleiner Handgriff ist.
- 🔒 Cloud-Aktion → nur für Whitelist-Nutzer (besteht bereits), kostet pro Bild.
- 🧹 Temp-Dateien werden nach dem Senden gelöscht (bestehendes Verhalten).

## Komponenten (folgt dem Face-Swap-Muster)

| Einheit | Aufgabe | Status |
|---|---|---|
| `textremove/provider.py` | `TextRemovalProvider`-Protocol + `ReplicateTextRemover` mit Methode `remove_text(image_path) -> str` (Ergebnis-URL). Kapselt die Cloud-Logik. | **neu** |
| `config.py` | Neues Feld `text_removal_model` (env `REPLICATE_TEXT_REMOVAL_MODEL`) + ggf. `text_detect_model` (nur falls 2-Stufen-Pipeline nötig) | erweitern |
| `bot/keyboards.py` | Zwei neue Buttons: `action:clean`, `action:recaption` | erweitern |
| `bot/state.py` | `action` erhält Werte `"clean"` / `"recaption"` (keine neuen Felder nötig) | erweitern |
| `bot/handlers.py` | Neue Actions; Video-Guard erweitern; Pipeline um eine **Text-entfernen-Stufe** ergänzen | erweitern |
| `bot/app.py` | `ReplicateTextRemover` bauen und in `Handlers` injizieren | erweitern |

### Provider-Schnittstelle (versteckt die Implementierungswahl)

```
class TextRemovalProvider(Protocol):
    def remove_text(self, image_path: str) -> str: ...   # gibt Ergebnis-URL zurück
```

`ReplicateTextRemover` implementiert das. **Offene Implementierungsentscheidung** (beim
Modell-Verifikationsschritt zu klären, ändert NICHT die Bot-Logik):
- **Variante 1 — Ende-zu-Ende-Modell:** ein Replicate-„Scene-Text-Removal"-Modell, das Text selbst
  erkennt und entfernt (kein Masken-Input). Bevorzugt, weil 1 Call, einfacher, günstiger.
- **Variante 2 — 2-Stufen-Pipeline:** Texterkennung (OCR/Detection) → Maske → Inpaint-Modell.
  Fallback, falls kein brauchbares Ende-zu-Ende-Modell verfügbar ist. Mehr Calls/Kosten.

Beide liegen vollständig hinter `remove_text()`; der Rest des Bots bleibt unberührt.

## Datenfluss

- **`clean`:** Bild empfangen → Buttons → „🧹 Text entfernen" → `remove_text` (Cloud) →
  Ergebnis herunterladen → senden.
- **`recaption`:** Bild → „🆕 Vorlage neu betexten" → `remove_text` (Cloud) → Ober-/Untertext
  abfragen (bestehender Text-Flow) → Text-Overlay (lokal, `add_text_to_image`) → senden.
- Pipeline-Reihenfolge in `_process_and_send`: **erst Text-Removal**, dann optional Text-Overlay.
- Alle Zwischen-/Temp-Dateien werden im `finally`-Block gelöscht (bestehendes Muster).

## Button-/Action-Logik

Erweiterte Action-Tastatur (nach Bild-Upload): bestehende Buttons + **🧹 Text entfernen**
(`action:clean`) + **🆕 Vorlage neu betexten** (`action:recaption`).

- `on_button`, `action:clean` → Pipeline sofort starten (`sess.action="clean"`).
- `on_button`, `action:recaption` → `sess.action="recaption"`, dann Ober-/Untertext abfragen
  (`awaiting="top_text"`, wie bei `text`/`both`); nach `bottom_text` → Pipeline.
- **Video-Guard erweitern:** `if sess.is_video and sess.action in ("face","both","clean","recaption")`
  → freundlich ablehnen („Cloud-Bearbeitung für Videos kommt später").

Pipeline-Bedingungen in `_process_and_send`:
- Text-Removal-Stufe läuft, wenn `sess.action in ("clean","recaption")`.
- Text-Overlay-Stufe läuft, wenn `sess.action in ("text","both","recaption")` und Text vorhanden.
- Face-Swap-Stufe unverändert (`sess.action in ("face","both")`).

## Fehlerbehandlung & Kosten

- Provider-Fehler/Timeouts → bestehende `except`-Logik zeigt „⚠️ Fehler: …".
- Replicate-Call kostet pro Bild (Variante 2 entsprechend mehr) — vor dem Lauf ist die Whitelist
  der Kostenschutz; ein Hinweis-Text im „Verarbeite…"-Schritt ist optional.
- `remove_text` gibt immer eine URL zurück; Download wird (wie beim Face-Swap) in
  `asyncio.to_thread` ausgelagert, um den Event-Loop nicht zu blockieren.

## Testing

- Unit-Test `textremove/provider.py` mit **gemocktem** Replicate-Client (kein Netzwerk), analog
  zu `tests/test_faceswap.py`: prüft Modell-Slug, Eingabe-Keys, URL-Normalisierung.
- Config-Test: `text_removal_model` wird aus env geladen / hat Default.
- Handler-Flow via manuelles E2E (wie gehabt).

## Offene Punkte (vor/bei Implementierung)

- **Modell-Verifikation:** konkretes Replicate-Modell + Eingabe-Feldnamen bestätigen; entscheiden
  zwischen Variante 1 (Ende-zu-Ende) und Variante 2 (Pipeline). Slug(s) in `.env` konfigurierbar.
- **Replicate-Token** muss echt sein (nicht Platzhalter) und Billing aktiv.

## Verifikation (E2E)

1. Bild mit eingebranntem Text schicken → „🧹 Text entfernen" → Text ist im Ergebnis weg.
2. Bild → „🆕 Vorlage neu betexten" → Text weg **und** neuer Ober-/Untertext drauf.
3. Video → „🧹 Text entfernen" → freundliche Ablehnung, kein Replicate-Call.
4. Temp-Verzeichnis: nach den Läufen keine Streureste (nur gespeicherte Gesichter bleiben).
5. `pytest` grün (neuer Provider-Test + Config-Test).
6. Auf dem Pi via Docker deployt, vom Handy nutzbar.

## Future

- Video-Textentfernung (Provider-Methode `remove_text_video` + Guard entfernen), analog zur
  Video-Face-Swap-Erweiterung. Deutlich teurer pro Job.
- Optional: „säubern + Gesicht tauschen + Text" kombiniert (aktuell nicht im Scope).
