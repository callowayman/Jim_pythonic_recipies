# Script to extract NBA scoreboard data using nba_api and format it into a pandas DataFrame.

import re
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard

def parse_game_clock_to_seconds(game_clock):
    """
    Converts NBA gameClock string (ISO-8601) to seconds remaining.
    Examples:
        'PT04M03.00S' -> 243
        'PT00M43.00S' -> 43
        None / ''     -> 0
    """
    if not game_clock or not isinstance(game_clock, str):
        return 0

    match = re.match(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", game_clock)
    if not match:
        return 0

    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = float(match.group(2)) if match.group(2) else 0.0

    return int(minutes * 60 + seconds)


def parse_game_clock(clock: str) -> str:
    """
    NBA live API returns ISO-8601-ish durations like:
      'PT00M43.00S', 'PT04M03.00S', 'PT0M7.00S'
    Convert to 'M:SS'. If blank/None, return ''.
    """
    if not clock:
        return ""

    # Match minutes + seconds
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(clock).strip())
    if not m:
        return str(clock)

    minutes = int(m.group(1) or 0)
    seconds = int(float(m.group(2) or 0))
    return f"{minutes}:{seconds:02d}"

def compute_score_diff(home_score, away_score):
    """
    Absolute score differential.
    """
    try:
        return abs(int(home_score) - int(away_score))
    except (TypeError, ValueError):
        return 0


def build_nba_scoreboard_df() -> pd.DataFrame:
    sb = scoreboard.ScoreBoard()
    nba_dict = sb.get_dict()

    games = nba_dict.get("scoreboard", {}).get("games", [])
    rows = []

    for g in games:
        home = g.get("homeTeam", {}) or {}
        away = g.get("awayTeam", {}) or {}

        home_team = f"{home.get('teamName', '')} ({home.get('teamTricode', '')})".strip()
        away_team = f"{away.get('teamName', '')} ({away.get('teamTricode', '')})".strip()

        rows.append({
            "home_team": home_team,
            "home_score": home.get("score"),
            "away_team": away_team,
            "away_score": away.get("score"),
            "period": g.get("period"),
            "time_remaining": parse_game_clock(g.get("gameClock")),
            "game_status": g.get("gameStatus"),       # optional but useful
            "game_status_text": g.get("gameStatusText"),
            "secs_left": parse_game_clock_to_seconds(g.get("gameClock")),
            "score_diff": compute_score_diff(home.get("score"), away.get("score"))
        })

    df = pd.DataFrame(rows)

    # Optional: make scores numeric when possible
    for c in ["home_score", "away_score", "period", "game_status"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


if __name__ == "__main__":
    df = build_nba_scoreboard_df()
    print(df)

