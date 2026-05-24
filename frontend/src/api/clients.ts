import type { Game, TimelinePoint } from "../types/game";

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

export async function saveScoreboardSnapshots(): Promise<{
  message: string;
  count: number;
}> {
  const response = await fetch(`${API_BASE_URL}/games/snapshots`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to save scoreboard snapshots");
  }

  return response.json();
}