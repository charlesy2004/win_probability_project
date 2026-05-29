import type { Game, TimelinePoint, LivePlay, GameStateDashboard } from "../types/game";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

console.log("API_BASE_URL:", API_BASE_URL);

export async function fetchLiveGames(): Promise<Game[]> {
  const response = await fetch(`${API_BASE_URL}/games/live`);

  if (!response.ok) {
    throw new Error("Failed to fetch games");
  }

  return response.json();
}

export async function fetchWinProbabilityTimeline(
  gameId: string
): Promise<TimelinePoint[]> {
  const response = await fetch(`${API_BASE_URL}/games/${gameId}/win-probability`);

  if (!response.ok) {
    throw new Error("Failed to fetch win probability timeline");
  }

  const data = await response.json();
  return data.timeline ?? data;
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