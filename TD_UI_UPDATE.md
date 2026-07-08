from services.td_model import apply_td_percentages
import datetime as dt
import re
from functools import lru_cache

import pandas as pd
import requests


STATS_URLS = [
    "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv",
    "https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{season}.csv",
]

TEAM_CODES = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WSH",
}

ESPN_TEAM_SLUGS = {v: v.lower() for v in TEAM_CODES.values()}
ESPN_TEAM_SLUGS.update({"WSH": "wsh", "LAR": "lar"})

TEAM_ALIASES = {"WSH": {"WSH", "WAS"}, "LAR": {"LAR", "LA"}}
for code in TEAM_CODES.values():
    TEAM_ALIASES.setdefault(code, {code})

TEAM_COLORS = {"BUF": "#0066ff", "BAL": "#8b5cf6", "PHI": "#22c55e", "DAL": "#60a5fa", "KC": "#ef4444", "SF": "#dc2626"}


def get_team_names():
    return sorted(TEAM_CODES.keys())


def clean_name(value):
    value = str(value).lower().replace(".", "").replace("'", "").replace("-", " ")
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"\s+", " ", value).strip()


def first_existing_column(df, choices):
    for col in choices:
        if col in df.columns:
            return col
    return None


def season_candidates(selection):
    if selection and selection != "auto":
        return [int(selection)]
    year = dt.date.today().year
    return [year, year - 1, year - 2]


def empty_stats_df(season):
    df = pd.DataFrame(columns=[
        "bm_player_name", "bm_clean_name", "bm_team", "bm_position", "week",
        "rushing_tds", "receiving_tds", "passing_tds", "carries", "receptions", "targets",
        "rushing_yards", "receiving_yards", "passing_yards", "attempts", "completions", "interceptions",
        "redzone_carries", "redzone_targets", "red_zone_carries", "red_zone_targets",
    ])
    df["bm_source_season"] = season
    return df


@lru_cache(maxsize=8)
def load_weekly_stats(selection="auto"):
    last_error = None

    for season in season_candidates(selection):
        for template in STATS_URLS:
            url = template.format(season=season)
            try:
                df = pd.read_csv(url)
                df["bm_source_season"] = season
                return normalize_stats(df, season, True, "")
            except Exception as exc:
                last_error = exc

        if selection != "auto":
            return normalize_stats(empty_stats_df(season), season, False, f"No stats file found for {season} yet.")

    season = season_candidates(selection)[0]
    return normalize_stats(empty_stats_df(season), season, False, f"Could not load nflverse stats. Last error: {last_error}")


def normalize_stats(df, season, available, message):
    df = df.copy()

    name_col = first_existing_column(df, ["player_display_name", "player_name", "full_name", "name", "gsis_name"])
    team_col = first_existing_column(df, ["recent_team", "team", "posteam", "club_code"])
    pos_col = first_existing_column(df, ["position", "position_group", "pos"])

    if name_col:
        df["bm_player_name"] = df[name_col].astype(str)
        df["bm_clean_name"] = df["bm_player_name"].apply(clean_name)
    else:
        df["bm_player_name"] = df.get("bm_player_name", "")
        df["bm_clean_name"] = df.get("bm_clean_name", "")

    df["bm_team"] = df[team_col].astype(str).str.upper() if team_col else df.get("bm_team", "")
    df["bm_position"] = df[pos_col].astype(str).str.upper() if pos_col else df.get("bm_position", "")

    for col in [
        "week", "rushing_tds", "receiving_tds", "passing_tds", "carries", "receptions", "targets",
        "rushing_yards", "receiving_yards", "passing_yards", "attempts", "completions", "interceptions",
        "redzone_carries", "redzone_targets", "red_zone_carries", "red_zone_targets",
    ]:
        if col not in df.columns:
            df[col] = 0

    df.attrs["source_season"] = season
    df.attrs["available"] = available
    df.attrs["message"] = message
    return df


@lru_cache(maxsize=64)
def get_roster_players(team_name):
    team_code = TEAM_CODES[team_name]
    slug = ESPN_TEAM_SLUGS[team_code]
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{slug}/roster"
    players = []
    allowed = {"QB", "RB", "WR", "TE"}

    try:
        data = requests.get(url, timeout=15).json()
        for group in data.get("athletes", []):
            for item in group.get("items", []):
                name = item.get("displayName") or item.get("fullName") or item.get("name")
                pos = str(item.get("position", {}).get("abbreviation", "")).upper()
                if name and pos in allowed:
                    players.append({"name": name, "clean_name": clean_name(name), "team": team_name, "team_code": team_code, "position": pos})
    except Exception:
        pass

    unique = {}
    for p in players:
        unique[p["clean_name"]] = p
    return list(unique.values())


