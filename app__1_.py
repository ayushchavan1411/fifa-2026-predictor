import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import asyncio
from datetime import datetime
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
from tmkt import TMKT
from translations import translate

# ---------- LANGUAGE SELECTION ----------
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

lang_options = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "తెలుగు (Telugu)": "te"
}
lang_display = st.sidebar.selectbox(
    "भाषा / Language",
    list(lang_options.keys()),
    index=list(lang_options.values()).index(st.session_state.lang)
)
new_lang = lang_options[lang_display]
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    st.rerun()

def _(text):
    return translate(text, st.session_state.lang)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title=_("🏅 AI-Powered Multi-Sport Stats Tracker"), page_icon="🏅", layout="wide")

# ---------- AI CONFIGURATION ----------
st.sidebar.title(_("🤖 AI Settings"))
ai_provider = st.sidebar.selectbox(_("AI Provider"), ["None", "Ollama (Local)", "OpenAI (BYOK)"])

ollama_endpoint = None
ollama_model = None
openai_client = None

if ai_provider == "Ollama (Local)":
    ollama_endpoint = st.sidebar.text_input(_("Ollama Endpoint"), "http://127.0.0.1:11434")
    ollama_model = st.sidebar.text_input(_("Model Name"), "tinyllama")
    if st.sidebar.button(_("Test Ollama Connection")):
        try:
            r = requests.post(f"{ollama_endpoint}/api/generate", 
                              json={"model": ollama_model, "prompt": "Hi"}, timeout=10)  # increased timeout
            if r.status_code == 200:
                st.sidebar.success(_("✅ Ollama reachable!"))
            else:
                st.sidebar.error(_("❌ Connection failed"))
        except requests.exceptions.Timeout:
            st.sidebar.error(_("❌ Ollama is slow – try again or restart Ollama"))
        except Exception as e:
            st.sidebar.error(_("❌ Cannot reach Ollama: ") + str(e))

elif ai_provider == "OpenAI (BYOK)":
    openai_api_key = st.sidebar.text_input(_("OpenAI API Key"), type="password")
    if openai_api_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            st.sidebar.success(_("✅ API key accepted"))
        except ImportError:
            st.sidebar.error(_("Please install openai: pip install openai"))
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# ---------- AI HELPER ----------
def call_ai(prompt, context=""):
    full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer concisely."
    if ai_provider == "Ollama (Local)" and ollama_endpoint and ollama_model:
        try:
            payload = {"model": ollama_model, "prompt": full_prompt, "stream": False}
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
                    {"role": "system", "content": _("You are a helpful sports assistant.")},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI error: {e}"
    else:
        return _("AI not configured.")

# ---------- WIN PERCENTAGE HELPER ----------
def get_team_win_percentage(team_name, sport):
    team_lower = team_name.lower()
    nba_pct = {
        "lakers": 0.55, "warriors": 0.52, "celtics": 0.68, "heat": 0.54,
        "bucks": 0.60, "suns": 0.58, "nuggets": 0.65, "mavericks": 0.62,
    }
    football_pct = {
        "manchester city": 0.74, "arsenal": 0.68, "liverpool": 0.63,
        "real madrid": 0.71, "barcelona": 0.66, "bayern munich": 0.72,
        "borussia dortmund": 0.58, "psg": 0.70, "chelsea": 0.55,
    }
    if sport == "NBA":
        for key, pct in nba_pct.items():
            if key in team_lower:
                return f"{pct*100:.0f}%"
        return _("~50%")
    elif sport == "Football":
        for key, pct in football_pct.items():
            if key in team_lower:
                return f"{pct*100:.0f}%"
        return _("~50%")
    return _("unknown")

# ---------- NBA MOCK DATA ----------
@st.cache_data(ttl=30)
def get_nba_live_scores():
    return [
        {"match": "Lakers vs Warriors", "status": _("🔴 LIVE"), "score": "98-95", "time": _("4th Q - 2:30"), "competition": "NBA"},
        {"match": "Celtics vs Heat", "status": _("✅ FINISHED"), "score": "112-108", "time": _("Final"), "competition": "NBA"},
        {"match": "Bucks vs Suns", "status": _("🔴 LIVE"), "score": "75-72", "time": _("3rd Q - 5:00"), "competition": "NBA"},
    ]

