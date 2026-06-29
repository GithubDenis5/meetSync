import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post("/api/v1/auth/refresh", {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Auth ─────────────────────────────────────────────────────

export const authApi = {
  register: (name: string, email: string, password: string) =>
    api.post("/auth/register", { name, email, password }),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
  telegram: (telegram_id: string, username?: string) =>
    api.post("/auth/telegram", { telegram_id, username }),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),
};

// ─── Users ────────────────────────────────────────────────────

export const userApi = {
  getMe: () => api.get("/users/me"),
  updateMe: (data: { name?: string; avatar?: string; timezone?: string }) =>
    api.patch("/users/me", data),
};

// ─── Groups ────────────────────────────────────────────────────

export const groupApi = {
  list: () => api.get("/groups"),
  create: (data: { name: string; description?: string }) =>
    api.post("/groups", data),
  get: (id: number) => api.get(`/groups/${id}`),
  update: (id: number, data: { name?: string; description?: string }) =>
    api.patch(`/groups/${id}`, data),
  delete: (id: number) => api.delete(`/groups/${id}`),
  refreshInvite: (id: number) => api.post(`/groups/${id}/refresh-invite`),
  members: (id: number) => api.get(`/groups/${id}/members`),
  join: (invite_code: string) => api.post("/groups/join", { invite_code }),
  updateRole: (groupId: number, memberId: number, role: string) =>
    api.patch(`/groups/${groupId}/members/${memberId}/role`, { role }),
  removeMember: (groupId: number, memberId: number) =>
    api.delete(`/groups/${groupId}/members/${memberId}`),
};

// ─── Calendar ─────────────────────────────────────────────────────

export const calendarApi = {
  setAvailability: (data: {
    group_id: number;
    date: string;
    status: string;
    start_time?: string;
    end_time?: string;
  }) => api.post("/calendar/availability", data),
  getMyAvailability: (groupId: number, startDate: string, endDate: string) =>
    api.get("/calendar/availability/me", {
      params: { group_id: groupId, start_date: startDate, end_date: endDate },
    }),
  getGroupCalendar: (groupId: number, startDate: string, endDate: string) =>
    api.get("/calendar/availability/group", {
      params: { group_id: groupId, start_date: startDate, end_date: endDate },
    }),
  getUserAvailability: (
    userId: number,
    groupId: number,
    startDate: string,
    endDate: string
  ) =>
    api.get(`/calendar/availability/user/${userId}`, {
      params: { group_id: groupId, start_date: startDate, end_date: endDate },
    }),
  deleteAvailability: (id: number) =>
    api.delete(`/calendar/availability/${id}`),
};

// ─── Ideas ─────────────────────────────────────────────────────

export const ideasApi = {
  list: (groupId: number, archived = false) =>
    api.get("/ideas", { params: { group_id: groupId, archived } }),
  create: (groupId: number, data: {
    title: string;
    description?: string;
    cost?: string;
    category?: string;
    photo_url?: string;
    location?: string;
  }) => api.post("/ideas", data, { params: { group_id: groupId } }),
  get: (id: number) => api.get(`/ideas/${id}`),
  update: (id: number, data: Record<string, unknown>) =>
    api.patch(`/ideas/${id}`, data),
  delete: (id: number) => api.delete(`/ideas/${id}`),
  archive: (id: number) => api.post(`/ideas/${id}/archive`),
  unarchive: (id: number) => api.post(`/ideas/${id}/unarchive`),
  react: (ideaId: number, reaction: string) =>
    api.post(`/ideas/${ideaId}/reactions`, { reaction }),
  reactions: (ideaId: number) => api.get(`/ideas/${ideaId}/reactions`),
  comments: (ideaId: number) => api.get(`/ideas/${ideaId}/comments`),
  addComment: (ideaId: number, text: string) =>
    api.post(`/ideas/${ideaId}/comments`, { text }),
};

// ─── Voting ────────────────────────────────────────────────────

export const votingApi = {
  list: (groupId: number, activeOnly = false) =>
    api.get("/voting", { params: { group_id: groupId, active_only: activeOnly } }),
  create: (data: {
    group_id: number;
    title: string;
    vote_type: string;
    category?: string;
    idea_ids?: number[];
    duration_hours: number;
  }) => api.post("/voting", data),
  get: (id: number) => api.get(`/voting/${id}`),
  cast: (voteId: number, optionId: number) =>
    api.post(`/voting/${voteId}/vote`, { option_id: optionId }),
  result: (voteId: number) => api.get(`/voting/${voteId}/result`),
};

// ─── Meetings ──────────────────────────────────────────────────

export const meetingApi = {
  list: (groupId: number) =>
    api.get("/meetings", { params: { group_id: groupId } }),
  get: (id: number) =>
    api.get(`/meetings/${id}`),
  create: (data: {
    group_id: number;
    title: string;
    description?: string;
    date: string;
    time?: string;
    location?: string;
    idea_id?: number;
  }) => api.post("/meetings", data),
  rsvp: (meetingId: number, status: string) =>
    api.post(`/meetings/${meetingId}/rsvp`, { status }),
  delete: (id: number) =>
    api.delete(`/meetings/${id}`),
  participants: (id: number) =>
    api.get(`/meetings/${id}/participants`),
};

// ─── Recommendations ──────────────────────────────────────────

export const recommendationApi = {
  list: (city: string, category?: string) =>
    api.get("/recommendations", { params: { city, category } }),
  ticketmaster: (city: string, category?: string) =>
    api.get("/recommendations/ticketmaster", { params: { city, category } }),
  weather: (city: string) =>
    api.get("/recommendations/weather", { params: { city } }),
};

// ─── Notifications ────────────────────────────────────────────

export const notificationApi = {
  list: (unreadOnly = false) =>
    api.get("/notifications", { params: { unread_only: unreadOnly } }),
  markRead: (id: number) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
  unreadCount: () => api.get("/notifications/unread-count"),
};