def safe_sum(df, column):
    if column not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def fallback_stats(source_season):
    return {
        "matched": False, "games": 0, "tds": 0,
        "passing_yards_total": 0, "passing_tds_total": 0, "attempts_total": 0, "completions_total": 0, "interceptions_total": 0,
        "carries_total": 0, "rushing_yards_total": 0, "rushing_tds_total": 0,
        "receptions_total": 0, "targets_total": 0, "receiving_yards_total": 0, "receiving_tds_total": 0,
        "touches": 0, "targets": 0, "redzone": 0, "usage_score": 0, "source_season": source_season,
    }


def recent_stats(player, stats_df, weeks=6):
    source_season = stats_df.attrs.get("source_season", dt.date.today().year)
    if stats_df.empty:
        return fallback_stats(source_season)

    aliases = TEAM_ALIASES.get(player["team_code"], {player["team_code"]})
    rows = stats_df[(stats_df["bm_clean_name"] == player["clean_name"]) & (stats_df["bm_team"].isin(aliases))].copy()
    if rows.empty:
        rows = stats_df[stats_df["bm_clean_name"] == player["clean_name"]].copy()
    if rows.empty:
        return fallback_stats(source_season)

    rows = rows.sort_values("week").tail(weeks)
    games = max(int(len(rows)), 1)

    passing_yards = safe_sum(rows, "passing_yards")
    passing_tds = safe_sum(rows, "passing_tds")
    attempts = safe_sum(rows, "attempts")
    completions = safe_sum(rows, "completions")
    interceptions = safe_sum(rows, "interceptions")
    carries = safe_sum(rows, "carries")
    rushing_yards = safe_sum(rows, "rushing_yards")
    rushing_tds = safe_sum(rows, "rushing_tds")
    receptions = safe_sum(rows, "receptions")
    targets = safe_sum(rows, "targets")
    receiving_yards = safe_sum(rows, "receiving_yards")
    receiving_tds = safe_sum(rows, "receiving_tds")
    redzone = safe_sum(rows, "redzone_carries") + safe_sum(rows, "redzone_targets") + safe_sum(rows, "red_zone_carries") + safe_sum(rows, "red_zone_targets")

    total_tds = rushing_tds + receiving_tds + passing_tds
    touches = carries + receptions
    usage_score = ((total_tds / games) * 25 + (touches / games) * 1.9 + (targets / games) * 2.2 +
                   ((rushing_yards + receiving_yards + passing_yards * 0.20) / games) * 0.10 + (redzone / games) * 4.5)

    return {
        "matched": True, "games": games, "tds": int(total_tds),
        "passing_yards_total": int(passing_yards), "passing_tds_total": int(passing_tds),
        "attempts_total": int(attempts), "completions_total": int(completions), "interceptions_total": int(interceptions),
        "carries_total": int(carries), "rushing_yards_total": int(rushing_yards), "rushing_tds_total": int(rushing_tds),
        "receptions_total": int(receptions), "targets_total": int(targets),
        "receiving_yards_total": int(receiving_yards), "receiving_tds_total": int(receiving_tds),
        "touches": int(touches), "targets": int(targets), "redzone": int(redzone),
        "usage_score": round(usage_score, 1), "source_season": source_season,
    }


def per_game(player, key):
    return player.get(key, 0) / max(player.get("games", 0), 1)


