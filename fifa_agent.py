# fifa_agent.py
import json
from google.adk.agents import Agent

# Helper: load worldcup data
def load_worldcup_data():
    with open('data/worldcup.json/2026/worldcup.json', 'r') as f:
        return json.load(f)

def get_standings_text():
    """Return a readable summary of current group standings."""
    data = load_worldcup_data()
    groups = {}
    for g in data.get('groups', []):
        groups[g.get('group', '')] = g.get('teams', [])
    matches = data.get('matches', [])
    standings = {}
    for group_name, teams in groups.items():
        for team in teams:
            standings[(group_name, team)] = {"played":0, "won":0, "drawn":0, "lost":0, "gf":0, "ga":0, "pts":0}
    for m in matches:
        if m.get('status') == 'finished':
            group = m.get('group', '')
            home = m.get('home_team')
            away = m.get('away_team')
            hg = m.get('home_score', 0)
            ag = m.get('away_score', 0)
            if (group, home) in standings:
                standings[(group, home)]["played"] += 1
                standings[(group, home)]["gf"] += hg
                standings[(group, home)]["ga"] += ag
                standings[(group, away)]["played"] += 1
                standings[(group, away)]["gf"] += ag
                standings[(group, away)]["ga"] += hg
                if hg > ag:
                    standings[(group, home)]["won"] += 1
                    standings[(group, home)]["pts"] += 3
                    standings[(group, away)]["lost"] += 1
                elif hg < ag:
                    standings[(group, away)]["won"] += 1
                    standings[(group, away)]["pts"] += 3
                    standings[(group, home)]["lost"] += 1
                else:
                    standings[(group, home)]["drawn"] += 1
                    standings[(group, away)]["drawn"] += 1
                    standings[(group, home)]["pts"] += 1
                    standings[(group, away)]["pts"] += 1
    lines = []
    for (group, team), data in standings.items():
        if data["played"] > 0:
            lines.append(f"Group {group}: {team} – P{data['played']} W{data['won']} D{data['drawn']} L{data['lost']} GF{data['gf']} GA{data['ga']} Pts{data['pts']}")
    return "\n".join(lines) if lines else "No matches played yet."

def get_current_standings() -> str:
    """Returns the current group standings of FIFA World Cup 2026."""
    return get_standings_text()

def predict_match_outcome(team1: str, team2: str) -> str:
    """Predicts the outcome of a match between two teams (simple heuristic)."""
    strengths = {
        "brazil": 95, "germany": 90, "argentina": 88, "france": 87,
        "england": 85, "spain": 84, "netherlands": 83, "portugal": 82,
        "belgium": 80, "croatia": 78, "mexico": 75, "usa": 74,
        "senegal": 72, "japan": 70, "south korea": 68, "australia": 65,
    }
    t1, t2 = team1.lower(), team2.lower()
    s1 = strengths.get(t1, 70)
    s2 = strengths.get(t2, 70)
    if s1 > s2 + 5:
        return f"{team1} is likely to win."
    elif s2 > s1 + 5:
        return f"{team2} is likely to win."
    else:
        return f"The match between {team1} and {team2} is expected to be close or a draw."

# Create the agent
root_agent = Agent(
    name="fifa_analyst",
    model="gemini-2.5-flash",
    instruction="""
You are a FIFA World Cup 2026 analyst. Use your tools:
- get_current_standings: returns group standings.
- predict_match_outcome(team1, team2): predicts winner.
Answer questions concisely and accurately.
""",
    tools=[get_current_standings, predict_match_outcome]
)
