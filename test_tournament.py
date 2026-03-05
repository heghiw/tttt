from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_flow():
    # configure 
    resp = client.post("/tournament/setup", json={"serves_per_match":11, "player_count":8, "service_change_interval":3})
    assert resp.status_code == 200

    groups = client.get("/tournament/groups").json()
    print("Groups:", groups)
    # verify round number and bracket are attached
    for g in groups:
        assert g.get('round') == 1
        assert g.get('bracket') in ("winner", "loser")
        # ensure player1/player2 exist
        assert 'player1' in g and 'player2' in g

    # report first match (player1 wins) with valid score
    if groups:
        match = groups[0]
        mid = match['id']
        r = client.post("/tournament/match", params={"match_id":mid, "score1":11, "score2":7})
        assert r.status_code == 200
        # now report the same match again so the same loser takes a second loss
        r2 = client.post("/tournament/match", params={"match_id":mid, "score1":12, "score2":8})
        if r2.status_code != 200:
            print("r2 failed", r2.status_code, r2.text)
        assert r2.status_code == 200

    lb = client.get("/tournament/leaderboard").json()
    print("Leaderboard:", lb)
    # ensure there is at least one eliminated player
    assert any(p.get('eliminated', False) for p in lb)

    # also hit readable version and verify formatting
    text = client.get("/tournament/leaderboard/readable").text
    print("Readable leaderboard:\n", text)
    assert "Rank" in text and "Player" in text

    # winners and losers endpoints should also respond
    losers = client.get("/tournament/leaderboard/losers").json()
    # should contain at least those in raw lb
    assert all(any(p['id']==q['id'] for q in losers) for p in lb)
    winners = client.get("/tournament/leaderboard/winners").json()
    print("Winners list:", winners)
    # all winners must not be eliminated
    assert all(not p.get('eliminated', False) for p in winners)

    # basic UI page should be reachable
    ui = client.get("/")
    assert ui.status_code == 200
    assert "Double Elimination" in ui.text
    # basic UI controls should be present
    assert "Initialize" in ui.text
    assert "Refresh" in ui.text
    assert "Player1" in ui.text and "Player2" in ui.text
    assert "submit-score" in ui.text  # score submission button class

    # request groups again; eliminated player(s) should not appear in the new grouping
    new_groups = client.get("/tournament/groups").json()
    # if final bracket there will only be one match with bracket 'final'
    if len(new_groups) == 1 and new_groups[0].get('bracket') == 'final':
        assert new_groups[0].get('round') >= 2
    else:
        # round should increment to 2 now
        for g in new_groups:
            assert g.get('round') == 2
    eliminated_ids = {p['id'] for p in lb}
    # iterate players in returned groups
    for g in new_groups:
        for player in (g['player1'], g['player2']):
            assert player['id'] not in eliminated_ids

if __name__ == '__main__':
    test_flow()
