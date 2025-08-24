# Contributing to Follow-Fellow

Wir freuen uns über Beiträge zu Follow-Fellow! Diese Anleitung hilft Ihnen dabei, einen erfolgreichen Beitrag zu leisten.

## 🚀 Quick Start

1. **Fork** das Repository
2. **Clone** Ihren Fork
3. **Erstellen** Sie einen Feature-Branch
4. **Machen** Sie Ihre Änderungen
5. **Testen** Sie Ihre Änderungen
6. **Committen** und **Pushen** Sie
7. **Erstellen** Sie einen Pull Request

## 🔧 Development Setup

```bash
# Repository klonen
git clone https://github.com/IHR-USERNAME/follow-fellow.git
cd follow-fellow

# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Tests ausführen
pytest

# Web-Interface starten
python follow_fellow.py --web
```

## 🧪 Testing

Bevor Sie einen Pull Request erstellen, stellen Sie sicher, dass:

1. **Alle Tests bestehen**:
   ```bash
   pytest
   ```

2. **Code Coverage akzeptabel ist** (>60%):
   ```bash
   pytest --cov=follow_fellow --cov-report=term
   ```

3. **Neue Features getestet sind**:
   - Fügen Sie Tests für neue Funktionalität hinzu
   - Siehe `test_follow_fellow.py` für Beispiele

4. **Interaktiver Test Runner funktioniert**:
   ```bash
   python run_tests.py
   ```

## 📝 Code Style

- **Python PEP 8** Konventionen befolgen
- **Docstrings** für alle öffentlichen Methoden
- **Type Hints** wo möglich verwenden
- **Deutsche Kommentare** für Konsistenz mit dem Projekt

## 🐛 Bug Reports

Wenn Sie einen Bug finden:

1. **Prüfen Sie**, ob der Bug bereits gemeldet wurde
2. **Erstellen Sie ein Issue** mit:
   - Detaillierter Beschreibung des Problems
   - Schritten zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - System-Informationen (OS, Python-Version)
   - Relevante Logs oder Screenshots

## ✨ Feature Requests

Für neue Features:

1. **Diskutieren Sie** die Idee in einem Issue
2. **Beschreiben Sie**:
   - Das Problem, das gelöst werden soll
   - Ihre vorgeschlagene Lösung
   - Mögliche Alternativen
   - Zusätzlicher Kontext

## 📋 Pull Request Guidelines

### Bevor Sie einen PR erstellen:

- [ ] Branch ist auf dem neuesten Stand mit `main`
- [ ] Alle Tests bestehen
- [ ] Code Coverage ist nicht gesunken
- [ ] Neue Features sind getestet
- [ ] README.md ist aktualisiert (falls nötig)
- [ ] TESTING.md ist aktualisiert (falls nötig)

### PR-Titel Format:

```
[Type] Kurze Beschreibung

Beispiele:
[Feature] Add cache statistics endpoint
[Fix] Resolve retry mechanism timeout issue
[Docs] Update testing documentation
[Test] Add integration tests for Flask routes
```

### PR-Beschreibung:

```markdown
## Beschreibung
Kurze Beschreibung der Änderungen

## Typ der Änderung
- [ ] Bug Fix
- [ ] Neue Funktion
- [ ] Breaking Change
- [ ] Dokumentation
- [ ] Tests

## Wie wurde getestet?
- [ ] Bestehende Tests bestehen
- [ ] Neue Tests hinzugefügt
- [ ] Manuell getestet

## Checklist:
- [ ] Code folgt dem Style Guide
- [ ] Selbst-Review durchgeführt
- [ ] Dokumentation aktualisiert
- [ ] Tests hinzugefügt/aktualisiert
```

## 🏗️ Projektstruktur

```
follow-fellow/
├── follow_fellow.py      # Hauptanwendung
├── test_follow_fellow.py # Umfassende Tests
├── run_tests.py          # Interaktiver Test Runner
├── requirements.txt      # Python Dependencies
├── pyproject.toml        # pytest Konfiguration
├── README.md             # Projekt-Dokumentation
├── TESTING.md            # Test-Dokumentation
├── CONTRIBUTING.md       # Diese Datei
├── LICENSE               # MIT Lizenz
├── RATING.md             # Repository-Bewertung
├── .env.example          # Umgebungsvariablen-Template
├── .gitignore            # Git Ignore-Regeln
└── .cache/               # API-Cache (ignoriert)
```

## 🔑 Environment Variables

Für die Entwicklung benötigen Sie:

```bash
# .env Datei erstellen
cp .env.example .env

# Notwendige Variablen setzen
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_username
```

## 🆘 Hilfe benötigt?

- **Dokumentation**: Siehe [README.md](README.md) und [TESTING.md](TESTING.md)
- **Issues**: Durchsuchen Sie bestehende Issues
- **Diskussionen**: Starten Sie eine Diskussion für größere Änderungen

## 🙏 Danke!

Vielen Dank für Ihren Beitrag zu Follow-Fellow! Jeder Beitrag, egal wie klein, wird geschätzt.

---

**Happy Coding! 🚀**
