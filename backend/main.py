from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from .models import TournamentConfig, Match, Player
from .storage import state

app = FastAPI(title="Double Elimination Tournament API")

# mount templates/static
import os
BASE_DIR = os.path.dirname(__file__)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/tournament/setup")
def setup(config: TournamentConfig):
    if config.player_count < 2 or config.player_count % 2 != 0:
        raise HTTPException(status_code=400, detail="Player count must be even and at least 2")
    # pass service change interval through
    state.setup(config.serves_per_match, config.player_count, getattr(config, 'service_change_interval', 3))
    return {"message": "Tournament configured", "players": [p.dict() for p in state.players]}


@app.get("/tournament/groups", response_model=List[Match])
def groups():
    try:
        return state.assign_groups()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tournament/match")
def report_match(match_id: int, score1: int, score2: int):
    try:
        state.report_match(match_id, score1, score2)
        return {"message": f"Recorded result for match {match_id}"}
    except ValueError as e:
        # differentiate validation errors from not-found
        msg = str(e)
        status = 400 if "Score does not" in msg or "Tournament not configured" in msg else 404
        raise HTTPException(status_code=status, detail=msg)


@app.get("/tournament/leaderboard", response_model=List[Player])
def leaderboard():
    """Return raw list of eliminated players sorted by total score. (alias for losers)
    """
    return state.leaderboard()


@app.get("/tournament/leaderboard/losers", response_model=List[Player])
def leaderboard_losers():
    """Same as `/tournament/leaderboard` - eliminated players."""
    return state.leaderboard()


@app.get("/tournament/leaderboard/winners", response_model=List[Player])
def leaderboard_winners():
    """Return active (non-eliminated) players sorted by wins (desc) then score."""
    active = [p for p in state.players if not p.eliminated]
    # sort winners by wins descending, then total_score descending
    return sorted(active, key=lambda p: (-p.wins, -p.total_score))


@app.get("/tournament/leaderboard/readable")
def leaderboard_readable():
    """Return a human-readable text leaderboard with ranks."""
    players = state.leaderboard()
    if not players:
        return "No eliminated players yet."
    lines = ["Rank | Player | Losses | Score"]
    lines.append("-----|--------|--------|------")
    for idx, p in enumerate(players, start=1):
        lines.append(f"{idx} | {p.id} | {p.losses} | {p.total_score}")
    return "\n".join(lines)
