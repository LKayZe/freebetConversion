from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def extract_odds_from_page(driver):
    """
    Extracts all matches and odds visible on the current page.
    Returns a dict: { "Team A - Team B": {o1, oN, o2} }
    """
    import re
    
    match_cards = driver.find_elements(By.CSS_SELECTOR, "a.cardEvent")
    if not match_cards:
         match_cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/football-sfootball/')]")
    
    data = {}
    
    for card in match_cards[:30]: # Grab top 30
        try:
            t1 = card.find_element(By.CSS_SELECTOR, "[data-qa='contestant-1-label']").text
            t2 = card.find_element(By.CSS_SELECTOR, "[data-qa='contestant-2-label']").text
            title = f"{t1} - {t2}"
            
            raw_text = card.text
            odds_matches = re.findall(r"(\d+,\d{2})", raw_text)
            
            o1, oN, o2 = "-", "-", "-"
            
            if len(odds_matches) >= 3:
                o1 = odds_matches[0].replace(',', '.')
                oN = odds_matches[1].replace(',', '.')
                o2 = odds_matches[2].replace(',', '.')
            elif len(odds_matches) == 2:
                o1 = odds_matches[0].replace(',', '.')
                o2 = odds_matches[1].replace(',', '.')
                # oN remains "-"
            
            data[title] = {"o1": o1, "oN": oN, "o2": o2}
            
        except:
            continue
            
    return data

def log(msg):
    # Print to console only for cleaner production run
    print(msg)

def scrape_betclic_early_win():
    log("🔄 Initialisation du navigateur (Mode Headless)...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Mode sans interface graphique
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    except Exception as e:
        log(f"❌ Erreur lors de l'initialisation de Chrome: {e}")
        log("Assurez-vous d'avoir Chrome et les drivers installés.")
        return

    url = "https://www.betclic.fr/football-sfootball"
    log(f"🌐 Connexion à {url}...")
    driver.get(url)

    try:
        # 1. Accepter les cookies
        try:
             wait = WebDriverWait(driver, 5)
             cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "popin_tc_privacy_button_2")))
             cookie_btn.click()
             log("🍪 Cookies gérés.")
        except:
             pass 

        # 2. Scrape Standard Odds (AVANT LE CLIC)
        log("📋 Extraction des cotes Standard (1, N, 2)...")
        time.sleep(2) # Wait for initial load
        standard_odds = extract_odds_from_page(driver)
        log(f"✅ {len(standard_odds)} matchs standard trouvés.")

        # 3. Trouver et cliquer sur "Early Win"
        log("⏳ Recherche du filtre 'Early Win'...")
        wait = WebDriverWait(driver, 10)
        early_win_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Early Win') or contains(text(), '2 buts d')]")))
        
        log("✅ Filtre trouvé ! Clic en cours...")
        driver.execute_script("arguments[0].click();", early_win_btn)
        
        # 4. Attendre mise à jour
        time.sleep(3) 

        # 5. Scrape Early Win Odds
        log("📋 Extraction des cotes 'Early Win' (1, 2)...")
        ew_odds = extract_odds_from_page(driver)
        log(f"✅ {len(ew_odds)} matchs Early Win trouvés.")
        
        # 6. Merge
        log("🔄 Fusion des données...")
        final_results = []
        
        for title, info in ew_odds.items():
            # info has o1, o2 (and maybe oN, but we ignore it or it's same)
            # Find matching standard match
            std_info = standard_odds.get(title)
            if std_info:
                # We take Early Win 1 and 2
                ew_1 = info['o1']
                ew_2 = info['o2']
                # We take Standard N
                std_N = std_info['oN']
                
                final_results.append({
                    "title": title,
                    "o1": ew_1,
                    "oN": std_N, # THE MERGE
                    "o2": ew_2
                })
            else:
                log(f"⚠️ Pas de correspondance standard pour : {title}")
        
        log("\n--- RÉSULTATS FINAUX (Early Win 1/2 + Standard N) ---")
        # Return the results 
        return final_results
            
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return []
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    res = scrape_betclic_early_win()
    print(res)
