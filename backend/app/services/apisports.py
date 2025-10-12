import logging
from typing import List, Dict, Any, Optional
import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class ApiSportsService:
    """Thin client for API-Sports provider.

    Notes:
    - API-Sports has separate subdomains per sport.
      football (soccer): https://v3.football.api-sports.io
      basketball:        https://v1.basketball.api-sports.io
      american-football: https://v1.american-football.api-sports.io
    - Requires header: 'x-apisports-key: <KEY>'
    - League/season selection is required for many endpoints; we rely on settings.API_SPORTS_DEFAULTS.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.API_SPORTS_KEY
        if not self.api_key:
            logger.warning("API_SPORTS_KEY not set – API-Sports calls will fail until configured")

    def _base_url_for(self, sport_key: str) -> str:
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key.upper()) or {}
        sport = defaults.get("sport")
        if sport == "football":
            return "https://v3.football.api-sports.io"
        if sport == "basketball":
            return "https://v1.basketball.api-sports.io"
        if sport == "american-football":
            return "https://v1.american-football.api-sports.io"
        raise ValueError(f"Unsupported API-Sports sport key: {sport_key}")

    def _headers(self) -> Dict[str, str]:
        return {"x-apisports-key": self.api_key}

    async def search_players(self, q: str, sport_key: str) -> List[Dict[str, Any]]:
        """Search players across supported sports.

        Returns a list of normalized dicts with minimal fields needed by autocomplete mapping stage.
        """
        if not self.api_key:
            # Provide a clearer failure when key is missing
            raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
        sport_key_up = sport_key.upper()
        base = self._base_url_for(sport_key_up)
        headers = self._headers()
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key_up, {})
        league = defaults.get("league")
        season = defaults.get("season") or None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                if sport_key_up == 'EPL':
                    # Football search: /players?league=39&search=...&season=YYYY
                    params = {"league": league, "search": q}
                    if season:
                        params["season"] = season
                    r = await client.get(f"{base}/players", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", []) if isinstance(payload, dict) else []
                    out = []
                    for item in response_list:
                        player = item.get("player", {})
                        statistics = item.get("statistics", [])
                        team_abbr = None
                        if statistics and isinstance(statistics, list):
                            first_stat = statistics[0]
                            team = first_stat.get("team") or {}
                            team_abbr = team.get("name")  # EPL typically uses full name
                        out.append({
                            "id": player.get("id"),
                            "first_name": player.get("firstname"),
                            "last_name": player.get("lastname"),
                            "team_abbr": team_abbr,
                        })
                    return out
                elif sport_key_up == 'NBA':
                    # Basketball: /players?search=... (league id may be needed for filtering)
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    if season:
                        params["season"] = season
                    r = await client.get(f"{base}/players", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for p in response_list:
                        team_abbr = None
                        teams = p.get("teams") or []
                        if teams:
                            last_team = teams[-1]
                            team_abbr = (last_team.get("team") or {}).get("code") or (last_team.get("team") or {}).get("name")
                        out.append({
                            "id": p.get("id"),
                            "first_name": p.get("firstname") or p.get("firstName"),
                            "last_name": p.get("lastname") or p.get("lastName"),
                            "team_abbr": team_abbr,
                        })
                    return out
                elif sport_key_up == 'NFL':
                    # American football: limited coverage; attempt /players?search=...
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    if season:
                        params["season"] = season
                    r = await client.get(f"{base}/players", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for p in response_list:
                        team_abbr = None
                        team = (p.get("team") or {})
                        team_abbr = team.get("name") or team.get("code")
                        name = (p.get("name") or "").split(" ")
                        first = name[0] if name else None
                        last = " ".join(name[1:]) if len(name) > 1 else None
                        out.append({
                            "id": p.get("id"),
                            "first_name": first,
                            "last_name": last,
                            "team_abbr": team_abbr,
                        })
                    return out
                else:
                    return []
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports player search failed", extra={"sport": sport_key_up, "status": status})
            # Surface auth errors distinctly
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports player search error")
        except httpx.HTTPError as e:
            logger.error("API-Sports player search network error", extra={"sport": sport_key_up, "error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def search_teams(self, q: str, sport_key: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
        sport_key_up = sport_key.upper()
        base = self._base_url_for(sport_key_up)
        headers = self._headers()
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key_up, {})
        league = defaults.get("league")
        season = defaults.get("season") or None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                if sport_key_up == 'EPL':
                    # football: /teams?league=39&search=...
                    params = {"league": league, "search": q}
                    try:
                        r = await client.get(f"{base}/teams", headers=headers, params=params)
                        r.raise_for_status()
                        payload = r.json()
                        response_list = payload.get("response", [])
                    except httpx.HTTPStatusError as e:
                        # Some combinations may error for certain accounts; fallback to search-only
                        if e.response is not None and e.response.status_code in (400, 404):
                            r = await client.get(f"{base}/teams", headers=headers, params={"search": q})
                            r.raise_for_status()
                            payload = r.json()
                            response_list = payload.get("response", [])
                        else:
                            raise
                    out = []
                    for t in response_list:
                        team = t.get("team") or {}
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("name"),
                        })
                    return out
                elif sport_key_up == 'NBA':
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    r = await client.get(f"{base}/teams", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for t in response_list:
                        team = t.get("team") or t
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("nickname") or team.get("name"),
                        })
                    return out
                elif sport_key_up == 'NFL':
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    r = await client.get(f"{base}/teams", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for t in response_list:
                        team = t.get("team") or t
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("name"),
                        })
                    return out
                else:
                    return []
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports team search failed", extra={"sport": sport_key_up, "status": status})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports team search error")
        except httpx.HTTPError as e:
            logger.error("API-Sports team search network error", extra={"sport": sport_key_up, "error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    # --- Football (EPL) basics ---
    async def get_football_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        base = self._base_url_for('EPL')
        headers = self._headers()
        defaults = settings.API_SPORTS_DEFAULTS.get('EPL', {})
        season_param = season or defaults.get('season')
        params = {"id": player_id}
        if season_param:
            params["season"] = season_param
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="EPL player not found")
                item = resp[0]
                player = item.get('player', {})
                stats_list = item.get('statistics') or []
                team_id = None
                team_name = None
                if stats_list:
                    team = (stats_list[0].get('team') or {})
                    team_id = team.get('id')
                    team_name = team.get('name')
                # Normalize first/last split
                first = player.get('firstname') or player.get('firstName')
                last = player.get('lastname') or player.get('lastName')
                return {
                    "id": player.get('id'),
                    "first_name": first,
                    "last_name": last,
                    "position": None,
                    "team": {"id": team_id, "name": team_name, "abbreviation": team_name},
                }
        except httpx.HTTPStatusError as e:
            logger.error("API-Sports EPL player fetch failed", extra={"status": e.response.status_code, "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports EPL player error")
        except httpx.HTTPError as e:
            logger.error("API-Sports EPL player network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_football_team_basic(self, team_id: str) -> Dict[str, Any]:
        base = self._base_url_for('EPL')
        headers = self._headers()
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="EPL team not found")
                team = (resp[0].get('team') or {})
                name = team.get('name')
                code = team.get('code') or name
                return {
                    "id": team.get('id'),
                    "name": name,
                    "abbreviation": code,
                    "city": None,
                    "conference": None,
                    "division": None,
                }
        except httpx.HTTPStatusError as e:
            logger.error("API-Sports EPL team fetch failed", extra={"status": e.response.status_code, "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports EPL team error")
        except httpx.HTTPError as e:
            logger.error("API-Sports EPL team network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")


apisports_service = ApiSportsService()