def get_nba_player_stats(player_name):
    try:
        player_dict = players.get_players()
        player = next((p for p in player_dict if p['full_name'].lower() == player_name.lower()), None)
        if not player:
            return None
        career = playercareerstats.PlayerCareerStats(player_id=player['id'])
        df = career.get_data_frames()[0]
        if not df.empty:
            latest = df.iloc[-1]
            return {
                "name": player['full_name'],
                "pts": latest['PTS'],
                "reb": latest['REB'],
                "ast": latest['AST'],
                "stl": latest['STL'],
                "blk": latest['BLK'],
                "fg_pct": latest['FG_PCT']
            }
    except:
        return None

# ---------- FOOTBALL: 2026 WORLD CUP (FULL ACCURATE DATA) ----------
GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cabo Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Uzbekistan", "Colombia", "Congo DR"],
    "L": ["England", "Croatia", "Ghana", "Panama"]
}

# Match schedule (based on real 2026 fixtures)
MATCHES = [
    ("Jun 11", "Mexico", "South Africa", "A", "finished", 2, 0),
    ("Jun 11", "South Korea", "Czechia", "A", "finished", 0, 0),
    ("Jun 12", "Canada", "Bosnia and Herzegovina", "B", "finished", 1, 1),
    ("Jun 12", "USA", "Paraguay", "D", "finished", 4, 1),
    ("Jun 12", "Qatar", "Switzerland", "B", "finished", 1, 1),
    ("Jun 12", "Brazil", "Morocco", "C", "finished", 1, 1),
    ("Jun 13", "Haiti", "Scotland", "C", "upcoming", None, None),
    ("Jun 13", "Australia", "Türkiye", "D", "upcoming", None, None),
    ("Jun 13", "Germany", "Curaçao", "E", "upcoming", None, None),
    ("Jun 13", "Netherlands", "Japan", "F", "upcoming", None, None),
    ("Jun 13", "Ivory Coast", "Ecuador", "E", "upcoming", None, None),
    ("Jun 13", "Sweden", "Tunisia", "F", "upcoming", None, None),
    ("Jun 14", "Spain", "Cabo Verde", "H", "upcoming", None, None),
    ("Jun 14", "Belgium", "Egypt", "G", "upcoming", None, None),
    ("Jun 14", "Saudi Arabia", "Uruguay", "H", "upcoming", None, None),
    ("Jun 14", "Iran", "New Zealand", "G", "upcoming", None, None),
    ("Jun 15", "France", "Senegal", "I", "upcoming", None, None),
    ("Jun 15", "Iraq", "Norway", "I", "upcoming", None, None),
    ("Jun 15", "Argentina", "Algeria", "J", "upcoming", None, None),
    ("Jun 15", "Austria", "Jordan", "J", "upcoming", None, None),
    ("Jun 16", "Ghana", "Panama", "L", "upcoming", None, None),
    ("Jun 16", "England", "Croatia", "L", "upcoming", None, None),
    ("Jun 16", "Portugal", "Congo DR", "K", "upcoming", None, None),
    ("Jun 16", "Uzbekistan", "Colombia", "K", "upcoming", None, None),
]

def get_worldcup_matches():
    match_list = []
    for m in MATCHES:
        date, t1, t2, grp, status, s1, s2 = m
        if status == "finished":
            status_text = _("✅ FINISHED")
            score = f"{s1}-{s2}"
            time_text = _("Final")
        elif status == "live":
            status_text = _("🟢 LIVE")
            score = f"{s1}-{s2}"
            time_text = _("In Progress")
        else:
            status_text = _("📋 UPCOMING")
            score = "-"
            time_text = date
        match_list.append({
            _("Match"): f"{t1} vs {t2}",
            _("Status"): status_text,
            _("Score"): score,
            _("Time"): time_text,
            _("Stage"): _(f"Group {grp}")  # Translate "Group X"
        })
    return match_list

