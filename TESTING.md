# 🧪 Testing Documentation - Follow-Fellow

Diese Dokumentation beschreibt das Test-Setup und die verfügbaren Tests für das Follow-Fellow Projekt.

## 📋 Übersicht

Das Projekt verwendet **pytest** als Test-Framework und bietet umfassende Unit-Tests, Integrationstests und API-Tests.

### Test-Struktur

```
follow-fellow/
├── test_follow_fellow.py          # Haupttest-Datei
├── pyproject.toml                 # Pytest-Konfiguration
├── requirements.txt               # Inkl. Test-Dependencies
└── README.md                      # Diese Dokumentation
```

## 🚀 Quick Start

### 1. Test-Dependencies installieren

```bash
pip install pytest pytest-cov pytest-mock
```

Oder aus requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Tests ausführen

**Alle Tests ausführen:**
```bash
pytest
```

**Mit Coverage-Report:**
```bash
pytest --cov=follow_fellow --cov-report=html
```

**Nur bestimmte Test-Klassen:**
```bash
pytest test_follow_fellow.py::TestGitHubFollowManager
```

**Verbose Output:**
```bash
pytest -v
```

## 📊 Test-Kategorien

### Unit Tests
- **TestGitHubFollowManager**: Tests für die Hauptklasse
- **TestFollowAnalyzer**: Tests für die Analyse-Funktionen
- **TestFlaskApp**: Tests für die Web-API

### Integration Tests
- **TestIntegration**: End-to-End Tests

### Parametrisierte Tests
- Tests mit verschiedenen Eingabe-Szenarien
- Abdeckung von Edge-Cases

## 🔧 Test-Konfiguration

### pytest.ini Optionen

```toml
[tool.pytest.ini_options]
testpaths = [".", "tests"]
addopts = [
    "--verbose",
    "--tb=short",
    "--strict-markers",
    "--disable-warnings",
    "--color=yes"
]
```

### Coverage-Konfiguration

```toml
[tool.coverage.run]
source = ["follow_fellow"]
omit = [
    "test_*.py",
    "*_test.py",
    "*/tests/*"
]
```

## 🏃‍♂️ Test-Befehle

### Basis-Befehle

```bash
# Alle Tests ausführen
pytest

# Tests mit Coverage
pytest --cov=follow_fellow

# HTML Coverage Report
pytest --cov=follow_fellow --cov-report=html

# Tests mit Details
pytest -v -s

# Nur fehlgeschlagene Tests
pytest --lf

# Tests bis zum ersten Fehler
pytest -x
```

### Spezifische Tests

```bash
# Einzelne Test-Datei
pytest test_follow_fellow.py

# Einzelne Test-Klasse
pytest test_follow_fellow.py::TestGitHubFollowManager

# Einzelne Test-Methode
pytest test_follow_fellow.py::TestGitHubFollowManager::test_init

# Tests mit Pattern
pytest -k "test_api"

# Tests nach Marker
pytest -m "unit"
```

### Performance Tests

```bash
# Zeitmessung für Tests
pytest --durations=10

# Langsame Tests ausschließen
pytest -m "not slow"

# Parallel ausführen (mit pytest-xdist)
pytest -n auto
```

## 📈 Coverage Reports

### HTML Report erstellen

```bash
pytest --cov=follow_fellow --cov-report=html
open htmlcov/index.html  # macOS
```

### Terminal Report

```bash
pytest --cov=follow_fellow --cov-report=term-missing
```

### Coverage-Ziele

- **Gesamt-Coverage**: > 90%
- **Kritische Module**: > 95%
- **API-Endpunkte**: 100%

## 🧪 Test-Arten im Detail

### 1. GitHubFollowManager Tests

```python
class TestGitHubFollowManager:
    def test_init(self):                    # Initialisierung
    def test_make_request_success(self):    # API-Requests
    def test_get_followers(self):           # Follower-Abruf
    def test_unfollow_user_success(self):   # Entfolgen
    # ... weitere Tests
```

**Abgedeckte Funktionen:**
- ✅ Initialisierung und Konfiguration
- ✅ API-Request Handling
- ✅ Rate Limiting
- ✅ Paginierung
- ✅ Fehlerbehandlung
- ✅ User-Operationen

### 2. FollowAnalyzer Tests

```python
class TestFollowAnalyzer:
    def test_analyze_follows(self):         # Follow-Analyse
    def test_generate_report(self):         # Report-Generierung
    # ... weitere Tests
```

**Abgedeckte Funktionen:**
- ✅ Follow-Verhältnis-Analyse
- ✅ Report-Generierung
- ✅ Datenverarbeitung
- ✅ Edge-Cases

### 3. Flask App Tests

```python
class TestFlaskApp:
    def test_index_route(self):             # Hauptseite
    def test_api_status_success(self):      # API-Endpunkte
    def test_api_cleanup_dry_run(self):     # Cleanup-Funktionen
    # ... weitere Tests
```

