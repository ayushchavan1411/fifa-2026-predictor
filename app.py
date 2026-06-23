import streamlit as st
import pandas as pd
import plotly.express as px
import json
import time
from datetime import datetime
from translations import translate
from fifa_agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from historical_data import load_all_historical_data, get_team_historical_stats, get_head_to_head

# ---------- LANGUAGE ----------
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'
lang_options = {"English": "en", "हिन्दी (Hindi)": "hi", "తెలుగు (Telugu)": "te"}
lang_display = st.sidebar.selectbox("भाषा / Language", list(lang_options.keys()), index=list(lang_options.values()).index(st.session_state.lang))
new_lang = lang_options[lang_display]
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    st.rerun()
def _(text): return translate(text, st.session_state.lang)

st.set_page_config(page_title=_("🏆 FIFA World Cup 2026 Predictor"), page_icon="⚽", layout="wide")

# ---------- DATA LOADING ----------
@st.cache_data
def load_worldcup_data():
    try:
        with open('data/worldcup.json/2026/worldcup.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("World Cup data file not found.")
        return None

@st.cache_data
def load_squads_data():
    try:
        with open('data/worldcup.json/2026/worldcup.squads.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("Squads file not found.")
        return None

@st.cache_data
def load_historical_data():
    matches = load_all_historical_data('data/historical_worldcup')
    stats = get_team_historical_stats(matches)
    return matches, stats

WORLDCUP_DATA = load_worldcup_data()
SQUADS_DATA = load_squads_data()

# Load historical data with fallback
try:
    HISTORICAL_MATCHES, HISTORICAL_STATS = load_historical_data()
except Exception as e:
    st.warning(f"Historical data error: {e}. Using fallback data.")
    HISTORICAL_MATCHES, HISTORICAL_STATS = [], {}

def get_matches_from_data():
    if WORLDCUP_DATA is None:
        return []
    return WORLDCUP_DATA.get('matches', [])

@st.cache_data
def get_cached_matches():
    return get_matches_from_data()

def get_groups_from_matches(matches):
    groups = {}
    for m in matches:
        group = m.get('group', 'Unknown')
        if group not in groups:
            groups[group] = set()
        groups[group].add(m.get('team1', ''))
        groups[group].add(m.get('team2', ''))
    return {g: list(teams - {''}) for g, teams in groups.items() if teams}

# ---------- PLAYER STATS ----------
@st.cache_data
def build_player_stats():
    matches = get_cached_matches()
    goalscorers = {}
    for m in matches:
        for goal in m.get('goals1', []):
            name = goal.get('name')
            if name:
                goalscorers[name] = goalscorers.get(name, 0) + 1
        for goal in m.get('goals2', []):
            name = goal.get('name')
            if name:
                goalscorers[name] = goalscorers.get(name, 0) + 1

    player_details = {}
    if SQUADS_DATA and isinstance(SQUADS_DATA, list):
        for team_entry in SQUADS_DATA:
            team_name = team_entry.get('name', 'Unknown')
            for player in team_entry.get('players', []):
                name = player.get('name')
                if name:
                    club = player.get('club', {})
                    club_name = club.get('name', 'Unknown') if isinstance(club, dict) else 'Unknown'
                    player_details[name] = {
                        'team': team_name,
                        'position': player.get('pos', 'Unknown'),
                        'club': club_name,
                        'number': player.get('number', ''),
                        'dob': player.get('date_of_birth', '')
                    }

    all_names = set(goalscorers.keys()) | set(player_details.keys())
    stats = []
    for name in all_names:
        details = player_details.get(name, {})
        stats.append({
            'Player': name,
            'Team': details.get('team', 'Unknown'),
            'Position': details.get('position', 'Unknown'),
            'Club': details.get('club', 'Unknown'),
            'Goals': goalscorers.get(name, 0)
        })
    df = pd.DataFrame(stats)
    df = df.sort_values('Goals', ascending=False)
    return df

def search_player_stats(query):
    df = build_player_stats()
    if df.empty:
        return None
    results = df[df['Player'].str.contains(query, case=False, na=False)]
    if results.empty:
        return None
    return results.iloc[0].to_dict()

# ---------- TEAM PERFORMANCE STATS (2026) ----------
def get_team_performance_2026():
    matches = get_cached_matches()
    groups = get_groups_from_matches(matches)
    perf = {}
    for group_name, teams in groups.items():
        for team in teams:
            perf[team] = {'gf': 0, 'ga': 0, 'points': 0, 'played': 0}
    for m in matches:
        score_obj = m.get('score', {})
        if score_obj and 'ft' in score_obj:
            ft = score_obj['ft']
            if isinstance(ft, list) and len(ft) == 2:
                team1 = m.get('team1', '')
                team2 = m.get('team2', '')
                s1, s2 = ft[0], ft[1]
                if team1 in perf and team2 in perf:
                    perf[team1]['gf'] += s1
                    perf[team1]['ga'] += s2
                    perf[team1]['played'] += 1
                    perf[team2]['gf'] += s2
                    perf[team2]['ga'] += s1
                    perf[team2]['played'] += 1
                    if s1 > s2:
                        perf[team1]['points'] += 3
                    elif s1 < s2:
                        perf[team2]['points'] += 3
                    else:
                        perf[team1]['points'] += 1
                        perf[team2]['points'] += 1
    return perf

# ---------- SQUAD COMPARISON ----------
def get_player_quality_score(player, position):
    score = 50
    top_clubs = {
        'Real Madrid': 20, 'Barcelona': 19, 'Bayern Munich': 19, 'Manchester City': 19,
        'Liverpool': 18, 'PSG': 18, 'Chelsea': 17, 'Manchester United': 17,
        'Arsenal': 16, 'Tottenham': 15, 'AC Milan': 15, 'Inter Milan': 15,
        'Juventus': 14, 'Borussia Dortmund': 14, 'Atletico Madrid': 14
    }
    club = player.get('club', '')
    for club_name, bonus in top_clubs.items():
        if club_name.lower() in club.lower():
            score += bonus
            break
    if position in ['FW', 'forward', 'Forward']:
        score += player.get('Goals', 0) * 3
    elif position in ['MF', 'midfielder', 'Midfielder']:
        score += player.get('Goals', 0) * 2
    elif position in ['DF', 'defender', 'Defender']:
        score += player.get('Goals', 0) * 1
    return min(score, 100)

def compare_squads(team1, team2, player_stats_df):
    players1 = player_stats_df[player_stats_df['Team'] == team1]
    players2 = player_stats_df[player_stats_df['Team'] == team2]
    positions = ['FW', 'MF', 'DF', 'GK']
    results = {}
    for pos in positions:
        p1 = players1[players1['Position'] == pos]
        p2 = players2[players2['Position'] == pos]
        p1_scores = [get_player_quality_score(row, pos) for _, row in p1.iterrows()]
        p2_scores = [get_player_quality_score(row, pos) for _, row in p2.iterrows()]
        p1_avg = sum(p1_scores) / len(p1_scores) if p1_scores else 0
        p2_avg = sum(p2_scores) / len(p2_scores) if p2_scores else 0
        results[pos] = {
            'team1_count': len(p1),
            'team1_avg': p1_avg,
            'team2_count': len(p2),
            'team2_avg': p2_avg,
            'advantage': 'team1' if p1_avg > p2_avg else 'team2' if p2_avg > p1_avg else 'equal'
        }
    total_team1 = sum(r['team1_avg'] for r in results.values())
    total_team2 = sum(r['team2_avg'] for r in results.values())
    squad_advantage = 'team1' if total_team1 > total_team2 else 'team2' if total_team2 > total_team1 else 'equal'
    return results, squad_advantage, total_team1, total_team2

# ---------- WIN PROBABILITY (Comprehensive) ----------
def calculate_win_probability(team1, team2, include_details=False):
    hist_stats = HISTORICAL_STATS
    t1_hist = hist_stats.get(team1, {'win_pct': 0.4, 'goals_per_match': 1.0})
    t2_hist = hist_stats.get(team2, {'win_pct': 0.4, 'goals_per_match': 1.0})
    hist_win_pct1 = t1_hist.get('win_pct', 0.4)
    hist_win_pct2 = t2_hist.get('win_pct', 0.4)

    h2h = get_head_to_head(HISTORICAL_MATCHES, team1, team2)
    total_h2h = h2h['total']
    if total_h2h > 0:
        h2h_win1 = h2h['team1_wins'] / total_h2h
        h2h_win2 = h2h['team2_wins'] / total_h2h
        h2h_draw = h2h['draws'] / total_h2h
    else:
        h2h_win1 = h2h_win2 = h2h_draw = 0.33

    perf_2026 = get_team_performance_2026()
    t1_2026 = perf_2026.get(team1, {'played': 0, 'points': 0, 'gf': 0, 'ga': 0})
    t2_2026 = perf_2026.get(team2, {'played': 0, 'points': 0, 'gf': 0, 'ga': 0})

    def get_form_score(team_data):
        played = team_data['played']
        if played == 0:
            return 0.4
        pts_per_match = team_data['points'] / played
        gf_per_match = team_data['gf'] / played
        return 0.6 * (pts_per_match / 3) + 0.2 * (gf_per_match / 3) + 0.2 * 0.5

    form1 = get_form_score(t1_2026)
    form2 = get_form_score(t2_2026)

    player_stats = build_player_stats()
    squad_results, squad_advantage, squad1_total, squad2_total = compare_squads(team1, team2, player_stats)
    total_squad = squad1_total + squad2_total
    if total_squad > 0:
        squad_win1 = squad1_total / total_squad
        squad_win2 = squad2_total / total_squad
    else:
        squad_win1 = squad_win2 = 0.5

    weights = {'historical': 0.35, 'head_to_head': 0.25, 'squad': 0.20, 'form': 0.20}
    draw_prob = 0.2 + (h2h_draw - 0.33) * 0.3 if total_h2h > 0 else 0.2

    p1_hist = hist_win_pct1 * (1 - draw_prob)
    p2_hist = hist_win_pct2 * (1 - draw_prob)
    p1_h2h = h2h_win1 * (1 - draw_prob)
    p2_h2h = h2h_win2 * (1 - draw_prob)
    p1_form = form1 * (1 - draw_prob)
    p2_form = form2 * (1 - draw_prob)
    p1_squad = squad_win1 * (1 - draw_prob)
    p2_squad = squad_win2 * (1 - draw_prob)

    final_p1 = (weights['historical'] * p1_hist +
                weights['head_to_head'] * p1_h2h +
                weights['squad'] * p1_squad +
                weights['form'] * p1_form)
    final_p2 = (weights['historical'] * p2_hist +
                weights['head_to_head'] * p2_h2h +
                weights['squad'] * p2_squad +
                weights['form'] * p2_form)
    final_draw = 1 - final_p1 - final_p2

    result = {
        'team1': team1,
        'team1_win': round(final_p1 * 100, 1),
        'team2': team2,
        'team2_win': round(final_p2 * 100, 1),
        'draw': round(final_draw * 100, 1),
        'historical_win_pct1': round(hist_win_pct1 * 100, 1),
        'historical_win_pct2': round(hist_win_pct2 * 100, 1),
        'h2h_wins1': h2h['team1_wins'],
        'h2h_wins2': h2h['team2_wins'],
        'h2h_draws': h2h['draws'],
        'h2h_total': h2h['total'],
        'form1': round(form1 * 100, 1),
        'form2': round(form2 * 100, 1),
        'squad_score1': round(squad1_total, 1),
        'squad_score2': round(squad2_total, 1),
        'squad_advantage': squad_advantage,
        'position_comparison': squad_results
    }
    return result

# ---------- AI SETTINGS ----------
st.sidebar.title(_("🤖 AI Settings"))
ai_provider = st.sidebar.selectbox(_("AI Provider"), ["None", "ADK Agent", "Ollama (Local)", "OpenAI (BYOK)"])
ollama_endpoint = ollama_model = openai_client = None
if ai_provider == "Ollama (Local)":
    ollama_endpoint = st.sidebar.text_input(_("Ollama Endpoint"), "http://127.0.0.1:11434")
    ollama_model = st.sidebar.text_input(_("Model Name"), "tinyllama")
    if st.sidebar.button(_("Test Ollama Connection")):
        try:
            import requests
            r = requests.post(f"{ollama_endpoint}/api/generate", json={"model": ollama_model, "prompt": "Hi"}, timeout=10)
            if r.status_code == 200:
                st.sidebar.success(_("✅ Ollama reachable!"))
            else:
                st.sidebar.error(_("❌ Connection failed"))
        except Exception as e:
            st.sidebar.error(_("❌ Cannot reach Ollama: ") + str(e))
elif ai_provider == "OpenAI (BYOK)":
    openai_api_key = st.sidebar.text_input(_("OpenAI API Key"), type="password")
    if openai_api_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            st.sidebar.success(_("✅ API key accepted"))
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# ---------- AI CALL ----------
def call_ai(prompt, context=""):
    if ai_provider == "ADK Agent":
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
        try:
            session_service = InMemorySessionService()
            runner = Runner(
                agent=root_agent,
                session_service=session_service,
                app_name="fifa_predictor"
            )
            session_id = "streamlit_session"
            result = runner.run(
                session_id=session_id,
                input=full_prompt
            )
            if hasattr(result, 'content'):
                return result.content
            elif hasattr(result, 'text'):
                return result.text
            elif hasattr(result, 'response'):
                return result.response
            else:
                return str(result)
        except Exception as e:
            return f"Agent error: {e}"
    elif ai_provider == "Ollama (Local)" and ollama_endpoint and ollama_model:
        try:
            import requests
            payload = {"model": ollama_model, "prompt": prompt, "stream": False}
            r = requests.post(f"{ollama_endpoint}/api/generate", json=payload, timeout=30)
            if r.status_code == 200:
                return r.json().get("response", _("No response"))
            else:
                return f"Ollama error: {r.status_code}"
        except Exception as e:
            return f"Error: {e}"
    elif ai_provider == "OpenAI (BYOK)" and openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": _("You are a football expert assistant.")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI error: {e}"
    else:
        return _("AI not configured.")

# ---------- WORLD CUP MATCHES ----------
def get_worldcup_matches(show_probabilities=False):
    matches = get_cached_matches()
    match_list = []
    for m in matches:
        team1 = m.get('team1', 'TBD')
        team2 = m.get('team2', 'TBD')
        group = m.get('group', 'Unknown')
        date = m.get('date', '')
        time_str = m.get('time', '')
        ground = m.get('ground', '')
        score_obj = m.get('score', {})
        if score_obj and 'ft' in score_obj:
            ft = score_obj['ft']
            if isinstance(ft, list) and len(ft) == 2:
                s1, s2 = ft[0], ft[1]
                status_text = _("✅ FINISHED")
                score = f"{s1}-{s2}"
                time_text = _("Final")
            else:
                status_text = _("✅ FINISHED")
                score = "-"
                time_text = _("Final")
        elif score_obj and 'ht' in score_obj:
            ht = score_obj['ht']
            if isinstance(ht, list) and len(ht) == 2:
                s1, s2 = ht[0], ht[1]
                status_text = _("🟢 LIVE")
                score = f"{s1}-{s2} (HT)"
                time_text = _("In Progress")
            else:
                status_text = _("🟢 LIVE")
                score = "-"
                time_text = _("In Progress")
        else:
            status_text = _("📋 UPCOMING")
            score = "-"
            time_text = f"{date} {time_str}" if time_str else date

        row = {
            _("Match"): f"{team1} vs {team2}",
            _("Status"): status_text,
            _("Score"): score,
            _("Time"): time_text,
            _("Stage"): _(f"Group {group}"),
            _("Venue"): ground
        }
        if show_probabilities:
            prob = calculate_win_probability(team1, team2)
            row[_("Win %")] = f"{prob['team1_win']}% / {prob['draw']}% / {prob['team2_win']}%"
        match_list.append(row)
    return match_list

# ---------- WORLD CUP STANDINGS ----------
def get_worldcup_standings():
    matches = get_cached_matches()
    groups = get_groups_from_matches(matches)
    standings = {}
    for group_name, teams in groups.items():
        for team in teams:
            standings[(group_name, team)] = {"played":0, "won":0, "drawn":0, "lost":0, "gf":0, "ga":0, "pts":0}
    for m in matches:
        score_obj = m.get('score', {})
        if score_obj and 'ft' in score_obj:
            ft = score_obj['ft']
            if isinstance(ft, list) and len(ft) == 2:
                group = m.get('group', 'Unknown')
                team1 = m.get('team1', '')
                team2 = m.get('team2', '')
                s1, s2 = ft[0], ft[1]
                if (group, team1) in standings and (group, team2) in standings:
                    standings[(group, team1)]["played"] += 1
                    standings[(group, team1)]["gf"] += s1
                    standings[(group, team1)]["ga"] += s2
                    standings[(group, team2)]["played"] += 1
                    standings[(group, team2)]["gf"] += s2
                    standings[(group, team2)]["ga"] += s1
                    if s1 > s2:
                        standings[(group, team1)]["won"] += 1
                        standings[(group, team1)]["pts"] += 3
                        standings[(group, team2)]["lost"] += 1
                    elif s1 < s2:
                        standings[(group, team2)]["won"] += 1
                        standings[(group, team2)]["pts"] += 3
                        standings[(group, team1)]["lost"] += 1
                    else:
                        standings[(group, team1)]["drawn"] += 1
                        standings[(group, team2)]["drawn"] += 1
                        standings[(group, team1)]["pts"] += 1
                        standings[(group, team2)]["pts"] += 1
    rows = []
    for (group, team), data in standings.items():
        rows.append({
            "Group": group,
            "Team": team,
            "Played": data["played"],
            "Won": data["won"],
            "Drawn": data["drawn"],
            "Lost": data["lost"],
            "GF": data["gf"],
            "GA": data["ga"],
            "Points": data["pts"]
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df['GD'] = df['GF'] - df['GA']
        df = df.sort_values(['Group','Points','GD','GF'], ascending=[True,False,False,False])
        return df.drop(columns=['GD'])
    return df

# ---------- MAIN APP ----------
st.title(_("🏆 FIFA World Cup 2026 Predictor"))
st.caption(_("Live scores, standings, and AI predictions for the World Cup | AI: {}").format(ai_provider) + f" | {datetime.now().strftime('%H:%M:%S')}")

auto_refresh = st.sidebar.checkbox(_("Auto-refresh live scores (every 30 sec)"), value=False)
if auto_refresh:
    st.sidebar.info(_("Auto-refresh enabled"))
    time.sleep(30)
    st.rerun()

mode = st.sidebar.radio(_("Mode"), [
    _("World Cup 2026"),
    _("Player Stats"),
    _("Team Stats"),
    _("Top Scorers"),
    _("AI Insights & Chat"),
    _("Match Predictor")
])

if mode == _("World Cup 2026"):
    st.subheader(_("🏆 FIFA World Cup 2026"))
    tab1, tab2 = st.tabs([_("📺 Matches"), _("📊 Group Standings")])
    with tab1:
        show_probs = st.checkbox(_("Show Win Probabilities"))
        matches = get_worldcup_matches(show_probabilities=show_probs)
        if matches:
            st.dataframe(pd.DataFrame(matches), use_container_width=True)
            if st.button(_("🤖 AI World Cup Analysis")):
                ctx = f"{_('World Cup matches')}: {pd.DataFrame(matches).to_string()}"
                analysis = call_ai(_("Analyze which match is most exciting and predict winners."), ctx)
                st.info(analysis)
        else:
            st.info(_("No match data."))
    with tab2:
        df_stand = get_worldcup_standings()
        if not df_stand.empty:
            for grp in sorted(df_stand['Group'].unique()):
                st.markdown(f"### {_('Group')} {grp}")
                group_df = df_stand[df_stand['Group'] == grp].rename(columns={
                    "Group": _("Group"),
                    "Team": _("Team"),
                    "Played": _("Played"),
                    "Won": _("Won"),
                    "Drawn": _("Drawn"),
                    "Lost": _("Lost"),
                    "GF": _("GF"),
                    "GA": _("GA"),
                    "Points": _("Points")
                })
                st.dataframe(group_df, use_container_width=True)
            if st.button(_("🤖 AI Group Analysis")):
                analysis = call_ai(_("Which teams are likely to advance to knockout stage?"), f"{_('Standings')}:\n{df_stand.to_string()}")
                st.info(analysis)
        else:
            st.info(_("Standings not available."))
    if st.button(_("🔄 Refresh World Cup")):
        st.cache_data.clear()
        st.rerun()

elif mode == _("Player Stats"):
    st.subheader(_("⚽ Player Stats – World Cup 2026"))
    st.markdown("All data is drawn **locally** from `worldcup.squads.json` and `worldcup.json`.")
    name = st.text_input(_("Search player by name"))
    if st.button(_("Search")):
        if not name:
            st.warning("Please enter a player name.")
        else:
            player = search_player_stats(name)
            if player:
                col1, col2 = st.columns(2)
                col1.metric(_("Team"), player['Team'])
                col1.metric(_("Position"), player['Position'])
                col1.metric(_("Club"), player['Club'])
                col2.metric(_("World Cup Goals"), player['Goals'])
            else:
                st.error("Player not found in the tournament squads.")

elif mode == _("Team Stats"):
    st.subheader(_("🏆 Team Stats – World Cup 2026"))
    df_stand = get_worldcup_standings()
    if not df_stand.empty:
        df_all = df_stand.copy()
        df_all['GD'] = df_all['GF'] - df_all['GA']
        df_all = df_all.sort_values(['Points', 'GD', 'GF'], ascending=[False, False, False])
        df_display = df_all.rename(columns={
            "Group": _("Group"),
            "Team": _("Team"),
            "Played": _("Played"),
            "Won": _("Won"),
            "Drawn": _("Drawn"),
            "Lost": _("Lost"),
            "GF": _("GF"),
            "GA": _("GA"),
            "Points": _("Points"),
            "GD": "GD"
        })
        st.dataframe(df_display, use_container_width=True)
        fig = px.bar(df_display, x='Team', y='Points', color='Group', title='Points per Team')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No team stats available.")

elif mode == _("Top Scorers"):
    st.subheader(_("⚽ World Cup 2026 Top Scorers"))
    df_top = build_player_stats()[['Player', 'Goals']].sort_values('Goals', ascending=False)
    if not df_top.empty:
        st.dataframe(df_top, use_container_width=True)
        fig = px.bar(df_top.head(10), x='Player', y='Goals', title='Top 10 Goal Scorers')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No goals scored yet.")

elif mode == _("Match Predictor"):
    st.subheader(_("🔮 Match Predictor – Detailed Analysis"))
    st.markdown("Select two teams to get a comprehensive win probability analysis based on historical data, head-to-head, squad comparison, and current form.")
    
    all_teams = []
    if SQUADS_DATA and isinstance(SQUADS_DATA, list):
        for team_entry in SQUADS_DATA:
            team_name = team_entry.get('name', '')
            if team_name:
                all_teams.append(team_name)
    all_teams = sorted(set(all_teams))
    
    if not all_teams:
        st.warning("No teams found. Please ensure squads data is loaded.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            team1 = st.selectbox(_("Select Team 1"), all_teams, index=0)
        with col2:
            team2 = st.selectbox(_("Select Team 2"), all_teams, index=min(1, len(all_teams)-1))
        
        if team1 and team2 and team1 != team2:
            # Store selected teams in session state
            st.session_state['predict_team1'] = team1
            st.session_state['predict_team2'] = team2
            
            if st.button(_("Calculate Win Probability")):
                with st.spinner(_("Analyzing data...")):
                    result = calculate_win_probability(team1, team2, include_details=True)
                    st.session_state['predict_result'] = result
            
            # Display result if available
            if 'predict_result' in st.session_state and st.session_state['predict_result']:
                result = st.session_state['predict_result']
                
                st.markdown(f"### 📊 Win Probability: {result['team1']} vs {result['team2']}")
                col1, col2, col3 = st.columns(3)
                col1.metric(f"{result['team1']} Win", f"{result['team1_win']}%")
                col2.metric("Draw", f"{result['draw']}%")
                col3.metric(f"{result['team2']} Win", f"{result['team2_win']}%")
                
                with st.expander(_("📈 Detailed Breakdown")):
                    st.markdown("#### Historical Performance")
                    st.write(f"**{result['team1']}** win rate in World Cups: {result['historical_win_pct1']}%")
                    st.write(f"**{result['team2']}** win rate in World Cups: {result['historical_win_pct2']}%")
                    
                    st.markdown("#### Head-to-Head")
                    h2h_total = result['h2h_total']
                    if h2h_total > 0:
                        st.write(f"Total meetings: {h2h_total}")
                        st.write(f"**{result['team1']}** wins: {result['h2h_wins1']}")
                        st.write(f"Draws: {result['h2h_draws']}")
                        st.write(f"**{result['team2']}** wins: {result['h2h_wins2']}")
                    else:
                        st.write("No previous World Cup meetings found.")
                    
                    st.markdown("#### Current Form (2026)")
                    st.write(f"**{result['team1']}** form score: {result['form1']}%")
                    st.write(f"**{result['team2']}** form score: {result['form2']}%")
                    
                    st.markdown("#### Squad Comparison")
                    st.write(f"**{result['team1']}** squad score: {result['squad_score1']}")
                    st.write(f"**{result['team2']}** squad score: {result['squad_score2']}")
                    st.write(f"Squad advantage: **{result['squad_advantage']}**")
                    
                    st.markdown("##### Position-wise Comparison")
                    pos_comp = result['position_comparison']
                    for pos, data in pos_comp.items():
                        st.write(f"**{pos}**: {result['team1']} avg {data['team1_avg']:.1f} vs {result['team2']} avg {data['team2_avg']:.1f} → {data['advantage']} advantage")
                
                # AI Analysis button – always visible after calculation
                if st.button(_("🤖 AI Analysis of this Match")):
                    prompt = f"Analyze the upcoming match between {result['team1']} and {result['team2']}. Based on the following data: Historical win rates: {result['team1']} {result['historical_win_pct1']}%, {result['team2']} {result['historical_win_pct2']}%. Head-to-head: {result['h2h_wins1']} wins for {result['team1']}, {result['h2h_draws']} draws, {result['h2h_wins2']} wins for {result['team2']}. Current form: {result['team1']} {result['form1']}%, {result['team2']} {result['form2']}%. Squad advantage: {result['squad_advantage']}. Provide a detailed prediction."
                    analysis = call_ai(prompt, "")
                    st.info(analysis)
        else:
            if team1 == team2:
                st.warning("Please select two different teams.")
            # Clear previous result when teams change
            if 'predict_result' in st.session_state:
                del st.session_state['predict_result']

else:  # AI Insights & Chat
    st.subheader(_("💬 Football Chat"))
    st.markdown("**Select ADK Agent in the sidebar to use the AI.**")
    q = st.text_area(_("Ask about football (World Cup, leagues...)"))
    if st.button(_("Ask AI")) and q:
        st.info(call_ai(q, _("Football knowledge.")))

st.divider()
st.caption(_("Data: openfootball/worldcup.json (matches & squads). Historical data from openfootball/worldcup. AI powered by Ollama/OpenAI/ADK."))
