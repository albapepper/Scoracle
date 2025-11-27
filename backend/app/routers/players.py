"""Player-focused routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.config import settings
from app.services import news_fast
from app.services.apisports import apisports_service
from app.routers._sport_helpers import (
    get_player_info,
    get_player_stats,
    local_player_summary_payload,
    summarize_comentions_for_mentions,
)

router = APIRouter(prefix="/{sport}/players", tags=["players"])


@router.get("/{player_id}")
async def player_summary(sport: str, player_id: str):
    s = sport.upper()
    info = None
    if s == "NBA":
        try:
            info = await apisports_service.get_basketball_player_basic(player_id)
        except Exception:
            info = None
    elif s == "FOOTBALL":
        try:
            info = await apisports_service.get_football_player_basic(player_id)
        except Exception:
            info = None
    elif s == "NFL":
        try:
            info = await apisports_service.get_nfl_player_basic(player_id)
        except Exception:
            info = None
    else:
        raise HTTPException(status_code=501, detail=f"Player summary not implemented for sport {s}")
    if not isinstance(info, dict):
        info = local_player_summary_payload(s, player_id)
    return {"summary": info, "sport": s, "id": player_id}


@router.get("/{player_id}/stats")
async def player_stats(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    if s == "NBA":
        stats = await apisports_service.get_basketball_player_statistics(player_id, season)
    else:
        raise HTTPException(status_code=501, detail=f"Player stats not implemented for sport {s}")
    return {"player_id": player_id, "sport": s, "season": season or "current", "stats": stats}


@router.get("/{player_id}/mentions")
async def player_mentions(sport: str, player_id: str):
    s = sport.upper()
    resolved_name = await news_fast.resolve_entity_name("player", player_id, s)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=s, hours=48, mode="player")
    mentions = result.get("articles", [])
    entity_info = None
    try:
        if s == "NBA":
            entity_info = await apisports_service.get_basketball_player_basic(player_id)
        elif s == "FOOTBALL":
            entity_info = await apisports_service.get_football_player_basic(player_id)
        elif s == "NFL":
            entity_info = await apisports_service.get_nfl_player_basic(player_id)
    except Exception:
        entity_info = None
    if not isinstance(entity_info, dict):
        entity_info = local_player_summary_payload(s, player_id, raise_on_missing=False)
    alongside = summarize_comentions_for_mentions(s, mentions, target_entity=("player", str(player_id)))
    try:
        mentions_sorted = sorted(mentions, key=lambda m: (m.get("pub_ts") or 0), reverse=True)
    except Exception:
        mentions_sorted = mentions
    return {
        "player_id": player_id,
        "sport": s,
        "entity_info": entity_info,
        "mentions": mentions_sorted,
        "alongside_entities": alongside,
        "_debug": {},
        "_echo": {"player_id": player_id},
    }


@router.get("/{player_id}/seasons")
async def player_seasons(sport: str, player_id: str):
    s = sport.upper()
    defaults = settings.API_SPORTS_DEFAULTS.get(s, {})
    season = defaults.get("season") or "current"
    return {"player_id": player_id, "sport": s, "seasons": [str(season)]}


# ===== Widget HTML endpoints =====

@router.get("/{player_id}/widget/basic", response_class=HTMLResponse)
async def player_widget_basic(sport: str, player_id: str):
    s = sport.upper()
    entity_info = await get_player_info(s, player_id)
    from app.services.widget_builder import build_player_basic_widget

    html = build_player_basic_widget(entity_info, s)
    return HTMLResponse(content=html)


@router.get("/{player_id}/widget/offense", response_class=HTMLResponse)
async def player_widget_offense(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_player_info(s, player_id)
    stats = await get_player_stats(s, player_id, season)
    from app.services.widget_builder import build_offense_widget

    html = build_offense_widget("player", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{player_id}/widget/defensive", response_class=HTMLResponse)
async def player_widget_defensive(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_player_info(s, player_id)
    stats = await get_player_stats(s, player_id, season)
    from app.services.widget_builder import build_defensive_widget

    html = build_defensive_widget("player", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{player_id}/widget/special-teams", response_class=HTMLResponse)
async def player_widget_special_teams(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_player_info(s, player_id)
    stats = await get_player_stats(s, player_id, season)
    from app.services.widget_builder import build_special_teams_widget

    html = build_special_teams_widget("player", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{player_id}/widget/discipline", response_class=HTMLResponse)
async def player_widget_discipline(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_player_info(s, player_id)
    stats = await get_player_stats(s, player_id, season)
    from app.services.widget_builder import build_discipline_widget

    html = build_discipline_widget("player", entity_info, stats, s)
    return HTMLResponse(content=html)
