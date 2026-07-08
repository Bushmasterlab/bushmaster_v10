def role_from_depth(position, depth_rank=None, is_active=True):
    if not is_active:
        return "inactive"

    position = (position or "").upper()

    if depth_rank is None:
        return "unknown"

    try:
        depth_rank = int(depth_rank)
    except (TypeError, ValueError):
        return "unknown"

    if depth_rank <= 1:
        return "starter"

    if position == "QB":
        if depth_rank == 2:
            return "backup_qb"
        return "reserve_qb"

    if position in {"RB", "WR", "TE"}:
        if depth_rank <= 3:
            return "rotation"
        return "reserve"

    return "reserve"


def playing_time_multiplier(position, role):
    position = (position or "").upper()

    if role == "inactive":
        return 0.0

    if role == "starter":
        return 1.0

    if position == "QB":
        if role == "backup_qb":
            return 0.02
        return 0.0

    if role == "rotation":
        return 0.45

    if role == "reserve":
        return 0.10

    return 0.35


def apply_playing_time(projection, position, depth_rank=None, is_active=True):
    role = role_from_depth(position, depth_rank, is_active)
    multiplier = playing_time_multiplier(position, role)

    adjusted = {}
    for key, value in projection.items():
        if isinstance(value, (int, float)):
            adjusted[key] = round(value * multiplier, 2)
        else:
            adjusted[key] = value

    adjusted["role"] = role
    adjusted["playing_time_multiplier"] = multiplier
    return adjusted
