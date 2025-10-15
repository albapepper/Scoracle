from typing import Dict, Any

def build_metrics_group(name: str, stats: Dict[str, Any]):
    """Return a simplified metrics group without percentile data."""
    return {
        'name': name,
        'stats': stats
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
