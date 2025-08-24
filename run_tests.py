#!/usr/bin/env python3
"""
Test Runner für Follow-Fellow
Einfache Ausführung verschiedener Test-Szenarien
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Führt einen Befehl aus und zeigt das Ergebnis an"""
    print(f"\n🚀 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Erfolgreich!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Fehlgeschlagen!")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen: {e}")
        return False


def main():
    """Hauptfunktion des Test-Runners"""
    print("🧪 Follow-Fellow Test Runner")
    print("=" * 50)
    
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not Path("follow_fellow.py").exists():
        print("❌ follow_fellow.py nicht gefunden!")
        print("Bitte führen Sie dieses Script im Projekt-Verzeichnis aus.")
        sys.exit(1)
    
    # Installiere Test-Dependencies falls nötig
    print("🔧 Prüfe Test-Dependencies...")
    try:
        import pytest
        print("✅ pytest ist installiert")
    except ImportError:
        print("📦 Installiere Test-Dependencies...")
        if not run_command("pip install pytest pytest-cov pytest-mock", "Dependencies installieren"):
            print("❌ Konnte Dependencies nicht installieren!")
            sys.exit(1)
    
    # Test-Szenarien
    scenarios = [
        {
            "name": "Schnelle Tests",
            "cmd": "pytest -x --tb=short",
            "description": "Führt Tests bis zum ersten Fehler aus"
        },
        {
            "name": "Alle Tests mit Details",
            "cmd": "pytest -v",
            "description": "Alle Tests mit ausführlicher Ausgabe"
        },
        {
            "name": "Coverage Report",
            "cmd": "pytest --cov=follow_fellow --cov-report=term-missing",
            "description": "Tests mit Coverage-Analyse"
        },
        {
            "name": "HTML Coverage Report",
            "cmd": "pytest --cov=follow_fellow --cov-report=html",
            "description": "Erstellt HTML Coverage Report"
        },
        {
            "name": "Nur Unit Tests",
            "cmd": "pytest test_follow_fellow.py::TestGitHubFollowManager test_follow_fellow.py::TestFollowAnalyzer -v",
            "description": "Nur Unit-Tests ausführen"
        },
        {
            "name": "Nur API Tests",
            "cmd": "pytest test_follow_fellow.py::TestFlaskApp -v",
            "description": "Nur Flask API Tests"
        }
    ]
    
    # Zeige verfügbare Optionen
    print("\n📋 Verfügbare Test-Szenarien:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario['name']} - {scenario['description']}")
    
    print("  7. Alle Szenarien nacheinander")
    print("  0. Beenden")
    
    # Benutzereingabe
    try:
        choice = input("\n🎯 Wählen Sie ein Szenario (1-7, 0 zum Beenden): ").strip()
        
        if choice == "0":
            print("👋 Auf Wiedersehen!")
            return
        
        elif choice == "7":
            print("\n🚀 Führe alle Test-Szenarien aus...")
            success_count = 0
            
            for scenario in scenarios:
                if run_command(scenario["cmd"], scenario["name"]):
                    success_count += 1
            
            print(f"\n📊 Zusammenfassung: {success_count}/{len(scenarios)} Szenarien erfolgreich")
            
            if success_count == len(scenarios):
                print("🎉 Alle Tests erfolgreich!")
            else:
                print("⚠️  Einige Tests sind fehlgeschlagen.")
        
        elif choice.isdigit() and 1 <= int(choice) <= len(scenarios):
            scenario = scenarios[int(choice) - 1]
            success = run_command(scenario["cmd"], scenario["name"])
            
            if success:
                print("🎉 Test erfolgreich abgeschlossen!")
            else:
                print("⚠️  Test ist fehlgeschlagen.")
        
        else:
            print("❌ Ungültige Auswahl!")
            return
    
    except KeyboardInterrupt:
        print("\n\n👋 Beendet durch Benutzer.")
        return
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        return
    
    # HTML Coverage Report öffnen falls erstellt
    html_report = Path("htmlcov/index.html")
    if html_report.exists():
        try:
            if sys.platform.startswith('darwin'):  # macOS
                os.system("open htmlcov/index.html")
            elif sys.platform.startswith('linux'):  # Linux
                os.system("xdg-open htmlcov/index.html")
            elif sys.platform.startswith('win'):  # Windows
                os.system("start htmlcov/index.html")
            print("🌐 HTML Coverage Report wurde geöffnet.")
        except:
            print("📄 HTML Coverage Report erstellt: htmlcov/index.html")


if __name__ == "__main__":
    main()
