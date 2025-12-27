"""Test NBA API endpoints to debug stats fetching."""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_SPORTS_KEY')

async def test():
    headers = {'x-apisports-key': api_key}
    base = 'https://v2.nba.api-sports.io'

    # Test with 'player' param (current implementation)
    print('Test 1: /players/statistics?player=265&season=2024')
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{base}/players/statistics', headers=headers, params={'player': 265, 'season': 2024})
        data = r.json()
        print(f'  Response count: {len(data.get("response", []))}')
        print(f'  Errors: {data.get("errors", "none")}')
        print(f'  Results: {data.get("results", 0)}')

    # Test with 'id' param
    print('\nTest 2: /players/statistics?id=265&season=2024')
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{base}/players/statistics', headers=headers, params={'id': 265, 'season': 2024})
        data = r.json()
        print(f'  Response count: {len(data.get("response", []))}')
        print(f'  Errors: {data.get("errors", "none")}')
        print(f'  Results: {data.get("results", 0)}')
        if data.get("response"):
            print(f'  Sample keys: {list(data["response"][0].keys())[:5]}')

    # Test team stats with 'team' param (old way)
    print('\nTest 3: /teams/statistics?team=17&season=2024')
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{base}/teams/statistics', headers=headers, params={'team': 17, 'season': 2024})
        data = r.json()
        print(f'  Response: {type(data.get("response"))}')
        print(f'  Errors: {data.get("errors", "none")}')
        if data.get("response"):
            resp = data["response"]
            if isinstance(resp, list) and resp:
                print(f'  Sample keys: {list(resp[0].keys())[:5]}')
            elif isinstance(resp, dict):
                print(f'  Sample keys: {list(resp.keys())[:5]}')

    # Test team stats with 'id' param (correct way for NBA)
    print('\nTest 4: /teams/statistics?id=17&season=2024')
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{base}/teams/statistics', headers=headers, params={'id': 17, 'season': 2024})
        data = r.json()
        print(f'  Response: {type(data.get("response"))}')
        print(f'  Errors: {data.get("errors", "none")}')
        if data.get("response"):
            resp = data["response"]
            if isinstance(resp, list) and resp:
                print(f'  Sample keys: {list(resp[0].keys())[:5]}')
            elif isinstance(resp, dict):
                print(f'  Sample keys: {list(resp.keys())[:5]}')

if __name__ == '__main__':
    asyncio.run(test())
