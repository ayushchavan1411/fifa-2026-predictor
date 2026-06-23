# Plan: Match Predictor

## Approach
Combine head-to-head records, ELO-style strength scores, and recent form into a probability model.

## Steps
1. Load historical match data
2. Calculate H2H win rates
3. Blend with squad quality scores
4. Output probability distribution

## Risks
- Limited historical data for some team pairs
