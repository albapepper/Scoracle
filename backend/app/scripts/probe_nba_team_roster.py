import asyncio
from app.services.apisports import apisports_service

async def main():
    teams = await apisports_service.list_nba_teams(league='standard')
    print(f"teams: {len(teams)} sample: {teams[:5]}")
    if not teams:
        return
    team_id = teams[0]['id']
    print(f"probing roster for team {team_id} with league param...")
    rows = await apisports_service.list_nba_team_players(team_id=team_id, season="2024", league='standard', page=1)
    print(f"with league rows: {len(rows)} sample: {rows[:3]}")
    print(f"probing roster for team {team_id} without league param...")
    rows2 = await apisports_service.list_nba_team_players(team_id=team_id, season="2024", league=None, page=1)
    print(f"without league rows: {len(rows2)} sample: {rows2[:3]}")

if __name__ == "__main__":
    asyncio.run(main())
