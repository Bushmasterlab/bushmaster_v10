# Dashboard TD Columns Fix

Your screenshot shows the main dashboard table, not the props page table.
The previous update changed `templates/props.html`, so the columns did not appear on the screen you were looking at.

This fix patches the dashboard template too.

## Changed

- `templates/index.html`
- `templates/props.html` if present
- `static/style.css`

## After installing

Restart Flask:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000/
```

You should see:

- Pass TD
- Rush TD
- Rec TD
- Best TD
