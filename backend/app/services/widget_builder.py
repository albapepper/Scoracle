"""Simple widget builder service for generating HTML widgets.

Keep it simple - widgets are just HTML strings returned from the backend.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import HTMLResponse


def build_basic_widget(entity_type: str, entity_info: Dict[str, Any], sport: str) -> str:
    """Build a basic widget template for the mentions page."""
    name = ""
    if entity_type == "player":
        first = entity_info.get("first_name") or ""
        last = entity_info.get("last_name") or ""
        name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
        position = entity_info.get("position", "")
        team = entity_info.get("team", {})
        team_name = team.get("name") or team.get("abbreviation") or ""
    else:
        name = entity_info.get("name") or "Unknown Team"
        team_name = ""
        position = ""
    
    html = f"""
    <div class="widget-basic" style="padding: 1rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem; font-weight: 600;">{name}</h3>
        {f'<p style="margin: 0.25rem 0; color: #666; font-size: 0.9rem;">{position}</p>' if position else ''}
        {f'<p style="margin: 0.25rem 0; color: #666; font-size: 0.9rem;">{team_name}</p>' if team_name else ''}
        <p style="margin: 0.5rem 0 0 0; color: #999; font-size: 0.8rem;">{sport}</p>
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