def fallback_projection(pos):
    if pos == "QB":
        return {"passing_yards": 185, "passing_tds": 1.1, "completions": 18.5, "attempts": 29.0, "interceptions": 0.7, "rushing_attempts": 2.5, "rushing_yards": 10, "rushing_tds": 0.1, "receptions": 0, "targets": 0, "receiving_yards": 0, "receiving_tds": 0}
    if pos == "RB":
        return {"passing_yards": 0, "passing_tds": 0, "completions": 0, "attempts": 0, "interceptions": 0, "rushing_attempts": 4.0, "rushing_yards": 16, "rushing_tds": 0.1, "receptions": 0.8, "targets": 1.1, "receiving_yards": 6, "receiving_tds": 0.0}
    if pos == "WR":
        return {"passing_yards": 0, "passing_tds": 0, "completions": 0, "attempts": 0, "interceptions": 0, "rushing_attempts": 0.1, "rushing_yards": 1, "rushing_tds": 0.0, "receptions": 1.4, "targets": 2.2, "receiving_yards": 16, "receiving_tds": 0.1}
    return {"passing_yards": 0, "passing_tds": 0, "completions": 0, "attempts": 0, "interceptions": 0, "rushing_attempts": 0.0, "rushing_yards": 0, "rushing_tds": 0.0, "receptions": 0.9, "targets": 1.4, "receiving_yards": 9, "receiving_tds": 0.1}


def project_player_props(player):
    if not player["matched"]:
        return fallback_projection(player["position"])

    lift = 1.05 if player["usage_score"] >= 8 else 0.95
    projection = {
        "passing_yards": round(per_game(player, "passing_yards_total") * lift),
        "passing_tds": round(per_game(player, "passing_tds_total") * lift, 1),
        "completions": round(per_game(player, "completions_total") * lift, 1),
        "attempts": round(per_game(player, "attempts_total") * lift, 1),
        "interceptions": round(per_game(player, "interceptions_total"), 1),
        "rushing_attempts": round(per_game(player, "carries_total") * lift, 1),
        "rushing_yards": round(per_game(player, "rushing_yards_total") * lift),
        "rushing_tds": round(per_game(player, "rushing_tds_total") * lift, 1),
        "receptions": round(per_game(player, "receptions_total") * lift, 1),
        "targets": round(per_game(player, "targets_total") * lift, 1),
        "receiving_yards": round(per_game(player, "receiving_yards_total") * lift),
        "receiving_tds": round(per_game(player, "receiving_tds_total") * lift, 1),
    }
    if player["position"] != "QB":
        for k in ["passing_yards", "passing_tds", "completions", "attempts", "interceptions"]:
            projection[k] = 0
    return projection


def player_role(player):
    """Estimate a realistic role from position, recent usage, and matched stats.

    This prevents backup QBs and low-usage reserves from being treated like starters.
    """
    pos = player.get("position", "")
    if not player.get("matched"):
        return "reserve_qb" if pos == "QB" else "reserve"

    games = max(player.get("games", 0), 1)
    attempts_pg = player.get("attempts_total", 0) / games
    carries_pg = player.get("carries_total", 0) / games
    targets_pg = player.get("targets_total", 0) / games
    touches_pg = player.get("touches", 0) / games

    if pos == "QB":
        if attempts_pg >= 18:
            return "starter"
        if attempts_pg >= 4:
            return "backup_qb"
        return "reserve_qb"

    if pos == "RB":
        if carries_pg >= 8 or touches_pg >= 10:
            return "starter"
        if touches_pg >= 4:
            return "rotation"
        return "reserve"

    if pos in {"WR", "TE"}:
        if targets_pg >= 5:
            return "starter"
        if targets_pg >= 2:
            return "rotation"
        return "reserve"

    return "reserve"


def role_multiplier(role):
    return {
        "starter": 1.00,
        "rotation": 0.55,
        "backup_qb": 0.02,
        "reserve_qb": 0.00,
        "reserve": 0.15,
        "inactive": 0.00,
    }.get(role, 0.35)


def confidence_for_role(player, role):
    games = max(player.get("games", 0), 0)
    score = 45 + min(games, 8) * 5
    if role == "starter":
        score += 15
    elif role == "rotation":
        score += 5
    elif role in {"backup_qb", "reserve_qb", "reserve"}:
        score -= 25
    return max(5, min(95, int(score)))


