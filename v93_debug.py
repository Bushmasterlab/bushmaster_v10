# V10 TD Percentage Update

This update separates touchdown percentages into:

- `passing_td_percentage`
- `rushing_td_percentage`
- `receiving_td_percentage`
- `td_chance` remains as the best/max TD chance for old templates

## Why

Passing TD and rushing TD should not use the same percentage.

Examples:
- A starting QB can have a strong passing TD chance but lower rushing TD chance.
- A rushing QB can have meaningful rushing TD chance.
- RBs should be driven by carries and red-zone share.
- Backup QBs should be near zero unless expected to play.

## Main file added

```text
services/td_model.py
```

## If your table does not show the new fields

Use these keys in your template:

```jinja2
{{ p.passing_td_percentage }}%
{{ p.rushing_td_percentage }}%
{{ p.receiving_td_percentage }}%
{{ p.td_chance }}%
```

## If predictor.py did not auto-wire

In the function that builds each player projection, add:

```python
from services.td_model import apply_td_percentages
```

Then before returning the player projection dictionary:

```python
projection = apply_td_percentages(player, projection, context)
```
