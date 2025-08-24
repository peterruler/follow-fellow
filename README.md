# 🐙 Follow-Fellow

Ein Python-Script mit Flask Web-Interface zur Verwaltung von GitHub-Follows. Das Tool analysiert Ihre GitHub-Follower und die Personen, denen Sie folgen, und kann automatisch einseitige Follows entfernen.

## ✨ Features

- 📊 **Analyse von GitHub-Follows**: Vergleicht Follower mit Following
- 🔍 **Einseitige Follows erkennen**: Zeigt Benutzer, die nicht zurückfolgen
- 🧹 **Automatisches Cleanup**: Entfernt einseitige Follows automatisch
- 🛡️ **Dry-Run Modus**: Simulation ohne tatsächliche Änderungen
- 🌐 **Web-Interface**: Benutzerfreundliche Web-Oberfläche
- 💻 **CLI-Interface**: Kommandozeilen-Tool für Automatisierung
- ⚡ **Rate Limiting**: Respektiert GitHub API-Limits
- 📋 **Detaillierte Reports**: Umfassende Analyse-Berichte

## 🚀 Installation

1. **Repository klonen**:
   ```bash
   git clone <repository-url>
   cd follow-fellow
   ```

2. **Python Virtual Environment erstellen**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Dependencies installieren**:
   ```bash
   pip install flask requests python-dotenv click
   ```

