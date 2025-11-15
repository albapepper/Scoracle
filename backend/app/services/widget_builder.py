"""Simple widget builder service for generating HTML widgets.

Keep it simple - widgets are just HTML strings returned from the backend.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import HTMLResponse


def build_player_basic_widget(profile_data: Dict[str, Any], sport: str) -> str:
    """Build a basic player widget displaying all fields from profile endpoint.
    
    Displays all data fields from the API-Sports profile response.
    """
    import json
    
    # Extract logo/image from various possible fields
    logo_url = (profile_data.get("logo") or profile_data.get("logo_url") or 
                profile_data.get("image") or profile_data.get("photo") or
                profile_data.get("player", {}).get("photo") if isinstance(profile_data.get("player"), dict) else None)
    
    # Build logo/image HTML
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="Entity" style="width: 120px; height: 120px; object-fit: contain; border-radius: 8px;" />'
    
    # Helper function to format field values
    def format_value(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return str(value)
    
    # Helper function to format field names
    def format_label(key):
        # Remove "player." prefix if present
        if key.lower().startswith("player."):
            key = key[7:]  # Remove "player." prefix
        # Remove "team." prefix if present
        if key.lower().startswith("team."):
            key = key[5:]  # Remove "team." prefix
        # Special handling for birth fields
        if key.lower() == "birth.country":
            return "Birth Country"
        if key.lower() == "birth.date":
            return "Birth Date"
        if key.lower() == "birth.place":
            return "Birth Place"
        # If key ends with ".name", show just the parent (e.g., "country.name" -> "Country")
        if key.lower().endswith(".name"):
            parent = key.rsplit(".", 1)[0]  # Get everything before ".name"
            return parent.replace("_", " ").replace("-", " ").title()
        return key.replace("_", " ").replace("-", " ").title()
    
    # Build info rows from all fields (excluding nested objects we'll handle separately)
    info_rows = []
    skip_keys = {"id", "logo", "logo_url", "image", "photo", "firstname", "lastname", "name"}  # Skip these as they're handled separately
    
    # Flatten nested structures
    def flatten_dict(d, prefix=""):
        items = []
        for k, v in d.items():
            if k in skip_keys:
                continue
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, key))
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Handle list of objects
                items.append((key, f"[{len(v)} items]"))
            else:
                items.append((key, v))
        return items
    
    # Get all fields
    all_fields = flatten_dict(profile_data)
    
    # Sort fields for consistent display
    all_fields.sort(key=lambda x: x[0])
    
    # Build field cards in horizontal grid layout
    for key, value in all_fields:
        formatted_value = format_value(value)
        if formatted_value and formatted_value not in ("None", "null", ""):
            label = format_label(key)
            info_rows.append(f'<div style="display: flex; flex-direction: column; padding: 0.5rem; min-width: 80px;"><span style="color: #666; font-size: 0.85rem; margin-bottom: 0.25rem;">{label}:</span><span style="font-weight: 500; font-size: 1rem;">{formatted_value}</span></div>')
    
    info_html = "".join(info_rows) if info_rows else '<p style="color: #999; margin-top: 0.5rem;">No additional information available.</p>'
    
    html = f"""
    <div class="widget-basic-player" style="padding: 1rem; display: flex; gap: 1.5rem; align-items: flex-start;">
        {f'<div style="flex-shrink: 0;">{logo_html}</div>' if logo_html else ''}
        <div style="flex: 1; min-width: 0;">
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                {info_html}
            </div>
        </div>
    </div>
    """
    return html


def build_team_basic_widget(profile_data: Dict[str, Any], sport: str) -> str:
    """Build a basic team widget displaying all fields from profile endpoint.
    
    Displays all data fields from the API-Sports profile response.
    """
    import json
    
    # Extract logo/image from various possible fields
    team_obj = profile_data.get("team") if isinstance(profile_data.get("team"), dict) else profile_data
    logo_url = (profile_data.get("logo") or team_obj.get("logo") or 
                profile_data.get("logo_url") or team_obj.get("logo_url") or
                profile_data.get("image") or team_obj.get("image"))
    
    # Build logo/image HTML
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="Entity" style="width: 120px; height: 120px; object-fit: contain; border-radius: 8px;" />'
    
    # Helper function to format field values
    def format_value(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return str(value)
    
    # Helper function to format field names
    def format_label(key):
        # Remove "player." prefix if present
        if key.lower().startswith("player."):
            key = key[7:]  # Remove "player." prefix
        # Remove "team." prefix if present
        if key.lower().startswith("team."):
            key = key[5:]  # Remove "team." prefix
        # Special handling for venue fields
        if key.lower() == "venue.city":
            return "City"
        if key.lower() == "venue.surface":
            return "Field Surface"
        if key.lower() == "venue.capacity":
            return "Stadium Capacity"
        # Special handling for leagues.standard fields
        if key.lower() == "leagues.standard.conference":
            return "Conference"
        if key.lower() == "leagues.standard.division":
            return "Division"
        # If key ends with ".name", show just the parent (e.g., "country.name" -> "Country")
        if key.lower().endswith(".name"):
            parent = key.rsplit(".", 1)[0]  # Get everything before ".name"
            return parent.replace("_", " ").replace("-", " ").title()
        return key.replace("_", " ").replace("-", " ").title()
    
    # Build info rows from all fields
    info_rows = []
    skip_keys = {"id", "logo", "logo_url", "image", "code", "flag", "country_code", "name", "national", "allstar", "nickname", "nbafranchise"}  # Skip these as they're handled separately or not needed
    
    # Flatten nested structures
    def flatten_dict(d, prefix=""):
        items = []
        for k, v in d.items():
            if k in skip_keys:
                continue
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, key))
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Handle list of objects
                items.append((key, f"[{len(v)} items]"))
            else:
                items.append((key, v))
        return items
    
    # Get all fields
    all_fields = flatten_dict(profile_data)
    
    # Sort fields for consistent display
    all_fields.sort(key=lambda x: x[0])
    
    # Build field cards in horizontal grid layout
    skip_patterns = ["code", "flag", "country_code"]  # Skip fields containing these patterns (for team widget)
    skip_exact = ["venue.address", "national", "name", "allstar", "nickname", "nbafranchise"]  # Skip these exact field names
    skip_patterns_extended = ["leagues.utah", "leagues.vegas", "leagues.sacramento"]  # Skip these league patterns
    for key, value in all_fields:
        # Skip exact matches
        if key.lower() in [s.lower() for s in skip_exact]:
            continue
        # Skip if key contains any of the skip patterns (case-insensitive)
        if any(pattern.lower() in key.lower() for pattern in skip_patterns):
            continue
        # Skip league patterns (utah, vegas, sacramento)
        if any(pattern.lower() in key.lower() for pattern in skip_patterns_extended):
            continue
        formatted_value = format_value(value)
        if formatted_value and formatted_value not in ("None", "null", ""):
            label = format_label(key)
            info_rows.append(f'<div style="display: flex; flex-direction: column; padding: 0.5rem; min-width: 80px;"><span style="color: #666; font-size: 0.85rem; margin-bottom: 0.25rem;">{label}:</span><span style="font-weight: 500; font-size: 1rem;">{formatted_value}</span></div>')
    
    info_html = "".join(info_rows) if info_rows else '<p style="color: #999; margin-top: 0.5rem;">No additional information available.</p>'
    
    html = f"""
    <div class="widget-basic-team" style="padding: 1rem; display: flex; gap: 1.5rem; align-items: flex-start;">
        {f'<div style="flex-shrink: 0;">{logo_html}</div>' if logo_html else ''}
        <div style="flex: 1; min-width: 0;">
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                {info_html}
            </div>
        </div>
    </div>
    """
    return html


def build_offense_widget(entity_type: str, entity_info: Dict[str, Any], stats: Dict[str, Any], sport: str) -> str:
    """Build offense widget for EntityPage."""
    name = ""
    if entity_type == "player":
        first = entity_info.get("first_name") or ""
        last = entity_info.get("last_name") or ""
        name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
    else:
        name = entity_info.get("name") or "Unknown Team"
    
    # Extract offense-related stats
    offense_stats = {}
    if stats:
        # Common offense stats across sports
        for key in ["points_per_game", "pts", "goals", "assists", "ast", "goals_assists", "shots", "shots_on_target"]:
            if key in stats:
                offense_stats[key] = stats[key]
    
    stats_html = ""
    if offense_stats:
        stats_html = "<div style='margin-top: 1rem;'>"
        for key, value in offense_stats.items():
            label = key.replace("_", " ").title()
            stats_html += f"<div style='display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;'><span style='color: #666;'>{label}</span><span style='font-weight: 600;'>{value}</span></div>"
        stats_html += "</div>"
    else:
        stats_html = "<p style='color: #999; margin-top: 1rem;'>No offense statistics available.</p>"
    
    html = f"""
    <div class="widget-offense" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600; color: #333;">Offense</h4>
        <h5 style="margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #666;">{name}</h5>
        {stats_html}
    </div>
    """
    return html


def build_defensive_widget(entity_type: str, entity_info: Dict[str, Any], stats: Dict[str, Any], sport: str) -> str:
    """Build defensive widget for EntityPage."""
    name = ""
    if entity_type == "player":
        first = entity_info.get("first_name") or ""
        last = entity_info.get("last_name") or ""
        name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
    else:
        name = entity_info.get("name") or "Unknown Team"
    
    # Extract defensive stats
    defensive_stats = {}
    if stats:
        for key in ["rebounds", "reb", "tackles", "interceptions", "blocks", "blk", "steals", "stl", "clearances", "saves"]:
            if key in stats:
                defensive_stats[key] = stats[key]
    
    stats_html = ""
    if defensive_stats:
        stats_html = "<div style='margin-top: 1rem;'>"
        for key, value in defensive_stats.items():
            label = key.replace("_", " ").title()
            stats_html += f"<div style='display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;'><span style='color: #666;'>{label}</span><span style='font-weight: 600;'>{value}</span></div>"
        stats_html += "</div>"
    else:
        stats_html = "<p style='color: #999; margin-top: 1rem;'>No defensive statistics available.</p>"
    
    html = f"""
    <div class="widget-defensive" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600; color: #333;">Defensive</h4>
        <h5 style="margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #666;">{name}</h5>
        {stats_html}
    </div>
    """
    return html


def build_special_teams_widget(entity_type: str, entity_info: Dict[str, Any], stats: Dict[str, Any], sport: str) -> str:
    """Build special teams/set pieces widget for EntityPage."""
    name = ""
    if entity_type == "player":
        first = entity_info.get("first_name") or ""
        last = entity_info.get("last_name") or ""
        name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
    else:
        name = entity_info.get("name") or "Unknown Team"
    
    # Extract special teams/set pieces stats
    special_stats = {}
    if stats:
        for key in ["free_throws", "ft_pct", "penalties", "penalty_kicks", "corners", "free_kicks", "set_pieces", "field_goals", "fg_pct"]:
            if key in stats:
                special_stats[key] = stats[key]
    
    stats_html = ""
    if special_stats:
        stats_html = "<div style='margin-top: 1rem;'>"
        for key, value in special_stats.items():
            label = key.replace("_", " ").title()
            stats_html += f"<div style='display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;'><span style='color: #666;'>{label}</span><span style='font-weight: 600;'>{value}</span></div>"
        stats_html += "</div>"
    else:
        stats_html = "<p style='color: #999; margin-top: 1rem;'>No special teams/set pieces statistics available.</p>"
    
    html = f"""
    <div class="widget-special-teams" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600; color: #333;">Special Teams / Set Pieces</h4>
        <h5 style="margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #666;">{name}</h5>
        {stats_html}
    </div>
    """
    return html


def build_discipline_widget(entity_type: str, entity_info: Dict[str, Any], stats: Dict[str, Any], sport: str) -> str:
    """Build discipline widget for EntityPage."""
    name = ""
    if entity_type == "player":
        first = entity_info.get("first_name") or ""
        last = entity_info.get("last_name") or ""
        name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
    else:
        name = entity_info.get("name") or "Unknown Team"
    
    # Extract discipline stats
    discipline_stats = {}
    if stats:
        for key in ["fouls", "yellow_cards", "red_cards", "penalties_committed", "turnovers", "turnover", "fouls_committed"]:
            if key in stats:
                discipline_stats[key] = stats[key]
    
    stats_html = ""
    if discipline_stats:
        stats_html = "<div style='margin-top: 1rem;'>"
        for key, value in discipline_stats.items():
            label = key.replace("_", " ").title()
            stats_html += f"<div style='display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;'><span style='color: #666;'>{label}</span><span style='font-weight: 600;'>{value}</span></div>"
        stats_html += "</div>"
    else:
        stats_html = "<p style='color: #999; margin-top: 1rem;'>No discipline statistics available.</p>"
    
    html = f"""
    <div class="widget-discipline" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600; color: #333;">Discipline</h4>
        <h5 style="margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #666;">{name}</h5>
        {stats_html}
    </div>
    """
    return html

