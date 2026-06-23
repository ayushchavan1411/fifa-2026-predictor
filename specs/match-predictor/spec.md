# Feature Spec: Match Predictor

## Goal
Predict win probabilities for any two World Cup 2026 teams using historical data.

## User Stories
- As a user, I want to select two teams and see win/draw/loss probabilities.
- As a user, I want AI analysis explaining the prediction.

## Acceptance Criteria
- [ ] Shows win probability for both teams and draw
- [ ] Uses head-to-head history, squad quality, and current form
- [ ] AI explanation available on request

## Technical Notes
Uses historical_data.py for H2H stats, strength scores from squad ratings.
