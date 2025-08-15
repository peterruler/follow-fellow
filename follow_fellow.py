#!/usr/bin/env python3
"""
GitHub Follow-Fellow Script
Vergleicht Follower mit gefolgten Benutzern und entfernt einseitige Follows.
"""

import os
import sys
import json
import time
from typing import List, Dict, Set, Tuple
from datetime import datetime

import requests
import click
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__)

class GitHubFollowManager:
    def __init__(self, username: str, token: str):
        self.username = username
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Follow-Fellow/1.0"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """Macht eine API-Anfrage mit Rate Limiting."""
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Rate Limit prüfen
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(0, reset_time - int(time.time()) + 1)
                if wait_time > 0:
                    print(f"⏳ Rate limit erreicht. Warte {wait_time} Sekunden...")
                    time.sleep(wait_time)
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ API-Fehler: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def get_all_paginated(self, endpoint: str) -> List[Dict]:
        """Holt alle Seiten einer paginierten API-Antwort."""
        all_items = []
        url = f"{self.base_url}{endpoint}"
        
        while url:
            response = self._make_request(url)
            data = response.json()
            all_items.extend(data)
            
            # Nächste Seite aus Link-Header
            link_header = response.headers.get('Link', '')
            url = None
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    url = link.split('<')[1].split('>')[0]
                    break
        
        return all_items
    
    def get_followers(self) -> Set[str]:
        """Holt alle Follower des Benutzers."""
        print(f"📥 Lade Follower von {self.username}...")
        followers_data = self.get_all_paginated(f"/users/{self.username}/followers")
        followers = {user['login'] for user in followers_data}
        print(f"✅ {len(followers)} Follower gefunden")
        return followers
    
    def get_following(self) -> Set[str]:
        """Holt alle Benutzer, denen der Benutzer folgt."""
        print(f"📤 Lade Following von {self.username}...")
        following_data = self.get_all_paginated(f"/users/{self.username}/following")
        following = {user['login'] for user in following_data}
        print(f"✅ {len(following)} Following gefunden")
        return following
    
    def unfollow_user(self, username: str) -> bool:
        """Entfolgt einem Benutzer."""
        try:
            url = f"{self.base_url}/user/following/{username}"
            response = self._make_request(url, "DELETE")
            return response.status_code == 204
        except Exception as e:
            print(f"❌ Fehler beim Entfolgen von {username}: {e}")
            return False
    
    def get_user_info(self, username: str) -> Dict:
        """Holt Benutzerinformationen."""
        try:
            url = f"{self.base_url}/users/{username}"
            response = self._make_request(url)
            return response.json()
        except Exception as e:
            print(f"❌ Fehler beim Laden der Infos für {username}: {e}")
            return {}

class FollowAnalyzer:
    def __init__(self, manager: GitHubFollowManager):
        self.manager = manager
    
    def analyze_follows(self) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
        """Analysiert Follower vs Following."""
        followers = self.manager.get_followers()
        following = self.manager.get_following()
        
        # Einseitige Follows (ich folge, aber sie folgen mir nicht)
        one_way_follows = following - followers
        
        # Follower die mir folgen, aber ich folge ihnen nicht zurück
        not_following_back = followers - following
        
        # Gegenseitige Follows
        mutual_follows = following & followers
        
        return one_way_follows, mutual_follows, followers, not_following_back
    
    def generate_report(self) -> Dict:
        """Generiert einen detaillierten Report."""
        one_way, mutual, followers, not_following_back = self.analyze_follows()
        following = self.manager.get_following()
        
        # Detaillierte Infos für einseitige Follows sammeln
        one_way_details = []
        for username in sorted(one_way):
            user_info = self.manager.get_user_info(username)
            one_way_details.append({
                'username': username,
                'name': user_info.get('name', ''),
                'bio': user_info.get('bio', ''),
                'followers': user_info.get('followers', 0),
                'following': user_info.get('following', 0),
                'public_repos': user_info.get('public_repos', 0),
                'created_at': user_info.get('created_at', ''),
                'updated_at': user_info.get('updated_at', ''),
                'html_url': user_info.get('html_url', '')
            })
        
        # Detaillierte Infos für nicht zurückgefolgte Follower sammeln
        not_following_back_details = []
        for username in sorted(not_following_back):
            user_info = self.manager.get_user_info(username)
            not_following_back_details.append({
                'username': username,
                'name': user_info.get('name', ''),
                'bio': user_info.get('bio', ''),
                'followers': user_info.get('followers', 0),
                'following': user_info.get('following', 0),
                'public_repos': user_info.get('public_repos', 0),
                'created_at': user_info.get('created_at', ''),
                'updated_at': user_info.get('updated_at', ''),
                'html_url': user_info.get('html_url', '')
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user': self.manager.username,
            'stats': {
                'total_followers': len(followers),
                'total_following': len(following),
                'mutual_follows': len(mutual),
                'one_way_follows': len(one_way),
                'not_following_back': len(not_following_back)
            },
            'one_way_follows': one_way_details,
            'not_following_back': not_following_back_details,
            'mutual_follows': sorted(list(mutual))
        }

# Flask Web Interface
@app.route('/')
def index():
    """Hauptseite mit Analyse-Interface."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Follow-Fellow Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1, h2 { color: #333; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-card { background: #007acc; color: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1; }
            .user-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; background: #fafafa; }
            .user-header { display: flex; justify-content: space-between; align-items: center; }
            .user-stats { color: #666; font-size: 0.9em; margin-top: 10px; }
            .btn { background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #005a9e; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            .loading { text-align: center; padding: 20px; }
            .hidden { display: none; }
            .actions { margin: 20px 0; }
            .checkbox-container { margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐙 Follow-Fellow Dashboard</h1>
            <p>Analyse und Verwaltung von GitHub Follows für <strong>peterruler</strong></p>
            
            <div class="actions">
                <button class="btn" onclick="loadAnalysis()">📊 Analyse durchführen</button>
                <button class="btn btn-danger" onclick="performCleanup(true)">🧹 Dry Run</button>
                <button class="btn btn-danger" onclick="performCleanup(false)">⚠️ Cleanup durchführen</button>
            </div>
            
            <div id="loading" class="loading hidden">
                <p>⏳ Lade Daten...</p>
            </div>
            
            <div id="results" class="hidden">
                <div id="stats-container"></div>
                <div id="one-way-container"></div>
            </div>
        </div>

        <script>
            async function loadAnalysis() {
                showLoading();
                try {
                    const response = await fetch('/api/analyze');
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    alert('Fehler beim Laden der Analyse: ' + error.message);
                } finally {
                    hideLoading();
                }
            }

            async function performCleanup(dryRun) {
                if (!dryRun && !confirm('Sind Sie sicher, dass Sie das Cleanup durchführen möchten? Dies entfernt alle einseitigen Follows!')) {
                    return;
                }
                
                showLoading();
                try {
                    const response = await fetch('/api/cleanup', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ dry_run: dryRun })
                    });
                    const data = await response.json();
                    displayCleanupResults(data);
                } catch (error) {
                    alert('Fehler beim Cleanup: ' + error.message);
                } finally {
                    hideLoading();
                }
            }

            function displayResults(data) {
                const statsHtml = `
                    <div class="stats">
                        <div class="stat-card">
                            <h3>${data.stats.total_followers}</h3>
                            <p>Follower</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.stats.total_following}</h3>
                            <p>Following</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.stats.mutual_follows}</h3>
                            <p>Gegenseitig</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.stats.one_way_follows}</h3>
                            <p>Einseitig</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.stats.not_following_back}</h3>
                            <p>Nicht zurück</p>
                        </div>
                    </div>
                `;
                
                const oneWayHtml = `
                    <h2>🔍 Einseitige Follows (${data.one_way_follows.length})</h2>
                    <p>Diese Benutzer folgen Ihnen nicht zurück:</p>
                    ${data.one_way_follows.map(user => `
                        <div class="user-card">
                            <div class="user-header">
                                <div>
                                    <h3><a href="${user.html_url}" target="_blank">${user.username}</a></h3>
                                    ${user.name ? `<p><strong>${user.name}</strong></p>` : ''}
                                    ${user.bio ? `<p>${user.bio}</p>` : ''}
                                </div>
                            </div>
                            <div class="user-stats">
                                👥 ${user.followers} Follower | 
                                📤 ${user.following} Following | 
                                📂 ${user.public_repos} Repos |
                                📅 Seit ${new Date(user.created_at).toLocaleDateString('de-DE')}
                            </div>
                        </div>
                    `).join('')}
                    
                    <h2>🔄 Follower ohne Rückfolgen (${data.not_following_back.length})</h2>
                    <p>Diese Benutzer folgen Ihnen, aber Sie folgen ihnen nicht zurück:</p>
                    ${data.not_following_back.map(user => `
                        <div class="user-card">
                            <div class="user-header">
                                <div>
                                    <h3><a href="${user.html_url}" target="_blank">${user.username}</a></h3>
                                    ${user.name ? `<p><strong>${user.name}</strong></p>` : ''}
                                    ${user.bio ? `<p>${user.bio}</p>` : ''}
                                </div>
                            </div>
                            <div class="user-stats">
                                👥 ${user.followers} Follower | 
                                📤 ${user.following} Following | 
                                📂 ${user.public_repos} Repos |
                                📅 Seit ${new Date(user.created_at).toLocaleDateString('de-DE')}
                            </div>
                        </div>
                    `).join('')}
                `;
                
                document.getElementById('stats-container').innerHTML = statsHtml;
                document.getElementById('one-way-container').innerHTML = oneWayHtml;
                document.getElementById('results').classList.remove('hidden');
            }

            function displayCleanupResults(data) {
                const resultsHtml = `
                    <div style="background: ${data.dry_run ? '#fff3cd' : '#d1edff'}; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h2>${data.dry_run ? '🔍 Dry Run Ergebnisse' : '✅ Cleanup Abgeschlossen'}</h2>
                        <p><strong>${data.processed}</strong> Benutzer verarbeitet</p>
                        ${data.dry_run ? '<p>Kein Follow wurde tatsächlich entfernt.</p>' : '<p>Alle einseitigen Follows wurden entfernt.</p>'}
                        <div style="margin-top: 15px;">
                            <h3>Verarbeitete Benutzer:</h3>
                            <ul>
                                ${data.users.map(user => `<li>${user}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
                document.getElementById('results').innerHTML = resultsHtml;
                document.getElementById('results').classList.remove('hidden');
            }

            function showLoading() {
                document.getElementById('loading').classList.remove('hidden');
                document.getElementById('results').classList.add('hidden');
            }

            function hideLoading() {
                document.getElementById('loading').classList.add('hidden');
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/analyze')
def api_analyze():
    """API-Endpoint für die Analyse."""
    try:
        username = os.getenv('GITHUB_USERNAME', 'peterruler')
        token = os.getenv('GITHUB_TOKEN')
        
        if not token:
            return jsonify({'error': 'GitHub Token nicht gefunden'}), 400
        
        manager = GitHubFollowManager(username, token)
        analyzer = FollowAnalyzer(manager)
        report = analyzer.generate_report()
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    """API-Endpoint für das Cleanup."""
    try:
        data = request.get_json()
        dry_run = data.get('dry_run', True)
        
        username = os.getenv('GITHUB_USERNAME', 'peterruler')
        token = os.getenv('GITHUB_TOKEN')
        
        if not token:
            return jsonify({'error': 'GitHub Token nicht gefunden'}), 400
        
        manager = GitHubFollowManager(username, token)
        analyzer = FollowAnalyzer(manager)
        
        one_way_follows, _, _, _ = analyzer.analyze_follows()
        
        processed_users = []
        for user in one_way_follows:
            processed_users.append(user)
            if not dry_run:
                success = manager.unfollow_user(user)
                print(f"{'✅' if success else '❌'} Entfolgt: {user}")
        
        return jsonify({
            'dry_run': dry_run,
            'processed': len(processed_users),
            'users': processed_users
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CLI Interface
@click.command()
@click.option('--dry-run', is_flag=True, help='Führt nur eine Simulation durch, ohne tatsächlich zu entfolgen')
@click.option('--username', default='peterruler', help='GitHub Username (Standard: peterruler)')
@click.option('--token', help='GitHub Personal Access Token (oder über GITHUB_TOKEN env var)')
@click.option('--web', is_flag=True, help='Startet die Web-Oberfläche')
@click.option('--port', default=5000, help='Port für die Web-Oberfläche (Standard: 5000)')
def main(dry_run, username, token, web, port):
    """GitHub Follow-Fellow - Verwaltet einseitige GitHub Follows."""
    
    if web:
        print(f"🚀 Starte Web-Oberfläche auf http://localhost:{port}")
        print("Drücken Sie Ctrl+C zum Beenden")
        app.run(debug=True, port=port, host='0.0.0.0')
        return
    
    # Token aus Umgebungsvariable falls nicht angegeben
    if not token:
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("❌ GitHub Token erforderlich! Setzen Sie GITHUB_TOKEN oder verwenden Sie --token")
            sys.exit(1)
    
    try:
        print(f"🐙 Follow-Fellow für {username}")
        print("=" * 50)
        
        manager = GitHubFollowManager(username, token)
        analyzer = FollowAnalyzer(manager)
        
        print("📊 Analysiere Follows...")
        one_way_follows, mutual_follows, followers, not_following_back = analyzer.analyze_follows()
        following = manager.get_following()
        
        # Report ausgeben
        print("\n📈 ZUSAMMENFASSUNG")
        print("=" * 30)
        print(f"👥 Follower: {len(followers)}")
        print(f"📤 Following: {len(following)}")
        print(f"🤝 Gegenseitig: {len(mutual_follows)}")
        print(f"➡️  Einseitig: {len(one_way_follows)}")
        print(f"⬅️  Folgen mir, ich nicht zurück: {len(not_following_back)}")
        
        if one_way_follows:
            print(f"\n🔍 EINSEITIGE FOLLOWS ({len(one_way_follows)})")
            print("=" * 40)
            print(f"{username} folgt diesen Benutzern, aber sie folgen nicht zurück:")
            
            for user in sorted(one_way_follows):
                user_info = manager.get_user_info(user)
                name = user_info.get('name', '')
                followers_count = user_info.get('followers', 0)
                print(f"  • {user} {f'({name})' if name else ''} - {followers_count} Follower")
        
        if not_following_back:
            print(f"\n🔄 FOLLOWER OHNE RÜCKFOLGEN ({len(not_following_back)})")
            print("=" * 50)
            print(f"Diese Benutzer folgen {username}, aber {username} folgt nicht zurück:")
            
            for user in sorted(not_following_back):
                user_info = manager.get_user_info(user)
                name = user_info.get('name', '')
                followers_count = user_info.get('followers', 0)
                print(f"  • {user} {f'({name})' if name else ''} - {followers_count} Follower")
            
            if dry_run:
                print(f"\n🔍 DRY RUN MODUS")
                print("=" * 20)
                print(f"Würde {len(one_way_follows)} Benutzer entfolgen:")
                for user in sorted(one_way_follows):
                    print(f"  • Würde {user} entfolgen")
            else:
                print(f"\n⚠️  CLEANUP DURCHFÜHREN")
                print("=" * 25)
                confirm = input(f"Möchten Sie wirklich {len(one_way_follows)} Benutzer entfolgen? (ja/nein): ")
                
                if confirm.lower() in ['ja', 'j', 'yes', 'y']:
                    successful = 0
                    failed = 0
                    
                    for user in one_way_follows:
                        print(f"🔄 Entfolge {user}...")
                        if manager.unfollow_user(user):
                            print(f"✅ {user} erfolgreich entfolgt")
                            successful += 1
                        else:
                            print(f"❌ Fehler beim Entfolgen von {user}")
                            failed += 1
                        
                        # Kurze Pause zwischen Requests
                        time.sleep(0.5)
                    
                    print(f"\n🎉 CLEANUP ABGESCHLOSSEN")
                    print("=" * 25)
                    print(f"✅ Erfolgreich: {successful}")
                    print(f"❌ Fehlgeschlagen: {failed}")
                else:
                    print("❌ Abgebrochen")
        else:
            print("\n🎉 Keine einseitigen Follows gefunden! Alle Follows sind gegenseitig.")
        
        if not not_following_back:
            print("\n🎉 Sie folgen allen Ihren Followern zurück!")
        
        print(f"\n📅 Analyse abgeschlossen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
