<form method="POST" class="game-form">
    <label>Home Team
        <select name="home_team">
            {% for team in teams %}
            <option value="{{ team }}" {% if team == selected_home %}selected{% endif %}>{{ team }}</option>
            {% endfor %}
        </select>
    </label>

    <label>Away Team
        <select name="away_team">
            {% for team in teams %}
            <option value="{{ team }}" {% if team == selected_away %}selected{% endif %}>{{ team }}</option>
            {% endfor %}
        </select>
    </label>

    <label>Stats Season
        <select name="stats_season">
            <option value="auto" {% if selected_stats_season == "auto" %}selected{% endif %}>Auto</option>
            <option value="2026" {% if selected_stats_season == "2026" %}selected{% endif %}>2026</option>
            <option value="2025" {% if selected_stats_season == "2025" %}selected{% endif %}>2025</option>
            <option value="2024" {% if selected_stats_season == "2024" %}selected{% endif %}>2024</option>
        </select>
    </label>

    <button type="submit">Run Prediction</button>
</form>

{% if error %}
<div class="warning">{{ error }}</div>
{% endif %}

{% if result.stats_message %}
<div class="warning">{{ result.stats_message }}</div>
{% endif %}
