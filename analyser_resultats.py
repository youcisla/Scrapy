"""
Script pour analyser les resultats du scraping YouTube.
Affiche des statistiques et le top des titres les plus accrocheurs.
"""

import json
import sys
from collections import Counter
from utiles import TextFeatures


def charger_donnees(fichier='tendances_youtube.json'):
    """Charge les donnees depuis le fichier JSON."""
    try:
        with open(fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ {len(data)} videos chargees depuis {fichier}")
        return data
    except FileNotFoundError:
        print(f"✗ Fichier {fichier} non trouve")
        print("Lancez d'abord le scraping avec :")
        print("  scrapy crawl youtube_trends -o tendances_youtube.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Erreur lors du parsing JSON : {e}")
        sys.exit(1)


def calculer_scores(data):
    """Calcule les scores psychologiques pour chaque video."""
    tf = TextFeatures(use_spacy=False)
    
    for video in data:
        features = video.get('features', {})
        if features:
            video['score_psychologique'] = tf.calculer_score_psychologique(features)
        else:
            video['score_psychologique'] = 0
    
    return data


def afficher_statistiques(data):
    """Affiche des statistiques generales."""
    print("\n" + "="*80)
    print("STATISTIQUES GENERALES".center(80))
    print("="*80)
    
    # Nombre total
    print(f"\nNombre total de videos : {len(data)}")
    
    # Repartition par pays
    pays_count = Counter(video.get('pays', 'Inconnu') for video in data)
    print(f"\nRepartition par pays :")
    for pays, count in pays_count.most_common(10):
        print(f"  - {pays:20} : {count:4} videos")
    
    # Statistiques sur les features
    print(f"\nStatistiques des features :")
    
    longueurs = [v['features']['longueur_caracteres'] for v in data if v.get('features')]
    if longueurs:
        print(f"  - Longueur moyenne des titres : {sum(longueurs)/len(longueurs):.1f} caracteres")
        print(f"  - Titre le plus court : {min(longueurs)} caracteres")
        print(f"  - Titre le plus long : {max(longueurs)} caracteres")
    
    exclamations = sum(v['features']['nb_exclamations'] for v in data if v.get('features'))
    interrogations = sum(v['features']['nb_interrogations'] for v in data if v.get('features'))
    emojis = sum(v['features']['nb_emojis'] for v in data if v.get('features'))
    hashtags = sum(v['features']['nb_hashtags'] for v in data if v.get('features'))
    
    print(f"  - Total exclamations : {exclamations}")
    print(f"  - Total interrogations : {interrogations}")
    print(f"  - Total emojis : {emojis}")
    print(f"  - Total hashtags : {hashtags}")
    
    # Langues
    langues = Counter(v['features']['langue_detectee'] for v in data if v.get('features'))
    print(f"\nRepartition par langue :")
    for langue, count in langues.items():
        print(f"  - {langue:10} : {count:4} videos ({count/len(data)*100:.1f}%)")


def afficher_top_titres(data, top_n=10):
    """Affiche les top N titres avec les scores les plus eleves."""
    print("\n" + "="*80)
    print(f"TOP {top_n} DES TITRES LES PLUS ACCROCHEURS".center(80))
    print("="*80)
    
    # Tri par score psychologique
    data_sorted = sorted(data, key=lambda x: x.get('score_psychologique', 0), reverse=True)
    
    for i, video in enumerate(data_sorted[:top_n], 1):
        score = video.get('score_psychologique', 0)
        titre = video.get('titre', 'N/A')
        pays = video.get('pays', 'N/A')
        features = video.get('features', {})
        
        print(f"\n{i}. Score : {score:.2f}/100")
        print(f"   Titre : {titre}")
        print(f"   URL : {video.get('url', 'N/A')}")
        print(f"   Pays : {pays}")
        
        if features:
            print(f"   Details :")
            print(f"     • {features.get('longueur_caracteres', 0)} caracteres, {features.get('longueur_mots', 0)} mots")
            print(f"     • Exclamations: {features.get('nb_exclamations', 0)} | Interrogations: {features.get('nb_interrogations', 0)}")
            print(f"     • Emojis: {features.get('nb_emojis', 0)} | Hashtags: {features.get('nb_hashtags', 0)}")
            print(f"     • Majuscules: {features.get('nb_majuscules', 0)} ({features.get('ratio_majuscules', 0):.1%})")
            print(f"     • Langue: {features.get('langue_detectee', 'N/A')}")
        
        print("-" * 80)


def afficher_categories_speciales(data):
    """Affiche des categories speciales de titres."""
    print("\n" + "="*80)
    print("CATEGORIES SPECIALES".center(80))
    print("="*80)
    
    # Titres avec le plus d'exclamations
    exclamations = [v for v in data if v.get('features', {}).get('nb_exclamations', 0) > 0]
    exclamations_sorted = sorted(exclamations, key=lambda x: x['features']['nb_exclamations'], reverse=True)
    
    print(f"\nTitres avec le plus d'exclamations (top 3) :")
    for i, video in enumerate(exclamations_sorted[:3], 1):
        nb = video['features']['nb_exclamations']
        print(f"  {i}. ({nb}!) {video['titre'][:80]}")
    
    # Titres avec le plus d'emojis
    emojis = [v for v in data if v.get('features', {}).get('nb_emojis', 0) > 0]
    emojis_sorted = sorted(emojis, key=lambda x: x['features']['nb_emojis'], reverse=True)
    
    print(f"\nTitres avec le plus d'emojis (top 3) :")
    for i, video in enumerate(emojis_sorted[:3], 1):
        nb = video['features']['nb_emojis']
        print(f"  {i}. ({nb} emojis) {video['titre'][:80]}")
    
    # Titres avec le plus de hashtags
    hashtags = [v for v in data if v.get('features', {}).get('nb_hashtags', 0) > 0]
    hashtags_sorted = sorted(hashtags, key=lambda x: x['features']['nb_hashtags'], reverse=True)
    
    print(f"\nTitres avec le plus de hashtags (top 3) :")
    for i, video in enumerate(hashtags_sorted[:3], 1):
        nb = video['features']['nb_hashtags']
        print(f"  {i}. ({nb} hashtags) {video['titre'][:80]}")
    
    # Titres tout en majuscules
    majuscules = [v for v in data if v.get('features', {}).get('ratio_majuscules', 0) > 0.8]
    
    print(f"\nTitres quasi tout en majuscules (top 3) :")
    for i, video in enumerate(majuscules[:3], 1):
        ratio = video['features']['ratio_majuscules']
        print(f"  {i}. ({ratio:.0%} maj.) {video['titre'][:80]}")


def main():
    """Fonction principale."""
    import sys
    
    # Fichier a analyser
    fichier = 'tendances_youtube.json'
    if len(sys.argv) > 1:
        fichier = sys.argv[1]
    
    print("="*80)
    print("ANALYSEUR DE TENDANCES YOUTUBE".center(80))
    print("="*80)
    
    # Chargement des donnees
    data = charger_donnees(fichier)
    
    # Calcul des scores
    print("Calcul des scores psychologiques...")
    data = calculer_scores(data)
    
    # Affichage des analyses
    afficher_statistiques(data)
    afficher_top_titres(data, top_n=10)
    afficher_categories_speciales(data)
    
    print("\n" + "="*80)
    print("FIN DE L'ANALYSE".center(80))
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
