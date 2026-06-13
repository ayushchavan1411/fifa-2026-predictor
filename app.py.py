import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Set page config
st.set_page_config(page_title="FIFA 2026 Match Predictor", layout="wide")

# Language translations
translations = {
    "English": {
        "title": "⚽ FIFA 2026 AI Match Predictor",
        "subtitle": "Predict FIFA World Cup 2026 match outcomes using AI",
        "settings": "📊 Prediction Settings",
        "team1": "Select Team 1",
        "team2": "Select Team 2",
        "warning": "⚠️ Please select different teams!",
        "vs": "VS",
        "win": "Win",
        "prediction_details": "📈 Prediction Details",
        "team": "Team",
        "predicted_goals": "Predicted Goals",
        "win_probability": "Win Probability",
        "result": "Result",
        "ai_explanation": "🤖 How the AI Works",
        "explanation_text": """This AI prediction model uses:
1. **Team Strength Ratings** - Based on FIFA rankings and historical performance
2. **Probability Calculation** - Computes win probability based on team strength
3. **Score Generation** - Predicts expected goals using statistical distribution

**Note:** This is a simplified model for educational purposes.""",
        "predictions_for": "📅 Predictions are for FIFA World Cup 2026 qualification/tournament matches",
        "generated_on": "Generated on",
        "win_text": "Win",
        "draw_text": "Draw",
        "loss_text": "Loss"
    },
    "Hindi": {
        "title": "⚽ FIFA 2026 AI मैच प्रेडिक्टर",
        "subtitle": "FIFA वर्ल्ड कप 2026 के मैच परिणामों की भविष्यवाणी करें",
        "settings": "📊 भविष्यवाणी सेटिंग्स",
        "team1": "टीम 1 चुनें",
        "team2": "टीम 2 चुनें",
        "warning": "⚠️ कृपया अलग-अलग टीमें चुनें!",
        "vs": "बनाम",
        "win": "जीत",
        "prediction_details": "📈 भविष्यवाणी विवरण",
        "team": "टीम",
        "predicted_goals": "अनुमानित गोल",
        "win_probability": "जीत की संभावना",
        "result": "परिणाम",
        "ai_explanation": "🤖 AI कैसे काम करता है",
        "explanation_text": """यह AI भविष्यवाणी मॉडल उपयोग करता है:
1. **टीम शक्ति रेटिंग** - FIFA रैंकिंग और ऐतिहासिक प्रदर्शन पर आधारित
2. **संभाव्यता गणना** - टीम की शक्ति के आधार पर जीत की संभावना की गणना करता है
3. **स्कोर जनरेशन** - सांख्यिकीय वितरण का उपयोग करके अपेक्षित गोल की भविष्यवाणी करता है

**नोट:** यह शैक्षिक उद्देश्यों के लिए एक सरलीकृत मॉडल है।""",
        "predictions_for": "📅 ये भविष्यवाणियां FIFA विश्व कप 2026 के योग्यता/टूर्नामेंट मैचों के लिए हैं",
        "generated_on": "उत्पन्न",
        "win_text": "जीत",
        "draw_text": "ड्रॉ",
        "loss_text": "हार"
    },
    "Telugu": {
        "title": "⚽ FIFA 2026 AI మ్యాచ్ ప్రెడిక్టర్",
        "subtitle": "FIFA వరల్డ్ కప్ 2026 మ్యాచ్ ఫలితాలను ఊహించండి",
        "settings": "📊 ప్రిడిక్షన్ సెట్టింగ్‌లు",
        "team1": "టీమ్ 1 ఎంచుకోండి",
        "team2": "టీమ్ 2 ఎంచుకోండి",
        "warning": "⚠️ దయచేసి వేర్వేరు టీమ్‌లను ఎంచుకోండి!",
        "vs": "వర్సెస్",
        "win": "గెలుపు",
        "prediction_details": "📈 ప్రిడిక్షన్ వివరాలు",
        "team": "టీమ్",
        "predicted_goals": "అంచనా గోల్‌లు",
        "win_probability": "గెలుపు సంభావ్యత",
        "result": "ఫలితం",
        "ai_explanation": "🤖 AI ఎలా పనిచేస్తుంది",
        "explanation_text": """ఈ AI ప్రిడిక్షన్ మోడల్ ఉపయోగిస్తుంది:
1. **టీమ్ శక్తి రేటింగ్‌లు** - FIFA ర్యాంకింగ్ మరియు చారిత్రక పనితీరుపై ఆధారపడి ఉంటుంది
2. **సంభావ్యత లెక్కింపు** - టీమ్ శక్తి ఆధారంగా గెలుపు సంభావ్యతను లెక్కిస్తుంది
3. **స్కోర్ జనరేషన్** - గణాంక పంపిణీని ఉపయోగించి ఊహించిన గోల్‌లను అంచనా వేస్తుంది

**గమనిక:** ఇది విద్యా ప్రయోజనాల కోసం సరళీకృత నమూనా.""",
        "predictions_for": "📅 ఈ అంచనాలు FIFA ప్రపంచ కప్ 2026 అర్హత/టోర్నమెంట్ మ్యాచ్‌ల కోసం",
        "generated_on": "ఆన్‌లో ఉత్పత్తి చేయబడినది",
        "win_text": "గెలుపు",
        "draw_text": "డ్రా",
        "loss_text": "ఓటమి"
    }
}

