from typing import Dict, Any

# Mapping from upstream balldontlie season averages raw keys to expanded names
SEASON_AVG_KEY_MAP = {
    'min': 'minutes_per_game',
    'pts': 'points_per_game',
    'ast': 'assists_per_game',
    'reb': 'rebounds_per_game',
    'stl': 'steals_per_game',
    'blk': 'blocks_per_game',
    'fg_pct': 'field_goal_percentage',
    'fg3_pct': 'three_point_percentage',
    'ft_pct': 'free_throw_percentage',
    'turnover': 'turnovers_per_game',
}

def normalize_season_average(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single season average row from balldontlie into extended key form.

    Unknown keys are copied through unchanged so we don't silently lose data.
    """
    if not isinstance(raw, dict):
        return raw  # defensive
    out = {}
    for k, v in raw.items():
        # Skip ids / meta fields we don't want on the numeric stat object
        if k in {'player_id'}:
            continue
        mapped = SEASON_AVG_KEY_MAP.get(k, k)
        out[mapped] = v
    return out

def remap_percentile_keys(percentiles: Dict[str, Any]) -> Dict[str, Any]:
    """Remap percentile dictionary using the same mapping so frontend can access expanded names."""
    if not percentiles:
        return percentiles
    remapped = {}
    inverse = {src: dst for src, dst in SEASON_AVG_KEY_MAP.items()}
    for k, v in percentiles.items():
        remapped[inverse.get(k, k)] = v
    return remapped

def build_metrics_group(name: str, stats: Dict[str, Any], percentiles: Dict[str, Any]):
    return {
        'name': name,
        'stats': stats,
        'percentiles': percentiles
    }