def td_chance(player):
    pos = player["position"]
    role = player.get("role") or player_role(player)
    mult = role_multiplier(role)

    if role in {"reserve_qb", "inactive"}:
        return 0
    if role == "backup_qb":
        return 1
    if not player["matched"]:
        return int({"QB": 4, "RB": 3, "WR": 3, "TE": 3}.get(pos, 1) * mult)

    games = max(player["games"], 1)
    td_pg = player["tds"] / games
    touch_pg = player["touches"] / games
    target_pg = player["targets"] / games
    rz_pg = player["redzone"] / games
    yards_pg = (player["rushing_yards_total"] + player["receiving_yards_total"] + player["passing_yards_total"] * 0.20) / games

    chance = {"QB": 5, "RB": 7, "WR": 6, "TE": 5}.get(pos, 2) + td_pg * 20
    if pos == "QB":
        chance += min(touch_pg * 0.9, 10) + min(yards_pg * 0.035, 8) + rz_pg * 2.5
    elif pos == "RB":
        chance += min(touch_pg * 1.55, 30) + min(target_pg * 0.7, 5) + rz_pg * 4.5
    elif pos == "WR":
        chance += min(target_pg * 2.8, 26) + min(touch_pg * 1.2, 8) + rz_pg * 4.0
    elif pos == "TE":
        chance += min(target_pg * 2.5, 22) + min(touch_pg * 1.1, 8) + rz_pg * 4.2
    return int(max(0, min(round(chance * mult), 85)))


def add_td_percentages(player):
    """Attach separate passing/rushing/receiving TD percentages to a player and its projection."""
    proj = player.get("projection", {})
    role = player.get("role") or player_role(player)
    games = max(player.get("games", 0), 1)
    context = {
        "team_points": 21.0,
        "red_zone_share": min(1.0, (player.get("redzone", 0) / games) / 6),
        "pass_attempts": player.get("attempts_total", 0) / games,
        "carries": player.get("carries_total", 0) / games,
        "targets": player.get("targets_total", 0) / games,
    }
    player_stub = {
        "position": player.get("position"),
        "role": role,
        "team_points": context["team_points"],
        "red_zone_share": context["red_zone_share"],
        "pass_attempts": context["pass_attempts"],
        "carries": context["carries"],
        "targets": context["targets"],
    }
    proj["role"] = role
    proj = apply_td_percentages(player_stub, proj, context)
    player["projection"] = proj
    player["passing_td_percentage"] = proj.get("passing_td_percentage", 0)
    player["rushing_td_percentage"] = proj.get("rushing_td_percentage", 0)
    player["receiving_td_percentage"] = proj.get("receiving_td_percentage", 0)
    player["td_chance"] = proj.get("td_chance", player.get("td_chance", 0))
    player["confidence"] = confidence_for_role(player, role)
    player["role"] = role
    return player


def build_team(team_name, stats_df):
    players = []
    for base in get_roster_players(team_name):
        stats = recent_stats(base, stats_df)
        p = {**base, **stats}
        p["role"] = player_role(p)
        p["projection"] = project_player_props(p)

        # Scale projection by expected playing time.
        mult = role_multiplier(p["role"])
        for key, value in list(p["projection"].items()):
            if isinstance(value, (int, float)):
                p["projection"][key] = round(value * mult, 1)

        p["td_chance"] = td_chance(p)
        p = add_td_percentages(p)
        players.append(p)

    players.sort(key=lambda x: (x["td_chance"], x["usage_score"], x["matched"]), reverse=True)
    limits = {"QB": 2, "RB": 4, "WR": 6, "TE": 3}
    counts = {k: 0 for k in limits}
    kept = []
    for p in players:
        pos = p["position"]
        if counts[pos] >= limits[pos]:
            continue
        # Keep starters/rotation. Avoid filling pages with zero-projection reserves.
        if p.get("role") in {"reserve_qb", "inactive"} and counts[pos] >= 1:
            continue
        if not p["matched"] and len(kept) >= 8:
            continue
        kept.append(p)
        counts[pos] += 1
        if len(kept) >= 14:
            break
    return kept


def implied_score(players):
    return int(round(14 + (sum(p["td_chance"] for p in players[:8]) / 100) * 7))


def team_totals(players):
    return {
        "passing_yards": round(sum(p["projection"]["passing_yards"] for p in players if p["position"] == "QB")),
        "rushing_yards": round(sum(p["projection"]["rushing_yards"] for p in players)),
        "rushing_tds": round(sum(p["projection"]["rushing_tds"] for p in players), 1),
        "receiving_yards": round(sum(p["projection"]["receiving_yards"] for p in players)),
        "receiving_tds": round(sum(p["projection"]["receiving_tds"] for p in players), 1),
        "receptions": round(sum(p["projection"]["receptions"] for p in players), 1),
    }


def win_probs(home_score, away_score):
    home = max(5, min(95, 50 + (home_score - away_score) * 3))
    return int(home), int(100 - home)


