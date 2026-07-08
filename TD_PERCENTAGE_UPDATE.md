from flask import Flask, render_template, request
from predictor import get_team_names, predict_game, dashboard_preview

app = Flask(__name__)


DEFAULT_HOME = "Buffalo Bills"
DEFAULT_AWAY = "Baltimore Ravens"
DEFAULT_SEASON = "auto"


def get_matchup_result():
    teams = get_team_names()
    selected_home = request.values.get("home_team", DEFAULT_HOME)
    selected_away = request.values.get("away_team", DEFAULT_AWAY)
    selected_stats_season = request.values.get("stats_season", DEFAULT_SEASON)
    error = None

    try:
        if selected_home == selected_away:
            error = "Pick two different teams."
            result = dashboard_preview(DEFAULT_HOME, DEFAULT_AWAY, selected_stats_season)
        else:
            result = predict_game(selected_home, selected_away, selected_stats_season)
    except Exception as exc:
        error = f"Prediction error: {exc}"
        result = dashboard_preview(DEFAULT_HOME, DEFAULT_AWAY, DEFAULT_SEASON)

    return {
        "teams": teams,
        "result": result,
        "error": error,
        "selected_home": selected_home,
        "selected_away": selected_away,
        "selected_stats_season": selected_stats_season,
    }


def render_matchup_template(template_name, active_page, title=None, position=None):
    context = get_matchup_result()
    context["active_page"] = active_page
    if title is not None:
        context["title"] = title
    if position is not None:
        context["position"] = position
    return render_template(template_name, **context)


@app.route("/", methods=["GET", "POST"])
def index():
    context = get_matchup_result()
    context["active_page"] = "dashboard"
    return render_template("index.html", **context)


@app.route("/games", methods=["GET", "POST"])
def games():
    return render_matchup_template("games.html", "games", title="Games")


@app.route("/player-props", methods=["GET", "POST"])
def player_props():
    return render_matchup_template("props.html", "player_props", title="All Player Props")


@app.route("/qb-props", methods=["GET", "POST"])
def qb_props():
    return render_matchup_template("props.html", "qb_props", title="Quarterback Props", position="QB")


@app.route("/rb-props", methods=["GET", "POST"])
def rb_props():
    return render_matchup_template("props.html", "rb_props", title="Running Back Props", position="RB")


@app.route("/wr-props", methods=["GET", "POST"])
def wr_props():
    return render_matchup_template("props.html", "wr_props", title="Wide Receiver Props", position="WR")


@app.route("/te-props", methods=["GET", "POST"])
def te_props():
    return render_matchup_template("props.html", "te_props", title="Tight End Props", position="TE")


@app.route("/team-props", methods=["GET", "POST"])
def team_props():
    return render_matchup_template("team_props.html", "team_props", title="Team Props")


@app.route("/betting-edges", methods=["GET", "POST"])
def betting_edges():
    return render_matchup_template("betting_edges.html", "betting_edges", title="Betting Edges")


@app.route("/trends", methods=["GET", "POST"])
def trends():
    return render_matchup_template("simple_page.html", "trends", title="Trends & Insights")


@app.route("/injuries", methods=["GET", "POST"])
def injuries():
    return render_matchup_template("simple_page.html", "injuries", title="Injuries")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    return render_matchup_template("simple_page.html", "settings", title="Settings")



@app.route("/props-debug", methods=["GET", "POST"])
def props_debug():
    return render_matchup_template("props_debug.html", "player_props", title="Props Debug")


if __name__ == "__main__":
    app.run(debug=True)
