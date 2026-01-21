import requests
import json
import re
import cloudscraper
import time

# --- IMPORTS SELENIUM (FALLBACK) ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os

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

def get_selenium_source(url):
    """Lance un navigateur headless pour récupérer le code source (Bypass Cloudflare)."""
    print("🚧 Démarrage Selenium (Fallback)...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Config Cloud Linux
    if os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    
    service = None
    if os.path.exists("/usr/bin/chromedriver"):
        service = ChromeService("/usr/bin/chromedriver")
    else:
        try:
             service = ChromeService(ChromeDriverManager().install())
        except:
             service = ChromeService()

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5) # Laisser le temps au JS Cloudflare de passer
        return driver.page_source
    except Exception as e:
        print(f"❌ Erreur Selenium : {e}")
        return None
    finally:
        if driver: driver.quit()

def scrape_winamax_football():
    url = "https://www.winamax.fr/paris-sportifs/sports/1"
    
    html_content = None

    # 1. Tentative Cloudscraper
    print(f"🔄 [1/2] Connexion Cloudscraper à {url}...")
    try:
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        response = scraper.get(url)
        if response.status_code == 200:
             html_content = response.text
        else:
             print(f"⚠️ Cloudscraper status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erreur Cloudscraper : {e}")

    # 2. Fallback Selenium si échec
    if not html_content or "PRELOADED_STATE" not in html_content:
        print("⚠️ Échec Cloudscraper ou données manquantes. Passage à Selenium...")
        html_content = get_selenium_source(url)

    if not html_content:
        print("❌ Échec total de récupération (Cloudscraper & Selenium).")
        return []

    # Extraction
    json_str = extract_winamax_json(html_content)
    if not json_str:
        print("❌ JSON introuvable dans le HTML récupéré.")
        return []

    try:
        data = json.loads(json_str)
    except:
        print("❌ Erreur de lecture du JSON.")
        return []

    # --- PARSING ---
    matches = data.get('matches', {})
    bets = data.get('bets', {})
    odds = data.get('odds', {})      

    matches_data = []

    for match_id, match_info in matches.items():
        if match_info.get('sportId') != 1: continue
        
        match_title = match_info.get('title')
        main_bet_id = match_info.get('mainBetId')
        
        if not main_bet_id: continue
        
        bet_info = bets.get(str(main_bet_id)) or bets.get(int(main_bet_id))
        if not bet_info: continue

        outcome_ids = bet_info.get('outcomes', [])
        if len(outcome_ids) != 3: continue 

        vals = []
        floats = []
        for oid in outcome_ids:
            odd_value = odds.get(str(oid)) or odds.get(int(oid))
            
            if isinstance(odd_value, (int, float)):
                vals.append(str(odd_value))
                floats.append(float(odd_value))
            elif isinstance(odd_value, list):
                vals.append(str(odd_value[0]))
                floats.append(float(odd_value[0]))
            else:
                vals.append("-")

        if len(vals) == 3 and len(floats) == 3:
            try:
                tjr = 1 / ( (1/floats[0]) + (1/floats[1]) + (1/floats[2]) )
                tjr = tjr * 100
            except ZeroDivisionError:
                tjr = 0

            matches_data.append({
                'title': match_title,
                'odds': floats,
                'odds_display': vals,
                'tjr': tjr
            })

    matches_data.sort(key=lambda x: x['tjr'], reverse=True)
    return matches_data

if __name__ == "__main__":
    data = scrape_winamax_football()
    print(f"{'MATCH':<50} | {'1':<6} | {'N':<6} | {'2':<6} | {'TJR':<6}")
    print("-" * 90)
    if data:
        for m in data[:5]:
             print(f"{m['title'][:48]:<50} | {m['odds_display'][0]:<6} | {m['odds_display'][1]:<6} | {m['odds_display'][2]:<6} | {m['tjr']:.2f}%")