**Abgedeckte Endpunkte:**
- ✅ `/` - Hauptseite
- ✅ `/api/status` - Request-Status
- ✅ `/api/analyze` - Analyse
- ✅ `/api/cleanup` - Cleanup

### 4. Parametrisierte Tests

```python
@pytest.mark.parametrize("followers,following,expected", [
    ({"user1"}, {"user1"}, set()),  # Alle gegenseitig
    (set(), {"user1"}, {"user1"}),  # Nur Following
    # ... weitere Szenarien
])
def test_follow_analysis_scenarios(followers, following, expected):
    # Test verschiedener Follow-Konstellationen
```

## 🔍 Mocking und Fixtures

### Wichtige Mocks

```python
# API-Requests mocken
@patch('follow_fellow.requests.Session.request')
def test_api_call(self, mock_request):
    mock_request.return_value = Mock(status_code=200)

# Umgebungsvariablen mocken
@patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
def test_with_env_var(self):
    # Test mit gesetzter Umgebungsvariable
```

### Fixtures

```python
@pytest.fixture
def mock_response():
    """Standard Mock Response für API-Calls"""
    response = Mock()
    response.status_code = 200
    response.headers = {...}
    return response

@pytest.fixture
def sample_followers():
    """Beispiel-Follower für Tests"""
    return [{"login": "user1"}, {"login": "user2"}]
```

## 🚨 Fehlerbehandlung Tests

### API-Fehler

```python
def test_api_error_handling(self):
    """Test Verhalten bei API-Fehlern"""
    # 404, 401, 403, 500 Errors
    # Rate Limit Überschreitung
    # Netzwerk-Timeouts
```

### Input-Validierung

```python
def test_invalid_inputs(self):
    """Test mit ungültigen Eingaben"""
    # Leere Strings
    # None Values
    # Ungültige Token
```

## 📊 Test-Metriken

### Aktuelle Coverage

```
Name               Stmts   Miss  Cover   Missing
------------------------------------------------
follow_fellow.py     342     15    96%   125-127, 234-238
Total                342     15    96%
```

### Performance-Benchmarks

```
Test                               Time (ms)
----------------------------------------
test_init                         0.12
test_make_request_success          1.45
test_get_followers                 2.33
test_generate_report              12.67
```

## 🛠️ Debugging Tests

### Fehlgeschlagene Tests analysieren

```bash
# Ausführliche Fehler-Ausgabe
pytest --tb=long

# PDB Debugger bei Fehlern
pytest --pdb

# Nur fehlgeschlagene Tests wiederholen
pytest --lf

# Tests mit Ausgaben
pytest -s
```

### Test-Daten inspizieren

```python
def test_with_debug(self):
    result = some_function()
    print(f"Debug: {result}")  # Mit -s Flag sichtbar
    assert result == expected
```

## 🔄 Continuous Integration

### GitHub Actions Setup

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=follow_fellow
```

## 📝 Test-Best-Practices

### 1. Test-Naming

```python
def test_should_return_followers_when_api_succeeds(self):
    """Test sollte beschreibend benannt sein"""
    pass

def test_should_raise_error_when_token_invalid(self):
    """Given-When-Then Pattern verwenden"""
    pass
```

### 2. Test-Isolation

```python
def setup_method(self):
    """Jeder Test sollte isoliert sein"""
    self.manager = GitHubFollowManager("test", "token")

def teardown_method(self):
    """Cleanup nach jedem Test"""
    pass
```

### 3. Mock-Guidelines

```python
# Gut: Externe Dependencies mocken
@patch('requests.get')
def test_api_call(self, mock_get):
    pass

# Schlecht: Interne Logik mocken
@patch('follow_fellow.GitHubFollowManager._internal_method')
def test_bad_mock(self, mock_internal):
    pass
```

## 🔧 Test-Utilities

### Eigene Test-Helpers

```python
def create_mock_response(status=200, data=None):
    """Helper für Mock-Responses"""
    response = Mock()
    response.status_code = status
    response.json.return_value = data or {}
    return response

def create_test_manager():
    """Helper für Test-Manager"""
    return GitHubFollowManager("testuser", "testtoken")
```

## 📚 Weitere Ressourcen

- [pytest Dokumentation](https://docs.pytest.org/)
- [pytest-cov Dokumentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Dokumentation](https://docs.python.org/3/library/unittest.mock.html)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

## 🎯 Nächste Schritte

1. **Tests erweitern**: Weitere Edge-Cases abdecken
2. **Performance-Tests**: Benchmark-Tests hinzufügen
3. **Property-Based Testing**: Mit `hypothesis` experimentieren
4. **Mutation Testing**: Mit `mutmut` Code-Qualität prüfen

Für Fragen oder Verbesserungsvorschläge bitte ein Issue erstellen! 🚀
