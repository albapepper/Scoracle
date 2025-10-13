from typing import Dict, Any

# Mapping from upstream season averages raw keys to expanded names (legacy keys; keep for back-compat)
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
    """Convert a single season average row with short keys into extended key form.

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

def epl_stats_list_to_map(stats_list: Any) -> Dict[str, Any]:
    """Convert EPL season_stats list format [{name, value, ...}, ...] to a flat dict {name: value}.
    If input is already a dict, return as-is.
    """
    if isinstance(stats_list, dict):
        return stats_list
    result: Dict[str, Any] = {}
    if isinstance(stats_list, list):
        for item in stats_list:
            if not isinstance(item, dict):
                continue
            name = item.get('name')
            if not name:
                continue
            result[str(name)] = item.get('value')
    return result

def compute_percentiles_from_cohort(target_values: Dict[str, Any], cohort: Any) -> Dict[str, float]:
    """Compute simple percentiles for numeric keys in target_values using a cohort list of dicts.
    Percentile = proportion of cohort with value <= target value, in 0-100.
    Non-numeric or missing values are ignored.
    """
    if not isinstance(target_values, dict) or not isinstance(cohort, list):
        return {}
    out: Dict[str, float] = {}
    for key, val in target_values.items():
        if not isinstance(val, (int, float)):
            continue
        values = []
        for entry in cohort:
            if not isinstance(entry, dict):
                continue
            v = entry.get(key)
            if isinstance(v, (int, float)):
                values.append(v)
        if not values:
            continue
        rank = sum(1 for v in values if v <= val)
        out[key] = round((rank / len(values)) * 100, 1)
    return out
