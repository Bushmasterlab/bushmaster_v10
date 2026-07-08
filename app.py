{% extends "layout.html" %}
{% set title = "Team Props" %}
{% block content %}
<section class="game-strip">
    <div class="game-card"><b>{{ result.home_code }}</b><span>AT</span><b>{{ result.away_code }}</b><small>Team props</small></div>
</section>
<section class="dashboard-grid">
    <div class="panel"><h3>{{ result.home_team }}</h3><p>Passing yards: <b>{{ result.home_totals.passing_yards }}</b></p><p>Rushing yards: <b>{{ result.home_totals.rushing_yards }}</b></p><p>Rushing TDs: <b>{{ result.home_totals.rushing_tds }}</b></p><p>Receiving yards: <b>{{ result.home_totals.receiving_yards }}</b></p><p>Receiving TDs: <b>{{ result.home_totals.receiving_tds }}</b></p><p>Receptions: <b>{{ result.home_totals.receptions }}</b></p></div>
    <div class="panel"><h3>{{ result.away_team }}</h3><p>Passing yards: <b>{{ result.away_totals.passing_yards }}</b></p><p>Rushing yards: <b>{{ result.away_totals.rushing_yards }}</b></p><p>Rushing TDs: <b>{{ result.away_totals.rushing_tds }}</b></p><p>Receiving yards: <b>{{ result.away_totals.receiving_yards }}</b></p><p>Receiving TDs: <b>{{ result.away_totals.receiving_tds }}</b></p><p>Receptions: <b>{{ result.away_totals.receptions }}</b></p></div>
</section>
{% endblock %}