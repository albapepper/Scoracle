"""Simple widget builder service for generating HTML widgets.

Keep it simple - widgets are just HTML strings returned from the backend.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import HTMLResponse


def build_player_basic_widget(entity_info: Dict[str, Any], sport: str) -> str:
    """Build a basic player widget for the mentions page.
    
    Displays: logo/image, name, nationality, college, age, height, weight, team, position
    """
    first = entity_info.get("first_name") or ""
    last = entity_info.get("last_name") or ""
    name = f"{first} {last}".strip() or entity_info.get("name", "Unknown Player")
    
    # Extract fields
    logo_url = entity_info.get("logo_url") or entity_info.get("image") or entity_info.get("photo")
    nationality = entity_info.get("nationality") or entity_info.get("country")
    college = entity_info.get("college") or entity_info.get("university")
    age = entity_info.get("age")
    height = entity_info.get("height")
    weight = entity_info.get("weight")
    position = entity_info.get("position")
    team = entity_info.get("team", {})
    team_name = team.get("name") or team.get("abbreviation") or ""
    
    # Build logo/image HTML
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{name}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; margin-bottom: 1rem;" />'
    
    # Build info rows
    info_rows = []
    if nationality:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Nationality</span><span style="font-weight: 500;">{nationality}</span></div>')
    if college:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">College</span><span style="font-weight: 500;">{college}</span></div>')
    if age:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Age</span><span style="font-weight: 500;">{age}</span></div>')
    if height:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Height</span><span style="font-weight: 500;">{height}</span></div>')
    if weight:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Weight</span><span style="font-weight: 500;">{weight}</span></div>')
    if position:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Position</span><span style="font-weight: 500;">{position}</span></div>')
    if team_name:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Team</span><span style="font-weight: 500;">{team_name}</span></div>')
    
    info_html = "".join(info_rows) if info_rows else '<p style="color: #999; margin-top: 0.5rem;">No additional information available.</p>'
    
    html = f"""
    <div class="widget-basic-player" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            {logo_html}
            <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600; color: #333;">{name}</h3>
        </div>
        <div style="margin-top: 1rem;">
            {info_html}
        </div>
        <p style="margin: 1rem 0 0 0; color: #999; font-size: 0.8rem; text-align: center;">{sport}</p>
    </div>
    """
    return html


def build_team_basic_widget(entity_info: Dict[str, Any], sport: str) -> str:
    """Build a basic team widget for the mentions page.
    
    Displays: logo/image, name, location, league, stadium, division
    """
    name = entity_info.get("name") or "Unknown Team"
    
    # Extract fields
    logo_url = entity_info.get("logo_url") or entity_info.get("image") or entity_info.get("logo")
    city = entity_info.get("city")
    location = city or entity_info.get("location")
    league = entity_info.get("league") or entity_info.get("conference")
    stadium = entity_info.get("stadium") or entity_info.get("venue") or entity_info.get("arena")
    division = entity_info.get("division")
    
    # Build logo/image HTML
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{name}" style="width: 100px; height: 100px; object-fit: contain; margin-bottom: 1rem;" />'
    
    # Build info rows
    info_rows = []
    if location:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Location</span><span style="font-weight: 500;">{location}</span></div>')
    if league:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">League</span><span style="font-weight: 500;">{league}</span></div>')
    if stadium:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Stadium</span><span style="font-weight: 500;">{stadium}</span></div>')
    if division:
        info_rows.append(f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;"><span style="color: #666;">Division</span><span style="font-weight: 500;">{division}</span></div>')
    
    info_html = "".join(info_rows) if info_rows else '<p style="color: #999; margin-top: 0.5rem;">No additional information available.</p>'
    
    html = f"""
    <div class="widget-basic-team" style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            {logo_html}
            <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600; color: #333;">{name}</h3>
        </div>
        <div style="margin-top: 1rem;">
            {info_html}
        </div>
        <p style="margin: 1rem 0 0 0; color: #999; font-size: 0.8rem; text-align: center;">{sport}</p>
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

