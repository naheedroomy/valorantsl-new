import axios, { AxiosResponse } from 'axios';
import { LeaderboardResponse, LeaderboardStats, LeaderboardEntry } from '../types/leaderboard';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling with retry logic
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Log detailed error information
    console.error('API Error:', {
      url: originalRequest?.url,
      method: originalRequest?.method,
      data: originalRequest?.data,
      status: error.response?.status,
      statusText: error.response?.statusText,
      responseData: error.response?.data,
      message: error.message
    });
    
    // Don't retry if we've already retried once
    if (originalRequest && !originalRequest._retry && error.response?.status !== 401) {
      originalRequest._retry = true;
      
      // Wait a bit before retrying
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Retrying request:', originalRequest.url);
      return apiClient(originalRequest);
    }
    
    throw error;
  }
);

export const leaderboardApi = {
  /**
   * Get paginated leaderboard
   */
  getLeaderboard: async (page: number = 1, perPage: number = 50): Promise<LeaderboardResponse> => {
    const response: AxiosResponse<LeaderboardResponse> = await apiClient.get(
      `/api/v1/leaderboard?page=${page}&per_page=${perPage}`
    );
    return response.data;
  },

  /**
   * Get top N players
   */
  getTopPlayers: async (count: number): Promise<LeaderboardEntry[]> => {
    const response: AxiosResponse<LeaderboardEntry[]> = await apiClient.get(
      `/api/v1/leaderboard/top/${count}`
    );
    return response.data;
  },

  /**
   * Search user by discord username
   */
  searchUser: async (username: string): Promise<LeaderboardEntry | null> => {
    const response: AxiosResponse<LeaderboardEntry | null> = await apiClient.get(
      `/api/v1/leaderboard/search/${username}`
    );
    return response.data;
  },

  /**
   * Get leaderboard statistics
   */
  getStats: async (): Promise<LeaderboardStats> => {
    const response: AxiosResponse<LeaderboardStats> = await apiClient.get(
      `/api/v1/leaderboard/stats`
    );
    return response.data;
  },

  /**
   * Health check endpoint
   */
  healthCheck: async (): Promise<any> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

// Registration and Discord OAuth API functions
export const discordAuth = async () => {
  const response = await apiClient.get('/api/v1/auth/login');
  return response.data;
};

export const checkDiscordExists = async (discordId: number) => {
  const response = await apiClient.get(`/api/v1/check-discord/${discordId}`);
  return response.data;
};

export const checkPuuidExists = async (puuid: string) => {
  const response = await apiClient.get(`/api/v1/check-puuid/${puuid}`);
  return response.data;
};

export const previewUserData = async (puuid: string) => {
  const response = await apiClient.get(`/api/v1/preview/${puuid}`);
  return response.data;
};

export const registerUser = async (userData: {
  puuid: string;
  discord_id: number;
  discord_username: string;
}) => {
  const response = await apiClient.post('/api/v1/register', userData);
  return response.data;
};

export default apiClient;