4. **GitHub Personal Access Token erstellen**:
   - Gehen Sie zu [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Erstellen Sie einen neuen Token mit folgenden Scopes:
     - `user:follow` (zum Folgen/Entfolgen)
     - `read:user` (zum Lesen von Benutzerdaten)

5. **Umgebungsvariablen konfigurieren**:
   ```bash
   cp .env.example .env
   # Bearbeiten Sie .env und fügen Sie Ihren GitHub Token hinzu
   ```

## 📖 Verwendung

### Web-Interface

Starten Sie das Web-Interface:

```bash
python follow_fellow.py --web
```

Öffnen Sie http://localhost:5000 in Ihrem Browser.

**Web-Interface Features**:
- 📊 Interaktive Analyse-Dashboard
- 👥 Detaillierte Benutzerprofile für einseitige Follows
- 🧹 Dry-Run und Cleanup-Funktionen
- 📈 Statistiken und Visualisierungen

### Command Line Interface

**Einfache Analyse**:
```bash
python follow_fellow.py
```

**Dry-Run (Simulation)**:
```bash
python follow_fellow.py --dry-run
```

**Cleanup durchführen**:
```bash
python follow_fellow.py  # ohne --dry-run Flag
```

**Andere Optionen**:
```bash
# Anderen Benutzer analysieren
python follow_fellow.py --username andererbenutzername

# Token direkt angeben
python follow_fellow.py --token ghp_xxxxxxxxxxxx

# Web-Interface auf anderem Port
python follow_fellow.py --web --port 8080
```

## 🛠️ Konfiguration

### Umgebungsvariablen (.env)

```env
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_USERNAME=peterruler
FLASK_ENV=development
FLASK_DEBUG=true
```

### GitHub Token Berechtigungen

Ihr GitHub Personal Access Token benötigt folgende Scopes:
- `user:follow` - Zum Folgen und Entfolgen von Benutzern
- `read:user` - Zum Lesen von Benutzerprofilen und Listen

## 📊 Ausgabe-Beispiel

```
🐙 Follow-Fellow für peterruler
==================================================
📥 Lade Follower von peterruler...
✅ 150 Follower gefunden
📤 Lade Following von peterruler...
✅ 180 Following gefunden

📈 ZUSAMMENFASSUNG
==============================
👥 Follower: 150
📤 Following: 180
🤝 Gegenseitig: 145
➡️  Einseitig: 35

🔍 EINSEITIGE FOLLOWS (35)
========================================
peterruler folgt diesen Benutzern, aber sie folgen nicht zurück:
  • user1 (Max Mustermann) - 1200 Follower
  • user2 (Jane Doe) - 850 Follower
  • user3 - 300 Follower

🔍 DRY RUN MODUS
====================
Würde 35 Benutzer entfolgen:
  • Würde user1 entfolgen
  • Würde user2 entfolgen
  • Würde user3 entfolgen
```

## ⚠️ Wichtige Hinweise

- **Rate Limits**: Das Script respektiert GitHubs Rate Limits (5000 Requests/Stunde)
- **Backup**: Führen Sie zuerst immer einen Dry-Run durch
- **Token Sicherheit**: Teilen Sie niemals Ihren GitHub Token
- **Vorsicht**: Einseitige Follows können strategisch wertvoll sein

## 🤝 Beitragen

1. Fork des Repositories
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE` Datei für Details.

## 🆘 Support

Bei Problemen oder Fragen:
1. Prüfen Sie die GitHub API-Dokumentation
2. Stellen Sie sicher, dass Ihr Token gültig ist
3. Prüfen Sie Ihre Internetverbindung
4. Erstellen Sie ein Issue in diesem Repository

## 🧪 Tests

Das Projekt verfügt über umfassende Tests mit pytest. Weitere Details in [TESTING.md](TESTING.md).

### Tests ausführen

**Alle Tests:**
```bash
pytest
```

**Mit Coverage-Report:**
```bash
pytest --cov=follow_fellow --cov-report=html
```

**Spezifische Tests:**
```bash
# Nur Unit-Tests
pytest test_follow_fellow.py::TestGitHubFollowManager

# Nur API-Tests  
pytest test_follow_fellow.py::TestFlaskApp

# Mit Details
pytest -v

# Bis zum ersten Fehler
pytest -x
```

### Test-Dependencies installieren

```bash
pip install pytest pytest-cov pytest-mock
```

### Coverage-Ziele

- ✅ Gesamt-Coverage: > 90%
- ✅ GitHubFollowManager: > 95%
- ✅ FollowAnalyzer: > 95%
- ✅ Flask API: 100%

Siehe [TESTING.md](TESTING.md) für detaillierte Test-Dokumentation.

## 🔧 Entwicklung

Für lokale Entwicklung:

```bash
# Development Server mit Debug-Modus
python follow_fellow.py --web

# Tests ausführen
pytest

# Tests mit Coverage
pytest --cov=follow_fellow --cov-report=html

# Code-Stil prüfen
flake8 follow_fellow.py

# Alle Tests in Überwachungsmodus
pytest --cov=follow_fellow --cov-report=term-missing -v
```

## 📈 Zukünftige Features

- 📱 Mobile-responsive Web-Interface
- 📊 Erweiterte Statistiken und Visualisierungen
- 🔄 Automatische Synchronisation
- 📧 E-Mail-Berichte
- 🔍 Erweiterte Filter-Optionen
- 💾 Datenbank-Integration für historische Daten

## 🤝 Contributing

Beiträge sind willkommen! Bitte lesen Sie unsere [TESTING.md](./TESTING.md) für Entwicklungsrichtlinien.

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Pushen Sie zum Branch (`git push origin feature/AmazingFeature`)
5. Öffnen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe die [LICENSE](LICENSE) Datei für Details.

## 👨‍💻 Autor

**Peter Ströβler** ([@peterruler](https://github.com/peterruler))

- GitHub: [@peterruler](https://github.com/peterruler)
- Repository: [follow-fellow](https://github.com/peterruler/follow-fellow)

## 🙏 Danksagungen

- Danke an die GitHub API für die umfassenden Endpunkte
- Inspiriert von der Notwendigkeit, GitHub-Follows effizient zu verwalten
- Community-Feedback für kontinuierliche Verbesserungen

---

**Viel Spaß beim Verwalten Ihrer GitHub-Follows! 🚀**