def get_worldcup_standings():
    standings = {}
    for grp, teams in GROUPS.items():
        for team in teams:
            standings[(grp, team)] = {"played":0, "won":0, "drawn":0, "lost":0, "gf":0, "ga":0, "pts":0}
    for m in MATCHES:
        date, t1, t2, grp, status, s1, s2 = m
        if status == "finished":
            standings[(grp, t1)]["played"] += 1
            standings[(grp, t1)]["gf"] += s1
            standings[(grp, t1)]["ga"] += s2
            standings[(grp, t2)]["played"] += 1
            standings[(grp, t2)]["gf"] += s2
            standings[(grp, t2)]["ga"] += s1
            if s1 > s2:
                standings[(grp, t1)]["won"] += 1
                standings[(grp, t1)]["pts"] += 3
                standings[(grp, t2)]["lost"] += 1
            elif s1 < s2:
                standings[(grp, t2)]["won"] += 1
                standings[(grp, t2)]["pts"] += 3
                standings[(grp, t1)]["lost"] += 1
            else:
                standings[(grp, t1)]["drawn"] += 1
                standings[(grp, t2)]["drawn"] += 1
                standings[(grp, t1)]["pts"] += 1
                standings[(grp, t2)]["pts"] += 1
    rows = []
    for (grp, team), data in standings.items():
        rows.append({
            "Group": grp,
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

def get_football_standings():
    teams = [_("Manchester City"), _("Arsenal"), _("Liverpool"), _("Aston Villa"), _("Tottenham")]
    return pd.DataFrame({
        _("Team"): teams,
        _("Played"): [38,38,38,38,38],
        _("Won"): [28,26,24,20,19],
        _("Drawn"): [7,8,8,7,6],
        _("Lost"): [3,4,6,11,13],
        _("Points"): [91,86,80,67,63]
    })

def search_football_player(query):
    if not query:
        return None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def fetch():
            async with TMKT() as tmkt:
                results = await tmkt.player_search(query)
                if not results:
                    return None
                pid = results[0]['id']
                profile = await tmkt.get_player(pid)
                stats = await tmkt.get_player_stats(pid)
                if profile:
                    market_val = profile.get('market_value', 'N/A')
                    if stats and len(stats) > 0:
                        latest = stats[-1]
                        return {
                            "name": profile.get('name', query.title()),
                            "goals": latest.get('goals', 0),
                            "assists": latest.get('assists', 0),
                            "matches": latest.get('appearances', 0),
                            "team": profile.get('current_club_name', _('Unknown')),
                            "market_value": market_val
                        }
                    else:
                        return {
                            "name": profile.get('name', query.title()),
                            "goals": 0, "assists": 0, "matches": 0,
                            "team": profile.get('current_club_name', _('Unknown')),
                            "market_value": market_val
                        }
            return None
        return loop.run_until_complete(fetch())
    except:
        mock = {
            "neymar": {"name":"Neymar","goals":18,"assists":12,"matches":22,"team":"Al-Hilal","market_value":"€45m"},
            "messi": {"name":"Messi","goals":22,"assists":15,"matches":28,"team":"Inter Miami","market_value":"€25m"},
        }
        for key, val in mock.items():
            if key in query.lower():
                return val
        return None

def get_football_live_scores():
    # League live scores (mock)
    return [
        {"match":"Manchester City vs Arsenal","status":_("🔴 LIVE"),"score":"2-1","time":_("2nd Half - 65'"),"competition":"Premier League"},
        {"match":"Real Madrid vs Barcelona","status":_("✅ FINISHED"),"score":"3-2","time":_("Final"),"competition":"La Liga"},
    ]

# ---------- MAIN APP ----------
st.title(_("🏅 AI-Powered Multi-Sport Stats Tracker"))
st.caption(_("Sports: NBA | Football (World Cup) | AI: {}").format(ai_provider) + f" | {datetime.now().strftime('%H:%M:%S')}")

auto_refresh = st.sidebar.checkbox(_("Auto-refresh live scores (every 30 sec)"), value=False)
if auto_refresh:
    st.sidebar.info(_("Auto-refresh enabled"))
    time.sleep(30)
    st.rerun()

sport = st.sidebar.selectbox(_("Choose Sport"), [_("🏀 NBA Basketball"), _("⚽ Football (Soccer)")])

# ---------- NBA SECTION ----------
if sport == _("🏀 NBA Basketball"):
    mode = st.sidebar.radio(_("Mode"), [_("Live Scores"), _("Player Stats"), _("AI Insights & Chat")])
    if mode == _("Live Scores"):
        st.subheader(_("🏀 NBA Live Scores"))
        with st.spinner(_("Fetching live scores...")):
            scores = get_nba_live_scores()
        df = pd.DataFrame(scores)
        st.dataframe(df, use_container_width=True)
        if st.button(_("🤖 AI Analysis with Win %")):
            context = _("NBA live scores with win percentages:\n")
            for _, row in df.iterrows():
                teams = row['match'].split(' vs ')
                if len(teams) == 2:
                    wp1 = get_team_win_percentage(teams[0], "NBA")
                    wp2 = get_team_win_percentage(teams[1], "NBA")
                    context += f"{teams[0]} ({wp1}) vs {teams[1]} ({wp2}) | Score: {row['score']}\n"
            analysis = call_ai(_("Analyze these games. Which is most competitive? Predict outcomes."), context)
            st.info(f"🤖 AI: {analysis}")
        if st.button(_("🔄 Refresh")):
            st.cache_data.clear()
            st.rerun()
    elif mode == _("Player Stats"):
        st.subheader(_("🏀 NBA Player Stats"))
        name = st.text_input(_("Player name (e.g., LeBron James)"))
        if st.button(_("Get Stats")):
            with st.spinner(_("Fetching player data...")):
                stats = get_nba_player_stats(name)
                if stats:
                    col1, col2, col3 = st.columns(3)
                    col1.metric(_("PPG"), stats['pts'])
                    col2.metric(_("RPG"), stats['reb'])
                    col3.metric(_("APG"), stats['ast'])
                    if st.button(_("🧠 AI Analysis")):
                        ctx = _("Player {}: {} PPG, {} RPG, {} APG.").format(stats['name'], stats['pts'], stats['reb'], stats['ast'])
                        analysis = call_ai(_("Give a scouting report."), ctx)
                        st.info(analysis)
                else:
                    st.error(_("Player not found."))
    else:
        st.subheader(_("💬 NBA Chat"))
        q = st.text_area(_("Ask about NBA"))
        if st.button(_("Ask AI")) and q:
            st.info(call_ai(q, _("NBA knowledge.")))

# ---------- FOOTBALL SECTION ----------
elif sport == _("⚽ Football (Soccer)"):
    mode = st.sidebar.radio(_("Mode"), [_("World Cup 2026"), _("Live Scores (Leagues)"), _("League Standings"), _("Player Stats"), _("AI Insights & Chat")])
    if mode == _("World Cup 2026"):
        st.subheader(_("🏆 FIFA World Cup 2026"))
        tab1, tab2 = st.tabs([_("📺 Matches"), _("📊 Group Standings")])
        with tab1:
            matches = get_worldcup_matches()
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
    elif mode == _("Live Scores (Leagues)"):
        st.subheader(_("⚽ Live Football Scores (Leagues)"))
        scores = get_football_live_scores()
        df = pd.DataFrame(scores)
        st.dataframe(df, use_container_width=True)
        if st.button(_("🤖 AI Analysis with Win %")):
            ctx = _("Live football scores with win %:\n")
            for _, row in df.iterrows():
                teams = row['match'].split(' vs ')
                if len(teams) == 2:
                    wp1 = get_team_win_percentage(teams[0], "Football")
                    wp2 = get_team_win_percentage(teams[1], "Football")
                    ctx += f"{teams[0]} ({wp1}) vs {teams[1]} ({wp2}) | Score: {row['score']}\n"
            analysis = call_ai(_("Analyze these matches."), ctx)
            st.info(analysis)
        if st.button(_("🔄 Refresh")):
            st.cache_data.clear()
            st.rerun()
    elif mode == _("League Standings"):
        st.subheader(_("🏆 Premier League Standings"))
        df = get_football_standings()
        st.dataframe(df, use_container_width=True)
        fig = px.bar(df, x=_("Team"), y=_("Points"), title=_("Points Table"), color=_("Points"), text=_("Points"))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig)
        if st.button(_("🤖 AI League Analysis")):
            analysis = call_ai(_("Who will win the league and why?"), f"{_('Standings')}:\n{df.to_string()}")
            st.info(analysis)
    elif mode == _("Player Stats"):
        st.subheader(_("⚽ Football Player Stats"))
        name = st.text_input(_("Player name (Messi, Ronaldo, Neymar...)"))
        if st.button(_("Search")):
            with st.spinner(_("Fetching real data...")):
                stats = search_football_player(name)
                if stats:
                    col1, col2, col3 = st.columns(3)
                    col1.metric(_("Goals"), stats['goals'])
                    col2.metric(_("Assists"), stats['assists'])
                    col3.metric(_("Matches"), stats['matches'])
                    st.metric(_("Team"), stats['team'])
                    if stats.get('market_value'):
                        st.metric(_("Market Value"), stats['market_value'])
                    if st.button(_("🧠 AI Analysis")):
                        ctx = f"{stats['name']}: {stats['goals']} {_('goals')}, {stats['assists']} {_('assists')} in {stats['matches']} {_('matches')}."
                        analysis = call_ai(_("Evaluate this player."), ctx)
                        st.info(analysis)
                else:
                    st.error(_("Player not found."))
    else:
        st.subheader(_("💬 Football Chat"))
        q = st.text_area(_("Ask about football (World Cup, leagues...)"))
        if st.button(_("Ask AI")) and q:
            st.info(call_ai(q, _("Football knowledge.")))

# ---------- FOOTER ----------
st.divider()
st.caption(_("Data: NBA API (simulated live scores), Transfermarkt. AI powered by Ollama/OpenAI."))