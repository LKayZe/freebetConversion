import requests
from bs4 import BeautifulSoup
import time
import cloudscraper

def scrape_psel_football():
    # URL fournie par l'utilisateur
    url = "https://www.enligne.parionssport.fdj.fr/paris-football?titre=Top%20Foot%20Europ%C3%A9en&ids=58535089,58941152,58531076,58532497,58532492,58554102,58545066,58531576,58531497,58531570,58551460,58532401,58551616,58532453,58558744,58532237,58626935,58602842,58529754,58608172,58529890,58529612,58544781,58529747,58530875,58531060,58559084,58576401"
    
    # Headers generic handled by cloudscraper
    try:
        # print(f"🔄 Connexion à PSEL...")
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
        print(f"❌ Erreur connexion PSEL : {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    events = soup.find_all("psel-event-main")
    
    matches_data = []
    
    for event in events:
        # 1. Extraction Titre
        names = []
        scoreboard = event.find("div", class_="psel-scoreboard-inline")
        if scoreboard:
            opponents = scoreboard.find_all("span", class_="psel-opponent__name")
            names = [op.get_text(strip=True) for op in opponents]
        
        if len(names) != 2: continue
        
        title = f"{names[0]} - {names[1]}"
        
        # 2. Extraction Cotes
        odds_vals = []
        outcomes = event.find_all("psel-outcome")
        
        # On attend 3 issues (1, N, 2)
        # Parfois il y a plus d'issues si le dump contient d'autres marchés, mais psel-event-main semble contenir le match card principal
        # L'ordre standard est 1, N, 2 dans le DOM
        
        for out in outcomes:
            val_tag = out.find("span", class_="psel-outcome__data")
            if val_tag:
                # Remplace , par .
                val_str = val_tag.get_text(strip=True).replace(",", ".")
                odds_vals.append(val_str)
        
        # On prend les 3 premières cotes
        if len(odds_vals) >= 3:
            s_o1, s_oN, s_o2 = odds_vals[0], odds_vals[1], odds_vals[2]
            
            try:
                f_o1 = float(s_o1)
                f_oN = float(s_oN)
                f_o2 = float(s_o2)
                
                # Calcul TJR
                implied_prob = (1/f_o1) + (1/f_oN) + (1/f_o2)
                tjr = (1 / implied_prob) * 100
            except:
                f_o1, f_oN, f_o2 = 1.01, 1.01, 1.01
                tjr = 0

            matches_data.append({
                'title': title,
                'odds': [f_o1, f_oN, f_o2],
                'odds_display': [s_o1, s_oN, s_o2], # Strings displayed
                'tjr': tjr
            })

    # Tri par TJR
    matches_data.sort(key=lambda x: x['tjr'], reverse=True)
    
    return matches_data

if __name__ == "__main__":
    data = scrape_psel_football()
    print(f"✅ {len(data)} matchs récupérés PSEL.")
    for m in data[:5]:
        print(f"{m['title']} | {m['odds_display']} | {m['tjr']:.2f}%")
