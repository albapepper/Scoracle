import asyncio
from app.services.apisports import apisports_service

async def main():
    print("Probing NBA list_nba_players (season=2024, page=1, league='standard')...")
    rows = await apisports_service.list_nba_players(season="2024", page=1, league='standard')
    print(f"list_nba_players rows: {len(rows)}")
    print("sample:", rows[:5])
    print("\nProbing NBA search_players('lebron', season=2024)...")
    rows2 = await apisports_service.search_players("lebron", "NBA", season_override="2024")
    print(f"search_players rows: {len(rows2)}")
    print("sample:", rows2[:5])

if __name__ == "__main__":
    asyncio.run(main())
