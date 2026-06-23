import json
import re
import os
from collections import defaultdict

def parse_cup_file(filepath):
    """Parse a cup.txt file and extract match results."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = []
    pattern = r'([A-Za-z\s]+)\s+(\d+)-(\d+)\s*(?:\([^)]*\))?\s+([A-Za-z\s]+)'
    
    lines = content.split('\n')
    for line in lines:
        if line.startswith('=') or line.startswith('▪') or not line.strip():
            continue
        for match in re.finditer(pattern, line):
            team1 = match.group(1).strip()
            score1 = int(match.group(2))
            score2 = int(match.group(3))
            team2 = match.group(4).strip()
            team1 = re.sub(r'\s*@.*$', '', team1).strip()
            team2 = re.sub(r'\s*@.*$', '', team2).strip()
            if team1 and team2 and len(team1) > 1 and len(team2) > 1:
                matches.append({
                    'team1': team1,
                    'team2': team2,
                    'score1': score1,
                    'score2': score2
                })
    return matches

def load_all_historical_data(data_dir='data/historical_worldcup'):
    all_matches = []
    if not os.path.exists(data_dir):
        return all_matches
    for item in os.listdir(data_dir):
        if os.path.isdir(os.path.join(data_dir, item)):
            cup_file = os.path.join(data_dir, item, 'cup.txt')
            if os.path.exists(cup_file):
                matches = parse_cup_file(cup_file)
                all_matches.extend(matches)
    return all_matches

def get_team_historical_stats(matches):
    stats = defaultdict(lambda: {'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'gf': 0, 'ga': 0})
    for m in matches:
        t1, t2 = m['team1'], m['team2']
        s1, s2 = m['score1'], m['score2']
        stats[t1]['played'] += 1
        stats[t2]['played'] += 1
        stats[t1]['gf'] += s1
        stats[t1]['ga'] += s2
        stats[t2]['gf'] += s2
        stats[t2]['ga'] += s1
        if s1 > s2:
            stats[t1]['won'] += 1
            stats[t2]['lost'] += 1
        elif s1 < s2:
            stats[t2]['won'] += 1
            stats[t1]['lost'] += 1
        else:
            stats[t1]['drawn'] += 1
            stats[t2]['drawn'] += 1
    result = {}
    for team, data in stats.items():
        played = data['played']
        win_pct = data['won'] / played if played > 0 else 0
        goals_per_match = data['gf'] / played if played > 0 else 0
        goals_conceded_per_match = data['ga'] / played if played > 0 else 0
        result[team] = {
            'played': played,
            'won': data['won'],
            'drawn': data['drawn'],
            'lost': data['lost'],
            'gf': data['gf'],
            'ga': data['ga'],
            'win_pct': win_pct,
            'goals_per_match': goals_per_match,
            'goals_conceded_per_match': goals_conceded_per_match
        }
    return result

def get_head_to_head(matches, team1, team2):
    h2h = {'team1_wins': 0, 'draws': 0, 'team2_wins': 0, 'total': 0}
    for m in matches:
        t1, t2 = m['team1'], m['team2']
        s1, s2 = m['score1'], m['score2']
        if (t1 == team1 and t2 == team2) or (t1 == team2 and t2 == team1):
            h2h['total'] += 1
            if s1 > s2:
                if t1 == team1:
                    h2h['team1_wins'] += 1
                else:
                    h2h['team2_wins'] += 1
            elif s1 < s2:
                if t1 == team2:
                    h2h['team1_wins'] += 1
                else:
                    h2h['team2_wins'] += 1
            else:
                h2h['draws'] += 1
    return h2h
