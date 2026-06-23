# AI Agents – FIFA World Cup 2026 Predictor

## ADK Agent
The `fifa_analyst` agent (defined in `fifa_agent.py`) uses the Google Agent Development Kit. It provides:

- `get_current_standings()` – returns group standings from local data.
- `predict_match_outcome(team1, team2)` – predicts winner using strength scores.

When you ask a question in the chat or click "AI World Cup Analysis", the agent:
1. Understands your intent.
2. Decides which tool to call.
3. Returns a structured answer.

## Customisation
To add more tools, modify `fifa_agent.py` and add them to `root_agent.tools`.
