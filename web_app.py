"""
Application web Flask pour visualiser les tendances YouTube
"""
from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime
from collections import Counter

app = Flask(__name__)

def charger_donnees():
    """Charge les données depuis le fichier JSON"""
    json_file = 'tendances_youtube.json'
    
    if not os.path.exists(json_file):
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        # Essayer de lire ligne par ligne
        videos = []
        with open(json_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    videos.append(json.loads(line.strip().rstrip(',')))
                except:
                    continue
        return videos

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """API pour obtenir les statistiques"""
    videos = charger_donnees()
    
    if not videos:
        return jsonify({
            'total': 0,
            'message': 'Aucune donnée disponible'
        })
    
    # Calculer les statistiques
    total = len(videos)
    pays_count = Counter(v.get('pays', 'Unknown') for v in videos)
    canaux_count = Counter(v.get('canal', 'Unknown') for v in videos)
    
    # Scores psychologiques
    scores = [v.get('score_psychologique', 0) for v in videos if v.get('score_psychologique')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Features moyennes
    longueurs = [v.get('features', {}).get('longueur', 0) for v in videos]
    emojis = [v.get('features', {}).get('nb_emojis', 0) for v in videos]
    hashtags = [v.get('features', {}).get('nb_hashtags', 0) for v in videos]
    exclamations = [v.get('features', {}).get('nb_exclamations', 0) for v in videos]
    questions = [v.get('features', {}).get('nb_questions', 0) for v in videos]
    majuscules = [v.get('features', {}).get('pourcentage_majuscules', 0) for v in videos]
    
    return jsonify({
        'total': total,
        'avg_score': round(avg_score, 2),
        'pays': dict(pays_count.most_common(10)),
        'top_canaux': dict(canaux_count.most_common(10)),
        'features_moyennes': {
            'longueur': round(sum(longueurs) / len(longueurs), 1) if longueurs else 0,
            'emojis': round(sum(emojis) / len(emojis), 2) if emojis else 0,
            'hashtags': round(sum(hashtags) / len(hashtags), 2) if hashtags else 0,
            'exclamations': round(sum(exclamations) / len(exclamations), 2) if exclamations else 0,
            'questions': round(sum(questions) / len(questions), 2) if questions else 0,
            'majuscules': round(sum(majuscules) / len(majuscules), 2) if majuscules else 0
        }
    })

@app.route('/api/videos')
def get_videos():
    """API pour obtenir la liste des vidéos"""
    videos = charger_donnees()
    
    # Trier par score psychologique décroissant
    videos_sorted = sorted(videos, 
                          key=lambda x: x.get('score_psychologique', 0), 
                          reverse=True)
    
    return jsonify(videos_sorted)

@app.route('/api/top/<int:n>')
def get_top_videos(n):
    """API pour obtenir le top N des vidéos"""
    videos = charger_donnees()
    
    # Trier par score psychologique décroissant
    videos_sorted = sorted(videos, 
                          key=lambda x: x.get('score_psychologique', 0), 
                          reverse=True)
    
    return jsonify(videos_sorted[:n])

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Serveur web démarré sur http://localhost:5000")
    print("=" * 80)
    app.run(debug=True, host='0.0.0.0', port=5000)
