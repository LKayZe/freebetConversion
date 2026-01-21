import streamlit as st
import requests
from bs4 import BeautifulSoup
import itertools
import pandas as pd
from betclic_early_win_scraper import scrape_betclic_early_win
from winamax_scraper import scrape_winamax_football
from psel_scraper import scrape_psel_football

# --- CONFIG & FONCTIONS SCRAPING ---

@st.cache_data(ttl=600)
def scrape_winamax_football_cached():
    """Wrapper pour le scraper Winamax."""
    return scrape_winamax_football()

@st.cache_data(ttl=600)
def scrape_psel_football_cached():
    """Wrapper pour le scraper PSEL."""
    return scrape_psel_football()

@st.cache_data(ttl=600)
def scrape_betclic_early_win_cached():
    """Wrapper pour le scraper Selenium."""
    return scrape_betclic_early_win()

# On utilise st.cache_data pour éviter de scraper à chaque interaction
@st.cache_data(ttl=600) # Cache 10 minutes
def scrape_betclic_football_cached():
    """Récupère les données et retourne une liste de dicts avec cotes et TJR."""
    url = "https://www.betclic.fr/football-sfootball"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    match_cards = soup.select('sports-events-event-card')
    if not match_cards: match_cards = soup.select('.cardEvent')

    matches_data = []

    for card in match_cards:
        try:
            t1_elem = card.select_one('[data-qa="contestant-1-label"]')
            t2_elem = card.select_one('[data-qa="contestant-2-label"]')
            if not t1_elem or not t2_elem: continue
            
            t1 = t1_elem.get_text(strip=True)
            t2 = t2_elem.get_text(strip=True)
            match_title = f"{t1} - {t2}"

            buttons_wrapper = card.select_one('bcdk-bet-button-wrapper')
            if not buttons_wrapper: continue
            odds_buttons = buttons_wrapper.select('button')
            if len(odds_buttons) < 3: continue

            floats = []
            values_display = []
            for i in range(3):
                btn = odds_buttons[i]
                labels = btn.select('.btn_label')
                odd_str = None
                for lbl in labels:
                    txt = lbl.get_text(strip=True)
                    if any(c.isdigit() for c in txt) and ',' in txt:
                        odd_str = txt
                        break
                if not odd_str: break
                f_val = float(odd_str.replace(',', '.'))
                floats.append(f_val)
                values_display.append(odd_str)
            
            if len(floats) == 3:
                implied_prob = sum(1/f for f in floats)
                tjr = (1 / implied_prob) * 100
                matches_data.append({
                    'title': match_title,
                    'odds': floats, # [1, N, 2]
                    'odds_display': values_display,
                    'tjr': tjr
                })

        except Exception as e:
            continue

    matches_data.sort(key=lambda x: x['tjr'], reverse=True)
    return matches_data

def calculate_conversion(triplet, target_gain):
    """Calcule le taux de conversion optimal pour un triplet de matchs."""
    odds_lists = [m['odds'] for m in triplet]
    combinations = list(itertools.product(*odds_lists))
    
    total_stake = 0
    stakes = []
    
    valid_combo = True
    
    indices_list = list(itertools.product(range(3), repeat=3))

    for idx, combo in enumerate(combinations):
        total_odd = combo[0] * combo[1] * combo[2]
        
        if total_odd <= 1:
            valid_combo = False
            break
            
        req_stake_k = target_gain / (total_odd - 1)
        total_stake += req_stake_k
        
        # Format label 1 N 2
        labels = ["1", "N", "2"]
        indices = indices_list[idx]
        outcome_label = "/".join([labels[i] for i in indices])

        stakes.append({
            'Issue': outcome_label,
            'Cote Totale': total_odd,
            'Mise Freebet (€)': req_stake_k
        })
        
    if not valid_combo or total_stake == 0:
        return 0.0, []
        
    conversion_rate = (target_gain / total_stake) * 100
    return conversion_rate, stakes

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Freebet Optimizer", page_icon="💸", layout="wide")

st.title("💸 Freebet Optimizer")
st.markdown("Optimisez la conversion de vos freebets en cash garanti via une stratégie de couverture sur 3 matchs.")

# Sidebar configuration
with st.sidebar:
    st.header("Paramètres")
    
    # Choix du Bookmaker
    bookmaker = st.selectbox("Bookmaker", ["Betclic", "Winamax", "PSEL"])
    
    target_gain = st.number_input("Gain Net Visé (€)", min_value=1.0, value=100.0, step=10.0)
    top_n = st.slider("Matchs à analyser (Top TJR)", min_value=5, max_value=40, value=15)
    
    early_win = False
    if bookmaker == "Betclic":
        early_win = st.checkbox("Option 'Early Win' (2 buts d'avance)")
        if early_win:
            st.caption("ℹ️ Applique -0.05 sur les cotes 1 et 2.")

    if st.button("Lancer l'analyse", type="primary"):
        st.session_state.run_analysis = True

