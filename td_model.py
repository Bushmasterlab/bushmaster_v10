from data.depth_chart_loader import load_depth_chart
from services.playing_time import apply_playing_time

def apply_role_adjustment_to_projection(player, projection):
    depth = load_depth_chart()
    player_id = player.get("player_id") or player.get("id")
    info = depth.get(player_id, {})

    return apply_playing_time(
        projection,
        position=player.get("position"),
        depth_rank=info.get("depth_rank"),
        is_active=info.get("is_active", True),
    )
