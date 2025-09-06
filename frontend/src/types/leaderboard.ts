export interface LeaderboardEntry {
  puuid: string;
  name: string;
  tag: string;
  discord_username: string;
  current_tier: string | null;
  elo: number;  // Always present now since we filter null values
  rank_in_tier?: number | null;
  peak_rank?: string | null;
  peak_season?: string | null;
  last_played_match?: string | null;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface LeaderboardStats {
  total_users: number;
  highest_elo: number;
  lowest_elo: number;
  average_elo: number;
  rank_distribution: Record<string, number>;
}

export interface ApiError {
  message: string;
  status: number;
}