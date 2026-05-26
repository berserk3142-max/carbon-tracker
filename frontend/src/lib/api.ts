import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (token expired)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login/', data),
  register: (data: {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    organization_name: string;
    industry?: string;
  }) => api.post('/auth/register/', data),
  me: () => api.get('/auth/me/'),
};

// Ingestion API
export const ingestionAPI = {
  upload: (file: File, sourceType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);
    return api.post('/ingestion/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getSources: (params?: Record<string, string>) =>
    api.get('/ingestion/sources/', { params }),
  getSource: (id: number) =>
    api.get(`/ingestion/sources/${id}/`),
  getRawRecords: (sourceId: number) =>
    api.get(`/ingestion/sources/${sourceId}/raw_records/`),
};

// Activities API
export const activitiesAPI = {
  list: (params?: Record<string, string>) =>
    api.get('/activities/', { params }),
  get: (id: number) =>
    api.get(`/activities/${id}/`),
  update: (id: number, data: Record<string, unknown>) =>
    api.patch(`/activities/${id}/`, data),
  approve: (id: number, comment?: string) =>
    api.post(`/activities/${id}/approve/`, { comment }),
  reject: (id: number, comment?: string) =>
    api.post(`/activities/${id}/reject/`, { comment }),
  lock: (id: number) =>
    api.post(`/activities/${id}/lock/`),
  bulkApprove: (recordIds: number[], comment?: string) =>
    api.post('/activities/bulk_approve/', { record_ids: recordIds, comment }),
  bulkLock: (recordIds: number[]) =>
    api.post('/activities/bulk_lock/', { record_ids: recordIds }),
  stats: () =>
    api.get('/activities/stats/'),
};

// Audits API
export const auditsAPI = {
  list: (params?: Record<string, string>) =>
    api.get('/audits/', { params }),
  getRecordTrail: (recordId: number) =>
    api.get(`/audits/record/${recordId}/`),
};

export default api;
