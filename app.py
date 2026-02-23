import streamlit as st
import requests
from bs4 import BeautifulSoup
import itertools
import pandas as pd
from streamlit_sortables import sort_items
from betclic_early_win_scraper import scrape_betclic_early_win
from winamax_scraper import scrape_winamax_football
from psel_scraper import scrape_psel_football
import unicodedata
import re
import threading

# --- CONFIG & FONCTIONS SCRAPING ---

import time

# Stockage partagé pour le scraping en arrière-plan (accessible depuis les threads)
_bg_results = {}

def normalize_name(name):
    """Normalise un nom d'équipe pour le matching cross-bookmaker."""
    name = name.lower().strip()
    # Supprimer les accents
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    # Supprimer ponctuation et espaces multiples
    name = re.sub(r'[^a-z0-9 ]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Supprimer les préfixes/suffixes de clubs (FC, AS, AC, SC, etc.)
    noise_words = {'fc', 'as', 'ac', 'sc', 'ss', 'us', 'rc', 'cd', 'cf', 'sl', 'sv', 'fk', 'sk', 'bk', 'if', 'bf', 'vfl', 'vfb', 'tsv', 'bsc', 'bvb', 'ssc', 'afc', 'rcd', 'rsc'}
    words = [w for w in name.split() if w not in noise_words]
    name = ' '.join(words) if words else name
    
    # Expansion des abréviations courantes
    abbrevs = {
        'utd': 'united', 'man': 'manchester', 'atl': 'atletico',
        'st': 'saint', 'ste': 'sainte', 'sp': 'sporting',
        'real': 'real', 'inter': 'inter', 'psv': 'psv',
        'psg': 'paris saint germain', 'om': 'olympique marseille',
        'ol': 'olympique lyonnais', 'asse': 'saint etienne',
        'losc': 'lille', 'ogc': 'nice', 'mhsc': 'montpellier',
        'sco': 'angers', 'srfc': 'rennes',
    }
    words = name.split()
    expanded = [abbrevs.get(w, w) for w in words]
    name = ' '.join(expanded)
    
    return name

def teams_match(name_a, name_b):
    """Vérifie si deux noms d'équipes correspondent (gère les abréviations).
    Chaque mot du nom court doit être un préfixe d'un mot du nom long."""
    words_a = name_a.split()
    words_b = name_b.split()
    # Le plus court doit matcher le plus long
    short, long = (words_a, words_b) if len(words_a) <= len(words_b) else (words_b, words_a)
    if not short:
        return False
    matched = 0
    for sw in short:
        for lw in long:
            if lw.startswith(sw) or sw.startswith(lw):
                matched += 1
                break
    return matched >= len(short)

def find_match_on_book(match_title, book_matches):
    """Trouve un match sur un autre bookmaker par matching de noms."""
    parts = match_title.split(' - ')
    if len(parts) != 2:
        return None
    team1_norm = normalize_name(parts[0])
    team2_norm = normalize_name(parts[1])
    
    for m in book_matches:
        m_parts = m['title'].split(' - ')
        if len(m_parts) != 2:
            continue
        m_t1 = normalize_name(m_parts[0])
        m_t2 = normalize_name(m_parts[1])
        # Match même ordre
        if teams_match(team1_norm, m_t1) and teams_match(team2_norm, m_t2):
            return m
        # Match inversé
        if teams_match(team1_norm, m_t2) and teams_match(team2_norm, m_t1):
            return m
    return None

@st.cache_data(ttl=600)
def scrape_winamax_football_cached(scrape_key=None):
    """Wrapper pour le scraper Winamax (Depend on scrape_key for cache invalidation)."""
    data = scrape_winamax_football()
    if not data:
        raise Exception("Winamax scraping returned empty")
    return data

@st.cache_data(ttl=600)
def scrape_psel_football_cached(scrape_key=None):
    """Wrapper pour le scraper PSEL."""
    data = scrape_psel_football()
    if not data:
        raise Exception("PSEL scraping returned empty")
    return data

@st.cache_data(ttl=600)
def scrape_betclic_early_win_cached(scrape_key=None):
    """Wrapper pour le scraper Selenium."""
    return scrape_betclic_early_win()

# On utilise st.cache_data pour éviter de scraper à chaque interaction
@st.cache_data(ttl=600) # Cache 10 minutes
def scrape_betclic_football_cached(scrape_key=None):
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
        st.session_state.scrape_key = time.time() # Update key on click

if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False
    
if 'scrape_key' not in st.session_state:
    st.session_state.scrape_key = 0 # Default key

if st.session_state.run_analysis:
    matches = []
    
    # Pass cache key to scrapers
    key = st.session_state.scrape_key
    
    if bookmaker == "Winamax":
        with st.spinner('Scraping Winamax (JSON API)...'):
            try:
                matches = scrape_winamax_football_cached(scrape_key=key)
            except:
                matches = []

    elif bookmaker == "PSEL":
        with st.spinner('Scraping Parions Sport En Ligne...'):
            try:
                matches = scrape_psel_football_cached(scrape_key=key)
            except:
                matches = []

    elif bookmaker == "Betclic":
        if early_win:
            with st.spinner('Scraping et Fusion des cotes "Early Win" (Selenium)... Cela peut prendre quelques secondes.'):
                raw_data = scrape_betclic_early_win_cached(scrape_key=key)
                
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
                matches = scrape_betclic_football_cached(scrape_key=key)

    # Lancer le scraping des autres bookmakers en arrière-plan
    def _scrape_other_books(bg_id, bk, k):
        other_bm = [b for b in ["Betclic", "Winamax", "PSEL"] if b != bk]
        result = {}
        for ob in other_bm:
            try:
                if ob == "Winamax":
                    result[ob] = scrape_winamax_football_cached(scrape_key=k)
                elif ob == "PSEL":
                    result[ob] = scrape_psel_football_cached(scrape_key=k)
                elif ob == "Betclic":
                    result[ob] = scrape_betclic_football_cached(scrape_key=k)
            except:
                result[ob] = []
        _bg_results[bg_id] = result
    
    # Démarrer le thread si pas déjà fait pour cette analyse
    bg_key = f"{key}_{bookmaker}"
    if bg_key not in _bg_results:
        t = threading.Thread(target=_scrape_other_books, args=(bg_key, bookmaker, key), daemon=True)
        t.start()

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
            # Stocker la meilleure combinaison en session (reset si nouvelle analyse)
            current_key = st.session_state.scrape_key
            if ('best_combo_list' not in st.session_state 
                or st.session_state.get('last_scrape_key') != current_key
                or st.session_state.get('last_bookmaker') != bookmaker):
                st.session_state.best_combo_list = list(best_combo)
                st.session_state.last_scrape_key = current_key
                st.session_state.last_bookmaker = bookmaker

            st.divider()
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(label="Taux de Conversion", value=f"{best_rate:.2f} %", delta="Excellent" if best_rate > 80 else "Moyen")
                total_fb = sum(d['Mise Freebet (€)'] for d in best_details)
                st.metric(label="Total Freebets Requis", value=f"{total_fb:.2f} €")
                st.metric(label="Gain Net Garanti", value=f"{target_gain:.2f} €")

            with col2:
                st.subheader("Matchs Sélectionnés")
                reorder_mode = st.toggle("🔀 Réorganiser", value=False)
                
                combo_list = st.session_state.best_combo_list
                
                for i, m in enumerate(combo_list):
                    if reorder_mode:
                        c_arrows, c_title = st.columns([0.12, 0.88])
                        with c_arrows:
                            if i > 0:
                                if st.button("⬆", key=f"up_{i}", use_container_width=True):
                                    combo_list[i], combo_list[i-1] = combo_list[i-1], combo_list[i]
                                    st.session_state.best_combo_list = combo_list
                                    st.rerun()
                            else:
                                st.write("")
                            if i < len(combo_list) - 1:
                                if st.button("⬇", key=f"down_{i}", use_container_width=True):
                                    combo_list[i], combo_list[i+1] = combo_list[i+1], combo_list[i]
                                    st.session_state.best_combo_list = combo_list
                                    st.rerun()
                        with c_title:
                            st.markdown(f"**{m['title']}**")
                            cols = st.columns(4)
                            cols[0].caption(f"TJR: {m['tjr']:.2f}%")
                            cols[1].markdown(f"1: **{m['odds_display'][0]}**")
                            cols[2].markdown(f"N: **{m['odds_display'][1]}**")
                            cols[3].markdown(f"2: **{m['odds_display'][2]}**")
                    else:
                        st.markdown(f"**{m['title']}**")
                        cols = st.columns(4)
                        cols[0].caption(f"TJR: {m['tjr']:.2f}%")
                        cols[1].markdown(f"1: **{m['odds_display'][0]}**")
                        cols[2].markdown(f"N: **{m['odds_display'][1]}**")
                        cols[3].markdown(f"2: **{m['odds_display'][2]}**")
                
                ordered_combo = combo_list
            
            # Recalculer les mises avec l'ordre choisi
            _, ordered_details = calculate_conversion(tuple(ordered_combo), target_gain)
            
            st.divider()
            
            df_details = pd.DataFrame(ordered_details)
            
            # Affichage en 3 lignes × 9 colonnes, groupé par résultat du Match 1
            group_labels = [f"Match 1 → 1", f"Match 1 → N", f"Match 1 → 2"]
            groups = [df_details.iloc[i*9:(i+1)*9].reset_index(drop=True) for i in range(3)]
            
            # --- Calculer la colonne rouge (comparaison cross-bookmaker) ---
            red_combo_idx = -1  # index global (0-26) de la combo à placer ailleurs
            best_diff = -999
            best_book_name = ""
            best_primary_odd = 0
            best_other_odd = 0
            labels_list = ["1", "N", "2"]
            indices_list_27 = list(itertools.product(range(3), repeat=3))
            
            other_books_data = _bg_results.get(bg_key, None)
            other_books_ready = other_books_data is not None
            valid_books = {}
            cross_data = {}
            
            if other_books_ready and other_books_data:
                # Trouver les matchs correspondants
                valid_books = {}
                cross_data = {}
                for ob_name, ob_matches in other_books_data.items():
                    found = [find_match_on_book(m['title'], ob_matches) for m in ordered_combo]
                    cross_data[ob_name] = found
                    if all(fm is not None for fm in found):
                        valid_books[ob_name] = found
                
                if valid_books:
                    for idx, indices in enumerate(indices_list_27):
                        primary_odd = 1.0
                        for match_i, outcome_i in enumerate(indices):
                            primary_odd *= ordered_combo[match_i]['odds'][outcome_i]
                        for ob_name, ob_found in valid_books.items():
                            other_odd = 1.0
                            for match_i, outcome_i in enumerate(indices):
                                other_odd *= ob_found[match_i]['odds'][outcome_i]
                            diff = other_odd - primary_odd
                            if diff > best_diff:
                                best_diff = diff
                                red_combo_idx = idx
                                best_book_name = ob_name
                                best_primary_odd = primary_odd
                                best_other_odd = other_odd
            
            # Couleurs par ligne
            row_colors = [
                'rgba(59, 130, 246, 0.25)',   # Issue - bleu
                'rgba(249, 115, 22, 0.25)',   # Cote Totale - orange
                'rgba(34, 197, 94, 0.25)',    # Mise Freebet - vert
            ]
            red_color = 'rgba(239, 68, 68, 0.45)'  # rouge pour la colonne recommandée
            
            for group_idx, (group_df, label) in enumerate(zip(groups, group_labels)):
                st.markdown(f"**{label}**")
                # Construire le HTML du tableau
                html = '<table style="width:100%; border-collapse:collapse; margin-bottom:1rem;">'
                for row_i, row_name in enumerate(["Issue", "Cote Totale", "Mise Freebet"]):
                    html += '<tr>'
                    for j in range(len(group_df)):
                        global_idx = group_idx * 9 + j  # index global 0-26
                        is_red = (global_idx == red_combo_idx)
                        bg = red_color if is_red else row_colors[row_i]
                        
                        if row_name == "Issue":
                            val = group_df.iloc[j]["Issue"]
                        elif row_name == "Cote Totale":
                            if is_red and best_other_odd > 0:
                                val = f"{best_other_odd:.2f}"
                            else:
                                val = f"{group_df.iloc[j]['Cote Totale']:.2f}"
                        else:
                            if is_red and best_other_odd > 1:
                                other_mise = target_gain / (best_other_odd - 1)
                                val = f"{other_mise:.2f} €"
                            else:
                                val = f"{group_df.iloc[j]['Mise Freebet (€)']:.2f} €"
                        
                        html += f'<td style="background:{bg}; border:2px solid rgba(255,255,255,0.2); text-align:center; padding:6px 8px; color:white; font-size:0.9rem;">{val}</td>'
                    html += '</tr>'
                html += '</table>'
                st.markdown(html, unsafe_allow_html=True)
            
            # --- COMPARAISON CROSS-BOOKMAKER ---
            st.divider()
            st.subheader("🔄 Comparaison Cross-Bookmaker")
            
            if not other_books_ready:
                st.info("⏳ Scraping des autres bookmakers en cours...")
                time.sleep(3)
                st.rerun()
            elif not other_books_data:
                st.warning("⚠️ Aucune donnée des autres bookmakers.")
            elif not valid_books:
                st.warning("⚠️ Les 3 matchs sélectionnés n'ont pas été trouvés sur les autres bookmakers.")
                for ob_name, found_matches in cross_data.items():
                    found_names = [fm['title'] if fm else '❌ Non trouvé' for fm in found_matches]
                    st.caption(f"{ob_name} : {', '.join(found_names)}")
            elif red_combo_idx >= 0:
                best_indices = indices_list_27[red_combo_idx]
                best_label = "/".join([labels_list[i] for i in best_indices])
                
                if best_diff > 0:
                    st.success(f"✅ **Meilleur pari à placer ailleurs : {best_label} sur {best_book_name}**")
                else:
                    st.info(f"ℹ️ **Pari avec le moins de perte : {best_label} sur {best_book_name}**")
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Issue", best_label)
                col_b.metric(f"Cote {bookmaker}", f"{best_primary_odd:.2f}")
                col_c.metric(f"Cote {best_book_name}", f"{best_other_odd:.2f}", delta=f"{best_diff:+.2f}")
                
                st.markdown("**Détail des cotes :**")
                for match_i, outcome_i in enumerate(best_indices):
                    m_primary = ordered_combo[match_i]
                    m_other = valid_books[best_book_name][match_i]
                    outcome_lbl = labels_list[outcome_i]
                    st.caption(
                        f"Match {match_i+1} ({m_primary['title']}) → "
                        f"{outcome_lbl} : {bookmaker} **{m_primary['odds'][outcome_i]:.2f}** | "
                        f"{best_book_name} **{m_other['odds'][outcome_i]:.2f}**"
                    )
        else:
            st.warning("Aucune combinaison rentable trouvée.")
else:
    st.info("👈 Cliquez sur 'Lancer l'analyse' dans le menu de gauche pour commencer.")
