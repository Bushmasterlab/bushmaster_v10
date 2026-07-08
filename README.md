{% extends "layout.html" %}
{% set title = "Props Debug" %}
{% block content %}
<section class="panel">
<h3>Props Debug</h3>
<p>Total props: {{ result.props|length }}</p>
<pre>{{ result.props }}</pre>
</section>
{% endblock %}
