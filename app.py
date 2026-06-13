import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="FIFA 2026 Match Predictor", layout="wide")

st.title("⚽ FIFA 2026 AI Match Predictor")
st.write("Predict FIFA World Cup 2026 match outcomes using AI")

teams = [
    "Argentina", "Belgium", "Brazil", "England", "France", 
    "Germany", "Italy", "Netherlands", "Portugal", "Spain",
    "Mexico", "USA", "Canada", "Japan", "South Korea",
    "Australia", "Uruguay", "Colombia", "Chile", "Peru",
    "Morocco", "Senegal", "Ghana", "Egypt", "Tunisia",
    "Poland", "Denmark", "Croatia", "Czech Republic", "Hungary"
]

teams.sort()

st.sidebar.header("📊 Prediction Settings")

col1, col2 = st.columns(2)

with col1:
    team1 = st.selectbox("Select Team 1", teams, index=0)

with col2:
    team2 = st.selectbox("Select Team 2", teams, index=1)

if team1 == team2:
    st.warning("⚠️ Please select different teams!")
else:
    def predict_match(team1, team2):
        team_strength = {
            "Argentina": 95, "Brazil": 94, "France": 93, "England": 91,
            "Belgium": 90, "Netherlands": 89, "Germany": 88, "Spain": 87,
            "Portugal": 86, "Italy": 85, "Uruguay": 82, "Mexico": 77,
            "USA": 76, "Canada": 75, "South Korea": 73, "Japan": 72,
            "Australia": 70, "Colombia": 78, "Peru": 76, "Chile": 75,
            "Poland": 80, "Denmark": 83, "Croatia": 81, "Czech Republic": 79,
            "Hungary": 74, "Senegal": 76, "Morocco": 78, "Ghana": 72,
            "Egypt": 70, "Tunisia": 71
        }
        
        strength1 = team_strength.get(team1, 75)
        strength2 = team_strength.get(team2, 75)
        
        total = strength1 + strength2
        prob_team1 = strength1 / total
        prob_team2 = strength2 / total
        
        base_goals1 = prob_team1 * 3
        base_goals2 = prob_team2 * 3
        
        np.random.seed(hash((team1, team2)) % 2**32)
        goals1 = int(np.random.normal(base_goals1, 0.5))
        goals2 = int(np.random.normal(base_goals2, 0.5))
        
        goals1 = max(0, goals1)
        goals2 = max(0, goals2)
        
        return prob_team1, prob_team2, goals1, goals2
    
    prob1, prob2, goals1, goals2 = predict_match(team1, team2)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(f"🏆 {team1}", f"{goals1}", f"Win: {prob1*100:.1f}%")
    
    with col2:
        st.write("")
        st.write("")
        st.write(f"### VS")
    
    with col3:
        st.metric(f"🏆 {team2}", f"{goals2}", f"Win: {prob2*100:.1f}%")
    
    st.divider()
    
    st.subheader("📈 Prediction Details")
    
    pred_data = {
        "Team": [team1, team2],
        "Predicted Goals": [goals1, goals2],
        "Win Probability": [f"{prob1*100:.1f}%", f"{prob2*100:.1f}%"],
        "Result": ["Win" if goals1 > goals2 else ("Draw" if goals1 == goals2 else "Loss"), 
                   "Loss" if goals1 > goals2 else ("Draw" if goals1 == goals2 else "Win")]
    }
    
    df = pd.DataFrame(pred_data)
    st.dataframe(df, use_container_width=True)
    
    st.subheader("🤖 How the AI Works")
    st.write("""
    This AI prediction model uses:
    1. **Team Strength Ratings** - Based on FIFA rankings and historical performance
    2. **Probability Calculation** - Computes win probability based on team strength
    3. **Score Generation** - Predicts expected goals using statistical distribution
    
    **Note:** This is a simplified model for educational purposes.
    """)
    
    st.divider()
    st.write("📅 Predictions are for FIFA World Cup 2026 qualification/tournament matches")
    st.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")