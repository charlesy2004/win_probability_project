import type { Game, TimelinePoint, LivePlay, GameStateDashboard } from "../types/game";

const API_BASE_URL = "https://humble-pancake-jjv7j7rq76j735v56-8000.app.github.dev";

export async function fetchLiveGames(): Promise<Game[]> {
  const response = await fetch(`${API_BASE_URL}/games/live`);
    if (!response.ok) {
        throw new Error("Failed to fetch games");
    }
    return response.json();
}

export async function fetchWinProbabilityTimeline(gameId: string): Promise<TimelinePoint[]> {
  const response = await fetch(`${API_BASE_URL}/games/${gameId}/win-probability`);
    if (!response.ok) {
        throw new Error("Failed to fetch win probability timeline");
    }
    const data = await response.json();
    return data.timeline ?? data; // Handle both { timeline: [...] } and direct array responses
}

export async function fetchGamePlays(gameId: string): Promise<LivePlay[]> {
  const response = await fetch(`${API_BASE_URL}/games/${gameId}/plays`);

  if (!response.ok) {
    throw new Error("Failed to fetch game plays");
  }

  const data = await response.json();

  return data.plays ?? [];
}

export async function fetchGameState(
  gameId: string
): Promise<GameStateDashboard> {
  const response = await fetch(`${API_BASE_URL}/games/${gameId}/state`);

  if (!response.ok) {
    throw new Error("Failed to fetch game state dashboard");
  }

  return response.json();
}