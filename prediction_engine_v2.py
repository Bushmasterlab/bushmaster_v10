import csv
from pathlib import Path

def load_depth_chart(path="sample_data/depth_chart_v93.csv"):
    path = Path(path)
    if not path.exists():
        return {}

    rows = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            player_id = row.get("player_id")
            if not player_id:
                continue

            rows[player_id] = {
                "depth_rank": int(row.get("depth_rank") or 99),
                "is_active": str(row.get("is_active", "1")).lower() in {"1", "true", "yes", "active"},
            }

    return rows


def get_depth_info(player_id, path="sample_data/depth_chart_v93.csv"):
    return load_depth_chart(path).get(player_id, {})
