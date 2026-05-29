# NBA Win Probability Dashboard

A full-stack NBA analytics dashboard that tracks live games, play-by-play events, game state, and win probability over time.

**Live App:** [https://win-probability-project-as5nddzel-charlesy2004s-projects.vercel.app/]  
**Backend API:** [https://win-probability-project-1.onrender.com/]

---

## Overview

This project uses live NBA game data to display real-time game context and estimate win probability throughout a game. The dashboard shows current live games, team scores, period and clock, play-by-play events, game state metrics, and a win probability timeline.

The goal of the project is to combine full-stack development, sports analytics, and data engineering into a deployed MVP.

---

## Tech Stack

**Frontend**
- React
- TypeScript
- Vite
- Vercel

**Backend**
- FastAPI
- Python
- Render

**Data / Modeling**
- NBA play-by-play data
- Feature engineering from game state
- Historical model comparison
- Logistic Regression
- XGBoost

---

## Features

- Live NBA game dashboard
- Game cards with current score, period, and clock
- Win probability timeline by game
- Play-by-play event feed
- Game state dashboard with:
  - Score differential
  - Possession
  - Team fouls
  - Bonus status
  - Period
  - Time remaining
- Deployed frontend and backend

---

## Architecture

```text
NBA API / play-by-play data
        ↓
FastAPI backend on Render
        ↓
Game state + win probability endpoints
        ↓
React + TypeScript frontend on Vercel
        ↓
Interactive dashboard