if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

if st.session_state.run_analysis:
    matches = []
    
    if bookmaker == "Winamax":
        with st.spinner('Scraping Winamax (JSON API)...'):
            matches = scrape_winamax_football_cached()

    elif bookmaker == "PSEL":
        with st.spinner('Scraping Parions Sport En Ligne...'):
            matches = scrape_psel_football_cached()

    elif bookmaker == "Betclic":
        if early_win:
            with st.spinner('Scraping et Fusion des cotes "Early Win" (Selenium)... Cela peut prendre quelques secondes.'):
                raw_data = scrape_betclic_early_win_cached()
                
            if not raw_data:
                st.error("Échec du scraping Early Win (Vérifiez les drivers/internet).")
            else:
                 # Conversion des données Selenium vers format App
                 for item in raw_data:
                    try:
                        t = item['title']
                        # Gestion sécurisée des cotes
                        def safe_float(val):
                            if val in [None, '-', '']: return 1.01
                            try: return float(val)
                            except: return 1.01
                        
                        o1 = safe_float(item.get('o1'))
                        oN = safe_float(item.get('oN'))
                        o2 = safe_float(item.get('o2'))
                        
                        floats = [o1, oN, o2]
                        
                        # Calcul TJR
                        try:
                            implied_prob = sum(1/f for f in floats)
                            tjr = (1 / implied_prob) * 100
                        except: tjr = 0
                        
                        matches.append({
                            'title': t,
                            'odds': floats,
                            'odds_display': [str(o1), str(oN), str(o2)],
                            'tjr': tjr
                        })
                    except Exception as e:
                        continue
                 
                 matches.sort(key=lambda x: x['tjr'], reverse=True)

        else:
            with st.spinner('Scraping Betclic...'):
                matches = scrape_betclic_football_cached()
    
    if not matches:
        st.error("Aucun match trouvé ou erreur de scraping.")
    else:

        st.success(f"{len(matches)} matchs récupérés.")
        
        # Filtrer Top N
        top_matches = matches[:top_n]
        st.info(f"Analyse des {len(top_matches)} meilleurs matchs (TJR moyen: {sum(m['tjr'] for m in top_matches)/len(top_matches):.2f}%)")

        with st.spinner('Calcul de la meilleure combinaison...'):
            best_rate = -1.0
            best_combo = None
            best_details = []
            
            triplets = itertools.combinations(top_matches, 3)
            
            # Progress bar for optimization (optional if too slow)
            # count = 0
            # total_combos = (len(top_matches) * (len(top_matches)-1) * (len(top_matches)-2)) / 6
            # my_bar = st.progress(0)
            
            for triplet in triplets:
                rate, details = calculate_conversion(triplet, target_gain)
                if rate > best_rate:
                    best_rate = rate
                    best_combo = triplet
                    best_details = details
        
        if best_combo:
            st.divider()
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(label="Taux de Conversion", value=f"{best_rate:.2f} %", delta="Excellent" if best_rate > 80 else "Moyen")
                total_fb = sum(d['Mise Freebet (€)'] for d in best_details)
                st.metric(label="Total Freebets Requis", value=f"{total_fb:.2f} €")
                st.metric(label="Gain Net Garanti", value=f"{target_gain:.2f} €")

            with col2:
                st.subheader("Matchs Sélectionnés")
                for m in best_combo:
                    st.markdown(f"**{m['title']}**")
                    cols = st.columns(4)
                    cols[0].caption(f"TJR: {m['tjr']:.2f}%")
                    cols[1].markdown(f"1: **{m['odds_display'][0]}**")
                    cols[2].markdown(f"N: **{m['odds_display'][1]}**")
                    cols[3].markdown(f"2: **{m['odds_display'][2]}**")
            
            st.divider()
            st.subheader("Répartition des Mises (27 combinaisons)")
            
            df_details = pd.DataFrame(best_details)
            # Format des colonnes
            st.dataframe(
                df_details.style.format({
                    "Cote Totale": "{:.2f}", 
                    "Mise Freebet (€)": "{:.2f}"
                }).background_gradient(subset=["Mise Freebet (€)"], cmap="Greens"),
                use_container_width=True
            )
        else:
            st.warning("Aucune combinaison rentable trouvée.")
else:
    st.info("👈 Cliquez sur 'Lancer l'analyse' dans le menu de gauche pour commencer.")