# FIFA 2026 Teams
teams = [
    "Argentina", "Belgium", "Brazil", "England", "France", 
    "Germany", "Italy", "Netherlands", "Portugal", "Spain",
    "Mexico", "USA", "Canada", "Japan", "South Korea",
    "Australia", "Uruguay", "Colombia", "Chile", "Peru",
    "Morocco", "Senegal", "Ghana", "Egypt", "Tunisia",
    "Poland", "Denmark", "Croatia", "Czech Republic", "Hungary"
]

teams.sort()

# Language selector in sidebar
st.sidebar.header("🌍 Language / భాష / भाषा")
selected_language = st.sidebar.selectbox("Select Language", list(translations.keys()))

# Get translations for selected language
lang = translations[selected_language]

# Main title and subtitle
st.title(lang["title"])
st.write(lang["subtitle"])

st.sidebar.header(lang["settings"])

# Team selection
col1, col2 = st.columns(2)

with col1:
    team1 = st.selectbox(lang["team1"], teams, index=0)

with col2:
    team2 = st.selectbox(lang["team2"], teams, index=1)

# Prevent same team selection
if team1 == team2:
    st.warning(lang["warning"])
else:
    # Simple AI prediction model
    def predict_match(team1, team2):
        # Team strength scores (simplified based on FIFA rankings)
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
        
        # Get team strengths
        strength1 = team_strength.get(team1, 75)
        strength2 = team_strength.get(team2, 75)
        
        # Calculate win probability
        total = strength1 + strength2
        prob_team1 = strength1 / total
        prob_team2 = strength2 / total
        
        # Generate predicted score
        base_goals1 = prob_team1 * 3
        base_goals2 = prob_team2 * 3
        
        # Add some randomness
        np.random.seed(hash((team1, team2)) % 2**32)
        goals1 = int(np.random.normal(base_goals1, 0.5))
        goals2 = int(np.random.normal(base_goals2, 0.5))
        
        # Ensure non-negative goals
        goals1 = max(0, goals1)
        goals2 = max(0, goals2)
        
        return prob_team1, prob_team2, goals1, goals2
    
    # Make prediction
    prob1, prob2, goals1, goals2 = predict_match(team1, team2)
    
    st.divider()
    
    # Display prediction
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(f"🏆 {team1}", f"{goals1}", f"{lang['win']}: {prob1*100:.1f}%")
    
    with col2:
        st.write("")
        st.write("")
        st.write(f"### {lang['vs']}")
    
    with col3:
        st.metric(f"🏆 {team2}", f"{goals2}", f"{lang['win']}: {prob2*100:.1f}%")
    
    st.divider()
    
    # Prediction details
    st.subheader(lang["prediction_details"])
    
    # Determine result text
    if goals1 > goals2:
        result1 = lang["win_text"]
        result2 = lang["loss_text"]
    elif goals1 < goals2:
        result1 = lang["loss_text"]
        result2 = lang["win_text"]
    else:
        result1 = lang["draw_text"]
        result2 = lang["draw_text"]
    
    pred_data = {
        lang["team"]: [team1, team2],
        lang["predicted_goals"]: [goals1, goals2],
        lang["win_probability"]: [f"{prob1*100:.1f}%", f"{prob2*100:.1f}%"],
        lang["result"]: [result1, result2]
    }
    
    df = pd.DataFrame(pred_data)
    st.dataframe(df, use_container_width=True)
    
    # AI Explanation
    st.subheader(lang["ai_explanation"])
    st.write(lang["explanation_text"])
    
    # Footer
    st.divider()
    st.write(lang["predictions_for"])
    st.write(f"{lang['generated_on']}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")