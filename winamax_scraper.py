import requests
import json

def extract_winamax_json(html_text):
    """Extraction robuste du JSON."""
    prefix = "var PRELOADED_STATE = "
    start_index = html_text.find(prefix)
    if start_index == -1: return None
    start_index += len(prefix)
    brace_count = 0
    in_string = False
    escape = False
    for i in range(start_index, len(html_text)):
        char = html_text[i]
        if char == '"' and not escape: in_string = not in_string
        if char == '\\' and not escape: escape = True
        else: escape = False
        if not in_string:
            if char == '{': brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0: return html_text[start_index:i+1]
    return None

def scrape_winamax_football():
    url = "https://www.winamax.fr/paris-sportifs/sports/1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://www.winamax.fr/paris-sportifs',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    print(f"🔄 Connexion à {url}...")
    try:
        response = requests.get(url, headers=headers)
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