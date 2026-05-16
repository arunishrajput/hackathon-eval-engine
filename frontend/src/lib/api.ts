import axios from 'axios';
import type { Hackathon, Submission, Evaluation, LeaderboardResponse, ChatSession, ChatMessage } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
});

// Attach bearer token from localStorage
api.interceptors.request.use(config => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// On 401: try refresh token once, then redirect to login
let isRefreshing = false;
api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry && typeof window !== 'undefined') {
      original._retry = true;
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            const { data } = await axios.post(`${API_BASE}/v1/auth/refresh`, { refresh_token: refreshToken });
            localStorage.setItem('access_token', data.access_token);
            api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
            isRefreshing = false;
            return api(original);
          }
        } catch {
          isRefreshing = false;
        }
        // No refresh token or refresh failed — clear session and go to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(err);
  }
);

// Auth API
export const authApi = {
  register: async (email: string, password: string, full_name?: string) => {
    const { data } = await api.post('/v1/auth/register', { email, password, full_name });
    return data;
  },

  login: async (email: string, password: string) => {
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);
    const { data } = await api.post('/v1/auth/token', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    return data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Hackathon API
export const hackathonApi = {
  list: async (): Promise<Hackathon[]> => {
    const { data } = await api.get('/v1/hackathons/');
    return data;
  },

  get: async (id: string): Promise<Hackathon> => {
    const { data } = await api.get(`/v1/hackathons/${id}`);
    return data;
  },

  create: async (payload: Partial<Hackathon>): Promise<Hackathon> => {
    const { data } = await api.post('/v1/hackathons/', payload);
    return data;
  },

  update: async (id: string, payload: Partial<Hackathon>): Promise<Hackathon> => {
    const { data } = await api.patch(`/v1/hackathons/${id}`, payload);
    return data;
  },
};

// Submission API
export const submissionApi = {
  create: async (hackathon_id: string, repo_url: string): Promise<Submission> => {
    const { data } = await api.post('/v1/submissions/', { hackathon_id, repo_url });
    return data;
  },

  list: async (): Promise<Submission[]> => {
    const { data } = await api.get('/v1/submissions/');
    return data;
  },

  get: async (id: string): Promise<Submission> => {
    const { data } = await api.get(`/v1/submissions/${id}`);
    return data;
  },

  retry: async (id: string): Promise<Submission> => {
    const { data } = await api.post(`/v1/submissions/${id}/retry`);
    return data;
  },
};

// Evaluation API
export const evaluationApi = {
  get: async (submissionId: string): Promise<Evaluation> => {
    const { data } = await api.get(`/v1/evaluations/${submissionId}`);
    return data;
  },

  getStreamUrl: (submissionId: string): string => {
    return `${API_BASE}/v1/evaluations/${submissionId}/stream`;
  },
};

// Ranking API
export const rankingApi = {
  getLeaderboard: async (hackathonId: string): Promise<LeaderboardResponse> => {
    const { data } = await api.get(`/v1/rankings/${hackathonId}/leaderboard`);
    return data;
  },
};

// Chat API
export const chatApi = {
  createOrGetSession: async (submissionId: string): Promise<ChatSession> => {
    const { data } = await api.post(`/v1/chat/sessions/${submissionId}`);
    return data;
  },

  sendMessage: async (sessionId: string, content: string): Promise<ChatMessage> => {
    const { data } = await api.post(`/v1/chat/sessions/${sessionId}/messages`, { content });
    return data;
  },
};

// Admin API
export const adminApi = {
  listUsers: async () => {
    const { data } = await api.get('/v1/admin/users');
    return data;
  },

  listHackathons: async () => {
    const { data } = await api.get('/v1/admin/hackathons');
    return data;
  },

  listSubmissions: async (hackathonId: string) => {
    const { data } = await api.get(`/v1/admin/hackathons/${hackathonId}/submissions`);
    return data;
  },

  getSubmission: async (submissionId: string) => {
    const { data } = await api.get(`/v1/admin/submissions/${submissionId}`);
    return data;
  },

  transitionStatus: async (hackathonId: string, status: string) => {
    const { data } = await api.patch(`/v1/admin/hackathons/${hackathonId}/status`, { status });
    return data;
  },

  updateCriteria: async (hackathonId: string, criteria: unknown[]) => {
    const { data } = await api.put(`/v1/admin/hackathons/${hackathonId}/criteria`, { criteria });
    return data;
  },

  finalizeRankings: async (hackathonId: string) => {
    const { data } = await api.post(`/v1/admin/hackathons/${hackathonId}/finalize-rankings`);
    return data;
  },
};
