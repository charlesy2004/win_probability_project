from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.espn_service import get_live_games

app = FastAPI(title="NBA Win Probability API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "NBA Win Probability API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/games/live")
def live_games():
    return get_live_games()