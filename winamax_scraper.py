import requests
import json
import re
import cloudscraper

def scrape_winamax_football():
    url = "https://www.winamax.fr/paris-sportifs/sports/1"
    
    print(f"🔄 Connexion à {url} (via Cloudscraper)...")
    try:
        # Configuration spécifique pour mieux imiter un navigateur de bureau
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    json_str = extract_winamax_json(response.text)
    if not json_str:
        print("❌ Impossible de trouver les données.")
        return

    try:
        data = json.loads(json_str)
    except:
        print("❌ Erreur de lecture du JSON.")
        return

    # --- C'EST ICI QUE TOUT SE JOUE ---
    matches = data.get('matches', {})
    bets = data.get('bets', {})
    outcomes = data.get('outcomes', {}) # Les Noms (ex: Atalanta)
    odds = data.get('odds', {})         # Les Cotes (ex: 1.50)

    # Si le dictionnaire 'odds' est vide, on affiche les clés pour debug
    if not odds:
        print("⚠️ Attention : Le tiroir 'odds' semble vide ou introuvable.")
        print(f"Clés disponibles dans data : {list(data.keys())}")
        
    print(f"✅ Données chargées : {len(matches)} matchs, {len(odds)} cotes disponibles.\n")

    matches_data = []

    for match_id, match_info in matches.items():
        if match_info.get('sportId') != 1: continue
        
        match_title = match_info.get('title')
        main_bet_id = match_info.get('mainBetId')
        
        if not main_bet_id: continue
        
        # On gère le cas où l'ID est un int ou un str
        bet_info = bets.get(str(main_bet_id)) or bets.get(int(main_bet_id))
        
        if not bet_info: continue

        outcome_ids = bet_info.get('outcomes', [])
        if len(outcome_ids) != 3: continue 

        # Récupération des cotes via le nouveau dictionnaire 'odds'
        vals = []
        floats = [] # Pour le calcul du TJR
        for oid in outcome_ids:
            # On cherche la cote dans le dictionnaire 'odds' avec l'ID de l'issue
            odd_value = odds.get(str(oid)) or odds.get(int(oid))
            
            # Parfois la cote est juste un chiffre, parfois un objet, on sécurise
            if isinstance(odd_value, (int, float)):
                vals.append(str(odd_value))
                floats.append(float(odd_value))
            elif isinstance(odd_value, list):
                vals.append(str(odd_value[0])) # Parfois [cote, variation]
                floats.append(float(odd_value[0]))
            else:
                vals.append("-")

        if len(vals) == 3 and len(floats) == 3:
            # Calcul du TJR : 1 / (1/c1 + 1/cN + 1/c2)
            try:
                tjr = 1 / ( (1/floats[0]) + (1/floats[1]) + (1/floats[2]) )
                tjr = tjr * 100 # En pourcentage
            except ZeroDivisionError:
                tjr = 0

            matches_data.append({
                'title': match_title,
                'odds': floats,
                'odds_display': vals,
                'tjr': tjr
            })

    # Tri par TJR décroissant
    matches_data.sort(key=lambda x: x['tjr'], reverse=True)
    
    return matches_data

if __name__ == "__main__":
    data = scrape_winamax_football()
    print(f"{'MATCH':<50} | {'1':<6} | {'N':<6} | {'2':<6} | {'TJR':<6}")
    print("-" * 90)
    if data:
        for m in data[:5]:
             print(f"{m['title'][:48]:<50} | {m['odds_display'][0]:<6} | {m['odds_display'][1]:<6} | {m['odds_display'][2]:<6} | {m['tjr']:.2f}%")