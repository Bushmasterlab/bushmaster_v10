{% extends "layout.html" %}
{% block content %}
<section class="panel">
    <h3>{{ title }}</h3>
    <p>This page is now linked and ready. The next version can add live data and tools here.</p>
    <p>Current sample matchup: <b>{{ result.home_team }}</b> vs <b>{{ result.away_team }}</b></p>
</section>
{% endblock %}