def make_prop(player, prop, value, edge):
    proj = player.get("projection", {})
    return {
        "player": player.get("name"),
        "name": player.get("name"),
        "team": player.get("team_code"),
        "position": player.get("position"),
        "pos": player.get("position"),
        "role": player.get("role", ""),
        "prop": prop,
        "market": prop,
        "value": value,
        "projection": value,
        "bushmaster_proj": value,
        "edge": edge,
        "confidence": "★" * max(1, min(5, round(player.get("confidence", 50) / 20))) + "☆" * max(0, 5 - max(1, min(5, round(player.get("confidence", 50) / 20)))),
        "confidence_score": player.get("confidence", 50),
        "td_chance": player.get("td_chance", 0),
        "passing_td_percentage": player.get("passing_td_percentage", 0),
        "rushing_td_percentage": player.get("rushing_td_percentage", 0),
        "receiving_td_percentage": player.get("receiving_td_percentage", 0),
    }


def top_props(players, limit=40):
    props = []
    for p in players:
        proj = p["projection"]
        if p["position"] == "QB":
            props.append(make_prop(p, "Passing Yards", proj["passing_yards"], round(proj["passing_yards"] * 0.04, 1)))
            props.append(make_prop(p, "Passing TD%", p.get("passing_td_percentage", 0), round(p.get("passing_td_percentage", 0) * 0.08, 1)))
            props.append(make_prop(p, "Rushing TD%", p.get("rushing_td_percentage", 0), round(p.get("rushing_td_percentage", 0) * 0.08, 1)))
        if p["position"] == "RB":
            props.append(make_prop(p, "Rushing Yards", proj["rushing_yards"], round(proj["rushing_yards"] * 0.05, 1)))
            props.append(make_prop(p, "Rushing TD%", p.get("rushing_td_percentage", 0), round(p.get("rushing_td_percentage", 0) * 0.08, 1)))
        if p["position"] in {"WR", "TE", "RB"}:
            props.append(make_prop(p, "Receptions", proj["receptions"], round(proj["receptions"] * 0.10, 1)))
            props.append(make_prop(p, "Receiving Yards", proj["receiving_yards"], round(proj["receiving_yards"] * 0.05, 1)))
            props.append(make_prop(p, "Receiving TD%", p.get("receiving_td_percentage", 0), round(p.get("receiving_td_percentage", 0) * 0.08, 1)))
    return sorted(props, key=lambda x: x["edge"], reverse=True)[:limit]


def predict_game(home_team, away_team, stats_selection="auto"):
    stats_df = load_weekly_stats(stats_selection)
    home_players = build_team(home_team, stats_df)
    away_players = build_team(away_team, stats_df)

    home_score = implied_score(home_players)
    away_score = implied_score(away_players)
    home_win, away_win = win_probs(home_score, away_score)
    all_players = home_players + away_players
    props = top_props(all_players, limit=60)

    return {
        "home_team": home_team, "away_team": away_team,
        "home_code": TEAM_CODES[home_team], "away_code": TEAM_CODES[away_team],
        "home_color": TEAM_COLORS.get(TEAM_CODES[home_team], "#38bdf8"),
        "away_color": TEAM_COLORS.get(TEAM_CODES[away_team], "#a78bfa"),
        "home_score": home_score, "away_score": away_score,
        "home_tds": max(1, round(home_score / 7)), "away_tds": max(1, round(away_score / 7)),
        "home_win": home_win, "away_win": away_win,
        "home_players": home_players, "away_players": away_players,
        "home_totals": team_totals(home_players), "away_totals": team_totals(away_players),
        "stats_selection": stats_selection,
        "stats_source_season": stats_df.attrs.get("source_season"),
        "stats_available": stats_df.attrs.get("available", False),
        "stats_message": stats_df.attrs.get("message", ""),
        "roster_source": "ESPN live roster",
        "top_props": props[:8],
        "props": props,
        "best_td": sorted(all_players, key=lambda p: p["td_chance"], reverse=True)[:5],
        "updated": dt.datetime.now().strftime("%b %d, %Y %I:%M %p"),
    }

def dashboard_preview(home_team="Buffalo Bills", away_team="Baltimore Ravens", stats_selection="auto"):
    return predict_game(home_team, away_team, stats_selection)

# V10 TD percentage helper
def apply_v10_td_percentages(player, projection, context=None):
    return apply_td_percentages(player, projection, context or {})
