# MEME-BOT — ToDo

Backlog / nächste Schritte. Erledigtes abhaken, Neues unten anhängen.

## 🔒 Security prüfen
- [ ] **GitHub absichern**
  - [ ] prüfen, dass keine Secrets im Verlauf/Repo liegen (`.env` & `data/` sind gitignored ✓)
  - [ ] Branch-Schutz / Dependabot / Secret-Scanning aktivieren
  - [ ] Bot-Token rotieren, falls er je im Klartext geteilt wurde
- [ ] **Claude einen Security-Review machen lassen**
  - [ ] Token-Handling, Whitelist-Robustheit, Input-Validierung
  - [ ] Prompt-Injection über Bild-Captions / Texte an Replicate-Modelle
  - [ ] Dateigrößen-/Längen-Limits, Fehlerpfade, Rate-Limiting
  - [ ] Abhängigkeiten (pip) auf bekannte CVEs prüfen

## 🧪 Funktionen testen (offene E2E)
- [ ] **Face-Swap (nano-banana)** am Pi: in `.env` `REPLICATE_IMAGE_MODEL=google/nano-banana` setzen → `./scripts/redeploy.sh` → echtes Foto → 🔁
- [ ] **GIF-Flow**: `/gif`, `/meme`, GIF an Bot weiterleiten + betexten
- [ ] Alle Befehle einmal durch (Ablaufplan in der Chat-Historie)
- [ ] Whitelist (fremder Account abgewiesen), `/clearchat`, Video-Ablehnung bei Cloud-Aktionen

## ✨ Funktionen erweitern
- [ ] Ideen sammeln. Kandidaten:
  - [ ] Video-Face-Swap aktivieren (Provider vorbereitet, Guard entfernen)
  - [ ] Claude-Captions (Sprüche/Vorschläge generieren)
  - [ ] Mehrere Gesichter / Gesicht direkt aus Foto wählen
  - [ ] Ergebnis als Sticker / Format-Optionen

## 🎛️ Funktionen & Commands vereinfachen (aktuell zu „schwer")
- [ ] Bedienung verschlanken — weniger Schritte, klarere Buttons
- [ ] **„Befehl → Bild"-Reihenfolge fixen** (gemerkter Befehl: erst `/clean`, dann Bild) — bereits gebrainstormt/geparkt
- [ ] ggf. natürlichere Eingabe (weniger Syntax, mehr Buttons/Defaults)

## 🏗️ Architektur prüfen & verbessern
- [ ] Integration-/Handler-Tests ergänzen (aktuell nur via E2E)
- [ ] Refactor wo Dateien wachsen (z. B. `handlers.py`)
- [ ] Cloud-Migration (geparkt) neu bewerten
- [ ] Modell-/Kosten-Monitoring (Replicate-Ausgaben im Blick)

## 📌 Sonstiges
- [ ] (frei für Neues)

---
_Status-Snapshot: gebaut & gepusht — Text (Bild/Video/GIF), Face-Swap (nano-banana), Text entfernen (flux-kontext), Befehle + Menü + Beschreibungen, GIPHY (/gif, /meme, GIF betexten), /clearchat, Deploy-Skripte. Specs/Pläne unter `docs/superpowers/`._
