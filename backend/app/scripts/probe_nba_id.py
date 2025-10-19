import asyncio
from app.services.apisports import apisports_service

async def main():
    print("player by id probe...")
    r = await apisports_service.get_basketball_player_basic('265')
    print(r)
    print("team by id probe...")
    t = await apisports_service.get_basketball_team_basic('1')
    print(t)

if __name__ == "__main__":
    asyncio.run(main())
