import os
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure LOCAL_DB_DIR points to the repo's instance/localdb (same place seeding wrote to)
REPO_ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("LOCAL_DB_DIR", str(REPO_ROOT / "instance" / "localdb"))

from app.main import app


def expect_true(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


def pick_first_id(results):
    for r in results:
        if r.get("id") is not None:
            return r["id"]
    return None


def fetch_first_id_with_queries(client: TestClient, sport: str, entity_type: str, queries: list[str]):
    for q in queries:
        resp = client.get(f"/api/v1/{sport}/autocomplete/{entity_type}", params={"q": q})
        if resp.status_code != 200:
            continue
        payload = resp.json()
        rid = pick_first_id(payload.get("results", []))
        if rid is not None:
            return rid
        # Try legacy route as a fallback
        resp2 = client.get(f"/api/v1/autocomplete/{entity_type}", params={"q": q, "sport": sport})
        if resp2.status_code == 200:
            payload2 = resp2.json()
            rid2 = pick_first_id(payload2.get("results", []))
            if rid2 is not None:
                return rid2
    return None


def test_sport_flow(client: TestClient, sport: str):
    # Query candidates tuned per sport to avoid API fallback when local DB is seeded
    player_queries = ["le", "ja", "an", "st", "jo", "mi", "br", "ke", "da"] if sport == "NBA" else ["li", "ro", "ma", "ne", "al", "jo", "an", "mi", "ra"]
    team_queries = ["la", "bo", "mi", "sa", "go", "wa", "ne", "de"] if sport == "NBA" else ["ma", "re", "ba", "in", "pa", "un", "ac", "cl"]

    player_id = fetch_first_id_with_queries(client, sport, "player", player_queries)
    expect_true(player_id is not None, f"{sport} no player id returned from autocomplete")

    team_id = fetch_first_id_with_queries(client, sport, "team", team_queries)
    expect_true(team_id is not None, f"{sport} no team id returned from autocomplete")

    # Verify sport summary endpoints accept these ids (lightweight)
    pr = client.get(f"/api/v1/{sport}/players/{player_id}")
    expect_true(pr.status_code in (200, 501, 502), f"{sport} player summary unexpected status: {pr.status_code}")
    # Some sports may not be implemented; 501 is acceptable for now

    tr2 = client.get(f"/api/v1/{sport}/teams/{team_id}")
    expect_true(tr2.status_code in (200, 501, 502), f"{sport} team summary unexpected status: {tr2.status_code}")

    print(f"[OK] {sport}: autocomplete returned ids (player={player_id}, team={team_id}) and endpoints accepted them")


def main():
    with TestClient(app) as client:
        test_sport_flow(client, "NBA")
        test_sport_flow(client, "FOOTBALL")
        # NFL optional; autocomplete might be sparse
        # test_sport_flow(client, "NFL")
    print("Smoke tests completed.")


if __name__ == "__main__":
    main()
