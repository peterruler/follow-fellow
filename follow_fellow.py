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
        # Request-Zähler für Limitierung
        self.request_count = 0
        self.max_requests = int(os.getenv('MAX_API_REQUESTS', 2500))
        # User Processing Limit
        self.max_users_to_process = int(os.getenv('MAX_USERS_TO_PROCESS', 200))
        # GitHub Rate Limit Tracking
        self.last_rate_limit_remaining = None
        self.last_rate_limit_total = None
        self.last_rate_limit_reset = None
    
    def _make_request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """Macht eine API-Anfrage mit Rate Limiting. GitHub Rate Limit hat Vorrang vor MAX_API_REQUESTS."""
        try:
            response = self.session.request(method, url, **kwargs)
            self.request_count += 1
            
            # GitHub Rate Limit Informationen aus Response Headers
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            rate_limit_total = int(response.headers.get('X-RateLimit-Limit', 0))
            rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
            
            # Speichere Rate Limit Informationen
            self.last_rate_limit_remaining = rate_limit_remaining
            self.last_rate_limit_total = rate_limit_total
            self.last_rate_limit_reset = rate_limit_reset
            
            # Formatiere Reset-Zeit
            reset_time_str = ""
            if rate_limit_reset > 0:
                reset_time = datetime.fromtimestamp(rate_limit_reset)
                reset_time_str = f" (Reset: {reset_time.strftime('%H:%M:%S')})"
            
            # Zeige jeden Request mit Rate Limit Status
            endpoint = url.replace(self.base_url, "").split('?')[0]  # Bereinige URL für Anzeige
            print(f"🔄 Request #{self.request_count}/{self.max_requests} -> {method} {endpoint}")
            print(f"   📊 GitHub Rate Limit: {rate_limit_remaining}/{rate_limit_total}{reset_time_str}")
            
            # Rate Limit Warnung
            if rate_limit_remaining < 100:
                print(f"   ⚠️  Wenig Rate Limit übrig: {rate_limit_remaining}")
            
            # Rate Limit prüfen
            if rate_limit_remaining < 10:
                wait_time = max(0, rate_limit_reset - int(time.time()) + 1)
                if wait_time > 0:
                    print(f"   ⏳ Rate limit fast erreicht. Warte {wait_time} Sekunden...")
                    time.sleep(wait_time)
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ API-Fehler bei Request #{self.request_count}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def get_request_status(self) -> Dict:
        """Gibt den aktuellen Request-Status zurück."""
        status = {
            'current_requests': self.request_count,
            'max_requests': self.max_requests,
            'remaining_requests': self.max_requests - self.request_count,
            'usage_percentage': (self.request_count / self.max_requests) * 100,
            'max_users_to_process': self.max_users_to_process
        }
        
        # Füge GitHub Rate Limit Informationen hinzu, falls verfügbar
        if self.last_rate_limit_remaining is not None:
            status['github_rate_limit'] = {
                'remaining': self.last_rate_limit_remaining,
                'total': self.last_rate_limit_total,
                'reset_timestamp': self.last_rate_limit_reset,
                'reset_time': datetime.fromtimestamp(self.last_rate_limit_reset).strftime('%H:%M:%S') if self.last_rate_limit_reset else None
            }
        
        return status
    
    def get_all_paginated(self, endpoint: str) -> List[Dict]:
        """Holt alle Seiten einer paginierten API-Antwort. Nur GitHub Rate Limit wird berücksichtigt."""
        all_items = []
        url = f"{self.base_url}{endpoint}"
        
        while url:
            # Prüfe GitHub Rate Limit vor jeder Anfrage (nicht MAX_API_REQUESTS)
            if self.last_rate_limit_remaining is not None and self.last_rate_limit_remaining <= 10:
                print(f"\n❌ KRITISCHER FEHLER: GITHUB RATE LIMIT ERREICHT!")
                print("=" * 60)
                print(f"Das GitHub API Rate Limit ist fast aufgebraucht: {self.last_rate_limit_remaining}")
                print(f"Paginierten Abruf für {endpoint} wird abgebrochen.")
                print("Das Programm wird beendet, um API-Missbrauch zu verhindern.")
                print("=" * 60)
                break
                
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
        status = self.get_request_status()
        print(f"📊 API-Requests verwendet: {status['current_requests']}/{status['max_requests']} ({status['usage_percentage']:.1f}%)")
        if 'github_rate_limit' in status:
            rl = status['github_rate_limit']
            print(f"🔄 GitHub Rate Limit: {rl['remaining']}/{rl['total']} (Reset: {rl['reset_time']})")
        return followers
    
    def get_following(self) -> Set[str]:
        """Holt alle Benutzer, denen der Benutzer folgt."""
        print(f"📤 Lade Following von {self.username}...")
        following_data = self.get_all_paginated(f"/users/{self.username}/following")
        following = {user['login'] for user in following_data}
        print(f"✅ {len(following)} Following gefunden")
        status = self.get_request_status()
        print(f"📊 API-Requests verwendet: {status['current_requests']}/{status['max_requests']} ({status['usage_percentage']:.1f}%)")
        if 'github_rate_limit' in status:
            rl = status['github_rate_limit']
            print(f"🔄 GitHub Rate Limit: {rl['remaining']}/{rl['total']} (Reset: {rl['reset_time']})")
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
        
        # Detaillierte Infos für einseitige Follows sammeln (begrenzt auf MAX_USERS_TO_PROCESS)
        one_way_details = []
        one_way_limited = list(sorted(one_way))[:self.manager.max_users_to_process]
        
        print(f"📊 Verarbeite {len(one_way_limited)} von {len(one_way)} einseitigen Follows (Limit: {self.manager.max_users_to_process})")
        
        for i, username in enumerate(one_way_limited, 1):
            # Prüfe GitHub Rate Limit vor jeder User-Info-Anfrage (nicht MAX_API_REQUESTS)
            if self.manager.last_rate_limit_remaining is not None and self.manager.last_rate_limit_remaining <= 10:
                print(f"\n❌ KRITISCHER FEHLER: GITHUB RATE LIMIT ERREICHT!")
                print("=" * 60)
                print(f"Das GitHub API Rate Limit ist fast aufgebraucht: {self.manager.last_rate_limit_remaining}")
                print(f"Detaillierte User-Infos für verbleibende {len(one_way_limited) - len(one_way_details)} Benutzer werden übersprungen.")
                print("Das Programm wird beendet, um API-Missbrauch zu verhindern.")
                print("=" * 60)
                break
            
            print(f"📋 Verarbeite User {i}/{len(one_way_limited)}: {username}")
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
        
        # Detaillierte Infos für nicht zurückgefolgte Follower sammeln (begrenzt auf MAX_USERS_TO_PROCESS)
        not_following_back_details = []
        not_following_back_limited = list(sorted(not_following_back))[:self.manager.max_users_to_process]
        
        print(f"📊 Verarbeite {len(not_following_back_limited)} von {len(not_following_back)} nicht zurückgefolgten Followern (Limit: {self.manager.max_users_to_process})")
        
        for i, username in enumerate(not_following_back_limited, 1):
            # Prüfe GitHub Rate Limit vor jeder User-Info-Anfrage (nicht MAX_API_REQUESTS)
            if self.manager.last_rate_limit_remaining is not None and self.manager.last_rate_limit_remaining <= 10:
                print(f"\n❌ KRITISCHER FEHLER: GITHUB RATE LIMIT ERREICHT!")
                print("=" * 60)
                print(f"Das GitHub API Rate Limit ist fast aufgebraucht: {self.manager.last_rate_limit_remaining}")
                print(f"Detaillierte User-Infos für verbleibende {len(not_following_back_limited) - len(not_following_back_details)} Benutzer werden übersprungen.")
                print("Das Programm wird beendet, um API-Missbrauch zu verhindern.")
                print("=" * 60)
                break
            
            print(f"📋 Verarbeite User {i}/{len(not_following_back_limited)}: {username}")
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
        
        # Request-Status hinzufügen
        request_status = self.manager.get_request_status()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user': self.manager.username,
            'request_status': request_status,
            'processing_limits': {
                'max_users_to_process': self.manager.max_users_to_process,
                'one_way_total': len(one_way),
                'one_way_processed': len(one_way_details),
                'not_following_back_total': len(not_following_back),
                'not_following_back_processed': len(not_following_back_details)
            },
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
                <button class="btn btn-danger" onclick="performCleanup(true)">🧹 Dry Run (Simulation)</button>
                <button class="btn btn-danger" onclick="performCleanup(false)">⚠️ Einseitige Follows entfernen</button>
                <button class="btn" onclick="loadStatus()">📊 Request-Status</button>
            </div>
            
            <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2196f3;">
                <p><strong>ℹ️  Wichtiger Hinweis:</strong> Das Cleanup entfernt nur einseitige Follows (Benutzer, die Ihnen NICHT zurückfolgen). Benutzer, die Ihnen folgen, werden niemals entfolgt.</p>
            </div>
            
            <div id="status-container" class="hidden">
                <div id="status-display"></div>
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

            async function loadStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    displayStatus(data);
                } catch (error) {
                    alert('Fehler beim Laden des Status: ' + error.message);
                }
            }

            async function performCleanup(dryRun) {
                if (!dryRun && !confirm('Sind Sie sicher, dass Sie einseitige Follows entfernen möchten?\\n\\nWICHTIG: Es werden nur Benutzer entfolgt, die Ihnen NICHT zurückfolgen!\\nBenutzer, die Ihnen folgen, bleiben unberührt.')) {
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

            function displayStatus(data) {
                var status = data.status;
                var progressColor = status.usage_percentage > 80 ? '#f44336' : status.usage_percentage > 60 ? '#ff9800' : '#4caf50';
                
                var statusHtml = '<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">';
                statusHtml += '<h3>📊 API Request Status</h3>';
                statusHtml += '<p><strong>Verwendete Requests:</strong> ' + status.current_requests + ' / ' + status.max_requests + '</p>';
                statusHtml += '<p><strong>Verbleibende Requests:</strong> ' + status.remaining_requests + '</p>';
                statusHtml += '<p><strong>Nutzung:</strong> ' + status.usage_percentage.toFixed(1) + '%</p>';
                statusHtml += '<div style="background: #fff; border-radius: 4px; overflow: hidden; margin: 10px 0;">';
                statusHtml += '<div style="width: ' + status.usage_percentage + '%; background: ' + progressColor + '; height: 20px; transition: width 0.3s;"></div>';
                statusHtml += '</div>';
                statusHtml += '</div>';
                
                document.getElementById('status-display').innerHTML = statusHtml;
                document.getElementById('status-container').classList.remove('hidden');
            }

            function displayResults(data) {
                // Request-Status anzeigen wenn verfügbar
                if (data.request_status) {
                    displayStatus({status: data.request_status});
                }
                
                var limitsInfo = '';
                if (data.processing_limits) {
                    var pl = data.processing_limits;
                    limitsInfo = '<div style="background: #fff3cd; padding: 10px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ffc107;">';
                    limitsInfo += '<h4>📊 Verarbeitungsgrenze</h4>';
                    limitsInfo += '<p><strong>Maximale Benutzer pro Kategorie:</strong> ' + pl.max_users_to_process + '</p>';
                    limitsInfo += '<p><strong>Einseitige Follows:</strong> ' + pl.one_way_processed + ' von ' + pl.one_way_total + ' verarbeitet</p>';
                    limitsInfo += '<p><strong>Nicht zurück gefolgt:</strong> ' + pl.not_following_back_processed + ' von ' + pl.not_following_back_total + ' verarbeitet</p>';
                    limitsInfo += '</div>';
                }
                
                var statsHtml = limitsInfo;
                statsHtml += '<div class="stats">';
                statsHtml += '<div class="stat-card">';
                statsHtml += '<h3>' + data.stats.total_followers + '</h3>';
                statsHtml += '<p>Follower</p>';
                statsHtml += '</div>';
                statsHtml += '<div class="stat-card">';
                statsHtml += '<h3>' + data.stats.total_following + '</h3>';
                statsHtml += '<p>Following</p>';
                statsHtml += '</div>';
                statsHtml += '<div class="stat-card">';
                statsHtml += '<h3>' + data.stats.mutual_follows + '</h3>';
                statsHtml += '<p>Gegenseitig</p>';
                statsHtml += '</div>';
                statsHtml += '<div class="stat-card">';
                statsHtml += '<h3>' + data.stats.one_way_follows + '</h3>';
                statsHtml += '<p>Einseitig</p>';
                statsHtml += '</div>';
                statsHtml += '<div class="stat-card">';
                statsHtml += '<h3>' + data.stats.not_following_back + '</h3>';
                statsHtml += '<p>Nicht zurück</p>';
                statsHtml += '</div>';
                statsHtml += '</div>';
                
                var oneWayHtml = '<h2>🔍 Einseitige Follows (' + data.one_way_follows.length + ') - ⚠️ Können entfolgt werden</h2>';
                oneWayHtml += '<p><strong>Diese Benutzer folgen Ihnen NICHT zurück:</strong></p>';
                oneWayHtml += '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;">';
                oneWayHtml += '<strong>💡 Info:</strong> Diese Benutzer können beim Cleanup sicher entfolgt werden.';
                oneWayHtml += '</div>';
                
                data.one_way_follows.forEach(function(user) {
                    oneWayHtml += '<div class="user-card">';
                    oneWayHtml += '<div class="user-header">';
                    oneWayHtml += '<div>';
                    oneWayHtml += '<h3><a href="' + user.html_url + '" target="_blank">' + user.username + '</a> <span style="color: #dc3545;">❌ Folgt nicht zurück</span></h3>';
                    if (user.name) {
                        oneWayHtml += '<p><strong>' + user.name + '</strong></p>';
                    }
                    if (user.bio) {
                        oneWayHtml += '<p>' + user.bio + '</p>';
                    }
                    oneWayHtml += '</div>';
                    oneWayHtml += '</div>';
                    oneWayHtml += '<div class="user-stats">';
                    oneWayHtml += '👥 ' + user.followers + ' Follower | ';
                    oneWayHtml += '📤 ' + user.following + ' Following | ';
                    oneWayHtml += '📂 ' + user.public_repos + ' Repos |';
                    oneWayHtml += '📅 Seit ' + new Date(user.created_at).toLocaleDateString('de-DE');
                    oneWayHtml += '</div>';
                    oneWayHtml += '</div>';
                });
                
                oneWayHtml += '<h2>🔄 Follower ohne Rückfolgen (' + data.not_following_back.length + ') - ✅ Sicher vor Cleanup</h2>';
                oneWayHtml += '<p><strong>Diese Benutzer folgen Ihnen, aber Sie folgen ihnen nicht zurück:</strong></p>';
                oneWayHtml += '<div style="background: #d1edff; padding: 10px; border-radius: 5px; margin: 10px 0;">';
                oneWayHtml += '<strong>🛡️ Sicherheit:</strong> Diese Benutzer werden NIEMALS beim Cleanup entfolgt, da sie Ihnen folgen!';
                oneWayHtml += '</div>';
                
                data.not_following_back.forEach(function(user) {
                    oneWayHtml += '<div class="user-card">';
                    oneWayHtml += '<div class="user-header">';
                    oneWayHtml += '<div>';
                    oneWayHtml += '<h3><a href="' + user.html_url + '" target="_blank">' + user.username + '</a> <span style="color: #28a745;">✅ Folgt Ihnen</span></h3>';
                    if (user.name) {
                        oneWayHtml += '<p><strong>' + user.name + '</strong></p>';
                    }
                    if (user.bio) {
                        oneWayHtml += '<p>' + user.bio + '</p>';
                    }
                    oneWayHtml += '</div>';
                    oneWayHtml += '</div>';
                    oneWayHtml += '<div class="user-stats">';
                    oneWayHtml += '👥 ' + user.followers + ' Follower | ';
                    oneWayHtml += '📤 ' + user.following + ' Following | ';
                    oneWayHtml += '📂 ' + user.public_repos + ' Repos |';
                    oneWayHtml += '📅 Seit ' + new Date(user.created_at).toLocaleDateString('de-DE');
                    oneWayHtml += '</div>';
                    oneWayHtml += '</div>';
                });
                
                document.getElementById('stats-container').innerHTML = statsHtml;
                document.getElementById('one-way-container').innerHTML = oneWayHtml;
                document.getElementById('results').classList.remove('hidden');
            }

            function displayCleanupResults(data) {
                var bgColor = data.dry_run ? '#fff3cd' : '#d1edff';
                var title = data.dry_run ? '🔍 Dry Run Ergebnisse' : '✅ Cleanup Abgeschlossen';
                var actionText = data.dry_run ? 'simuliert' : 'entfolgt';
                var conclusionText = data.dry_run ? 'Kein Follow wurde tatsächlich entfernt.' : 'Alle einseitigen Follows wurden entfernt.';
                
                var resultsHtml = '<div style="background: ' + bgColor + '; padding: 15px; border-radius: 8px; margin: 20px 0;">';
                resultsHtml += '<h2>' + title + '</h2>';
                resultsHtml += '<p><strong>' + data.processed + '</strong> einseitige Follows verarbeitet</p>';
                resultsHtml += '<p><strong>Wichtig:</strong> Nur Benutzer, die Ihnen NICHT zurückfolgen, wurden ' + actionText + '.</p>';
                resultsHtml += '<p>' + conclusionText + '</p>';
                resultsHtml += '<div style="margin-top: 15px;">';
                resultsHtml += '<h3>Verarbeitete Benutzer:</h3>';
                resultsHtml += '<ul>';
                
                for (var i = 0; i < data.users.length; i++) {
                    resultsHtml += '<li>' + data.users[i] + '</li>';
                }
                
                resultsHtml += '</ul>';
                resultsHtml += '</div>';
                resultsHtml += '</div>';
                
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

@app.route('/api/status')
def api_status():
    """API-Endpoint für den Request-Status."""
    try:
        username = os.getenv('GITHUB_USERNAME', 'peterruler')
        token = os.getenv('GITHUB_TOKEN')
        
        if not token:
            return jsonify({'error': 'GitHub Token nicht gefunden'}), 400
        
        manager = GitHubFollowManager(username, token)
        status = manager.get_request_status()
        
        return jsonify({
            'status': status,
            'message': f"API-Requests: {status['current_requests']}/{status['max_requests']} ({status['usage_percentage']:.1f}%)"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        try:
            report = analyzer.generate_report()
            return jsonify(report)
        except Exception as e:
            if "GitHub Rate Limit erreicht" in str(e):
                return jsonify({
                    'error': 'GitHub Rate Limit erreicht',
                    'message': f'Das GitHub API Rate Limit wurde erreicht. Warten Sie bis zur Reset-Zeit.',
                    'current_requests': manager.request_count,
                    'github_rate_limit': manager.last_rate_limit_remaining
                }), 429
            else:
                return jsonify({'error': str(e)}), 500
        
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
        
        try:
            one_way_follows, _, _, _ = analyzer.analyze_follows()
            
            processed_users = []
            for user in one_way_follows:
                # Prüfe GitHub Rate Limit vor jedem Unfollow (nicht MAX_API_REQUESTS)
                if manager.last_rate_limit_remaining is not None and manager.last_rate_limit_remaining <= 10:
                    return jsonify({
                        'error': 'GitHub Rate Limit erreicht',
                        'message': f'Das GitHub API Rate Limit wurde erreicht.',
                        'dry_run': dry_run,
                        'processed': len(processed_users),
                        'users': processed_users,
                        'incomplete': True
                    }), 429
                
                processed_users.append(user)
                if not dry_run:
                    success = manager.unfollow_user(user)
                    print(f"{'✅' if success else '❌'} Entfolgt: {user}")
            
            return jsonify({
                'dry_run': dry_run,
                'processed': len(processed_users),
                'users': processed_users,
                'incomplete': False
            })
            
        except Exception as e:
            if "GitHub Rate Limit erreicht" in str(e):
                return jsonify({
                    'error': 'GitHub Rate Limit erreicht',
                    'message': f'Das GitHub API Rate Limit wurde erreicht.',
                    'current_requests': manager.request_count,
                    'github_rate_limit': manager.last_rate_limit_remaining
                }), 429
            else:
                return jsonify({'error': str(e)}), 500
                
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
        try:
            one_way_follows, mutual_follows, followers, not_following_back = analyzer.analyze_follows()
            following = manager.get_following()
        except Exception as e:
            if "GitHub Rate Limit erreicht" in str(e):
                print(f"\n💡 EMPFEHLUNG:")
                print("- Warten Sie bis das GitHub Rate Limit zurückgesetzt wird")
                print("- Das GitHub API erlaubt 5000 Requests pro Stunde für authentifizierte Anfragen")
                print("- Das Programm wurde sicher beendet, keine weiteren API-Requests wurden gemacht")
                sys.exit(1)
            else:
                raise e
        
        # Request-Status anzeigen
        status = manager.get_request_status()
        print(f"\n📊 API REQUEST STATUS")
        print("=" * 25)
        print(f"Verwendete Requests: {status['current_requests']}/{status['max_requests']} ({status['usage_percentage']:.1f}%)")
        print(f"Verbleibende Requests: {status['remaining_requests']}")
        print(f"Max. Users zu verarbeiten: {status['max_users_to_process']}")
        
        # Warnung wenn fast alle Requests aufgebraucht
        if status['remaining_requests'] <= 100:
            print(f"⚠️  WARNUNG: Nur noch {status['remaining_requests']} Requests übrig!")
        
        # GitHub Rate Limit Status anzeigen falls verfügbar
        if 'github_rate_limit' in status:
            rl = status['github_rate_limit']
            print(f"\n🔄 GITHUB RATE LIMIT STATUS")
            print("=" * 30)
            print(f"Verbleibendes Rate Limit: {rl['remaining']}/{rl['total']}")
            print(f"Rate Limit Reset: {rl['reset_time']}")
            
            # Warnung bei niedrigem Rate Limit
            if rl['remaining'] < 100:
                print(f"⚠️  WARNUNG: Niedriges Rate Limit! Nur noch {rl['remaining']} Requests übrig.")
        
        # Report ausgeben
        print("\n📈 ZUSAMMENFASSUNG")
        print("=" * 30)
        print(f"👥 Follower: {len(followers)}")
        print(f"📤 Following: {len(following)}")
        print(f"🤝 Gegenseitig: {len(mutual_follows)}")
        print(f"➡️  Einseitig: {len(one_way_follows)}")
        print(f"⬅️  Folgen mir, ich nicht zurück: {len(not_following_back)}")
        
        if one_way_follows:
            print(f"\n🔍 EINSEITIGE FOLLOWS ({len(one_way_follows)} total)")
            print("=" * 40)
            print(f"{username} folgt diesen Benutzern, aber sie folgen NICHT zurück:")
            print("(Diese können beim Cleanup entfolgt werden)")
            
            # Begrenzt auf max_users_to_process für detaillierte Ausgabe
            one_way_limited = list(sorted(one_way_follows))[:manager.max_users_to_process]
            if len(one_way_limited) < len(one_way_follows):
                print(f"📊 Zeige {len(one_way_limited)} von {len(one_way_follows)} Benutzern (Limit: {manager.max_users_to_process}):")
            
            for user in one_way_limited:
                user_info = manager.get_user_info(user)
                name = user_info.get('name', '')
                followers_count = user_info.get('followers', 0)
                print(f"  • {user} {f'({name})' if name else ''} - {followers_count} Follower")
            
            if len(one_way_limited) < len(one_way_follows):
                remaining = len(one_way_follows) - len(one_way_limited)
                print(f"  ... und {remaining} weitere (erhöhen Sie MAX_USERS_TO_PROCESS für vollständige Liste)")
        
        if not_following_back:
            print(f"\n🔄 FOLLOWER OHNE RÜCKFOLGEN ({len(not_following_back)} total)")
            print("=" * 50)
            print(f"Diese Benutzer folgen {username}, aber {username} folgt NICHT zurück:")
            print("(Diese werden beim Cleanup NICHT entfolgt - sie folgen Ihnen ja!)")
            
            # Begrenzt auf max_users_to_process für detaillierte Ausgabe
            not_following_back_limited = list(sorted(not_following_back))[:manager.max_users_to_process]
            if len(not_following_back_limited) < len(not_following_back):
                print(f"📊 Zeige {len(not_following_back_limited)} von {len(not_following_back)} Benutzern (Limit: {manager.max_users_to_process}):")
            
            for user in not_following_back_limited:
                user_info = manager.get_user_info(user)
                name = user_info.get('name', '')
                followers_count = user_info.get('followers', 0)
                print(f"  • {user} {f'({name})' if name else ''} - {followers_count} Follower")
            
            if len(not_following_back_limited) < len(not_following_back):
                remaining = len(not_following_back) - len(not_following_back_limited)
                print(f"  ... und {remaining} weitere (erhöhen Sie MAX_USERS_TO_PROCESS für vollständige Liste)")
            
            if dry_run:
                print(f"\n🔍 DRY RUN MODUS")
                print("=" * 20)
                print(f"Würde {len(one_way_follows)} einseitige Follows entfolgen:")
                print("(Nur Benutzer, die Ihnen NICHT zurückfolgen)")
                for user in sorted(one_way_follows):
                    print(f"  • Würde {user} entfolgen")
            else:
                print(f"\n⚠️  CLEANUP DURCHFÜHREN")
                print("=" * 25)
                print("WICHTIG: Es werden nur Benutzer entfolgt, die Ihnen NICHT zurückfolgen!")
                print("Benutzer, die Ihnen folgen, werden NICHT entfolgt.")
                confirm = input(f"Möchten Sie wirklich {len(one_way_follows)} einseitige Follows entfolgen? (ja/nein): ")
                
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
