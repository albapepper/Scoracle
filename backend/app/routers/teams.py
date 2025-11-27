"""Team-focused routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.services import news_fast
from app.services.apisports import apisports_service
from app.routers._sport_helpers import (
    get_team_info,
    get_team_stats,
    local_team_summary_payload,
    summarize_comentions_for_mentions,
)

router = APIRouter(prefix="/{sport}/teams", tags=["teams"])


@router.get("/{team_id}")
async def team_summary(sport: str, team_id: str):
    s = sport.upper()
    info = None
    if s == "NBA":
        try:
            info = await apisports_service.get_basketball_team_basic(team_id)
        except Exception:
            info = None
    elif s == "FOOTBALL":
        try:
            info = await apisports_service.get_football_team_basic(team_id)
        except Exception:
            info = None
    elif s == "NFL":
        try:
            info = await apisports_service.get_nfl_team_basic(team_id)
        except Exception:
            info = None
    else:
        raise HTTPException(status_code=501, detail=f"Team summary not implemented for sport {s}")
    if not isinstance(info, dict):
        info = local_team_summary_payload(s, team_id)
    return {"summary": info, "sport": s, "id": team_id}


@router.get("/{team_id}/stats")
async def team_stats(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    if s == "NBA":
        stats = await apisports_service.get_basketball_team_statistics(team_id, season)
    else:
        raise HTTPException(status_code=501, detail=f"Team stats not implemented for sport {s}")
    return {"team_id": team_id, "sport": s, "season": season or "current", "stats": stats}


@router.get("/{team_id}/mentions")
async def team_mentions(sport: str, team_id: str):
    s = sport.upper()
    resolved_name = await news_fast.resolve_entity_name("team", team_id, s)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=s, hours=48, mode="team")
    mentions = result.get("articles", [])
    entity_info = None
    try:
        if s == "NBA":
            entity_info = await apisports_service.get_basketball_team_basic(team_id)
        elif s == "FOOTBALL":
            entity_info = await apisports_service.get_football_team_basic(team_id)
        elif s == "NFL":
            entity_info = await apisports_service.get_nfl_team_basic(team_id)
    except Exception:
        entity_info = None
    if not isinstance(entity_info, dict):
        entity_info = local_team_summary_payload(s, team_id, raise_on_missing=False)
    alongside = summarize_comentions_for_mentions(s, mentions, target_entity=("team", str(team_id)))
    try:
        mentions_sorted = sorted(mentions, key=lambda m: (m.get("pub_ts") or 0), reverse=True)
    except Exception:
        mentions_sorted = mentions
    return {
        "team_id": team_id,
        "sport": s,
        "entity_info": entity_info,
        "mentions": mentions_sorted,
        "alongside_entities": alongside,
        "_debug": {},
        "_echo": {"team_id": team_id},
    }


@router.get("/{team_id}/roster")
async def team_roster_stub(sport: str, team_id: str, season: str | None = Query(None)):
    return {"team_id": team_id, "sport": sport.upper(), "season": season or "current", "roster": []}


# ===== Widget HTML endpoints =====

@router.get("/{team_id}/widget/basic", response_class=HTMLResponse)
async def team_widget_basic(sport: str, team_id: str):
    s = sport.upper()
    entity_info = await get_team_info(s, team_id)
    from app.services.widget_builder import build_team_basic_widget

    html = build_team_basic_widget(entity_info, s)
    return HTMLResponse(content=html)


@router.get("/{team_id}/widget/offense", response_class=HTMLResponse)
async def team_widget_offense(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_team_info(s, team_id)
    stats = await get_team_stats(s, team_id, season)
    from app.services.widget_builder import build_offense_widget

    html = build_offense_widget("team", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{team_id}/widget/defensive", response_class=HTMLResponse)
async def team_widget_defensive(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_team_info(s, team_id)
    stats = await get_team_stats(s, team_id, season)
    from app.services.widget_builder import build_defensive_widget

    html = build_defensive_widget("team", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{team_id}/widget/special-teams", response_class=HTMLResponse)
async def team_widget_special_teams(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_team_info(s, team_id)
    stats = await get_team_stats(s, team_id, season)
    from app.services.widget_builder import build_special_teams_widget

    html = build_special_teams_widget("team", entity_info, stats, s)
    return HTMLResponse(content=html)


@router.get("/{team_id}/widget/discipline", response_class=HTMLResponse)
async def team_widget_discipline(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    entity_info = await get_team_info(s, team_id)
    stats = await get_team_stats(s, team_id, season)
    from app.services.widget_builder import build_discipline_widget

    html = build_discipline_widget("team", entity_info, stats, s)
    return HTMLResponse(content=html)
