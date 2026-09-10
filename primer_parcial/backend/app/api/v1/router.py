from fastapi import APIRouter
from app.api.v1 import auth, tournaments, teams, players, matches, stats, standings, public

api_router = APIRouter()

api_router.include_router(public.router, prefix="/public", tags=["Public (Mobile-First)"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tournaments.router, prefix="/tournaments", tags=["Tournaments"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches & Results"])
api_router.include_router(stats.router, prefix="/stats", tags=["Player Stats & Scorers"])
api_router.include_router(standings.router, prefix="/standings", tags=["Standings Leaderboard"])
