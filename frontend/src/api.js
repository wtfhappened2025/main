import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const axiosAuth = axios.create({ baseURL: API });

axiosAuth.interceptors.request.use((config) => {
  const token = localStorage.getItem('wtf_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

axiosAuth.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('wtf_token');
      localStorage.removeItem('wtf_user');
      window.dispatchEvent(new Event('auth_expired'));
    }
    return Promise.reject(err);
  }
);

// Admin axios instance
const axiosAdmin = axios.create({ baseURL: API });
axiosAdmin.interceptors.request.use((config) => {
  const token = localStorage.getItem('wtf_admin_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const api = {
  // Auth
  register: (data) => axios.post(`${API}/auth/register`, data).then(r => r.data),
  login: (data) => axios.post(`${API}/auth/login`, data).then(r => r.data),
  getMe: () => axiosAuth.get('/auth/me').then(r => r.data),
  saveOnboarding: (data) => axiosAuth.put('/auth/onboarding', data).then(r => r.data),
  forgotPassword: (identifier) => axios.post(`${API}/auth/forgot-password`, { identifier }).then(r => r.data),
  resetPassword: (token, new_password) => axios.post(`${API}/auth/reset-password`, { token, new_password }).then(r => r.data),
  updateProfile: (data) => axiosAuth.put('/auth/profile', data).then(r => r.data),
  changePassword: (data) => axiosAuth.put('/auth/change-password', data).then(r => r.data),
  suspendAccount: () => axiosAuth.post('/auth/suspend').then(r => r.data),
  deleteAccount: () => axiosAuth.delete('/auth/delete').then(r => r.data),
  toggleAutoRenew: () => axiosAuth.put('/auth/auto-renew').then(r => r.data),

  // Subscription
  getSubscriptionInfo: () => axiosAuth.get('/subscription/info').then(r => r.data),
  createCheckout: (origin_url) => axiosAuth.post('/subscription/checkout', { origin_url }).then(r => r.data),
  checkPaymentStatus: (sessionId) => axiosAuth.get(`/subscription/status/${sessionId}`).then(r => r.data),

  // Content (public)
  getFeed: (category) => axios.get(`${API}/feed`, { params: { limit: 20, category } }).then(r => r.data),
  getPersonalizedFeed: () => axiosAuth.get('/feed/personalized').then(r => r.data),
  getExplanation: (topicId) => axios.get(`${API}/explanation/${topicId}`).then(r => r.data),
  explain: (input) => axiosAuth.post('/explain', { input }).then(r => r.data),
  getTrending: () => axios.get(`${API}/trending`).then(r => r.data),
  saveTopic: (topicId) => axiosAuth.post(`/save/${topicId}`).then(r => r.data),
  getSaved: () => axiosAuth.get('/saved').then(r => r.data),
  getRenderCard: (topicId, templateType = 'standard') =>
    axios.get(`${API}/render-card/${topicId}`, { params: { template_type: templateType } }).then(r => r.data),
  refreshTrending: () => axios.post(`${API}/refresh-trending`).then(r => r.data),

  // Admin
  adminLogin: (data) => axios.post(`${API}/admin/login`, data).then(r => r.data),
  adminGetStats: () => axiosAdmin.get('/admin/stats').then(r => r.data),
  adminGetUsers: () => axiosAdmin.get('/admin/users').then(r => r.data),
  adminUpdateUserStatus: (userId, status) =>
    axiosAdmin.put(`/admin/users/${userId}/status?status=${status}`).then(r => r.data),
  adminGetPrompts: () => axiosAdmin.get('/admin/prompts').then(r => r.data),
  adminUpdatePrompt: (promptId, data) => axiosAdmin.put(`/admin/prompts/${promptId}`, data).then(r => r.data),
  adminGetTopics: () => axiosAdmin.get('/admin/topics').then(r => r.data),
  adminCreateTopic: (data) => axiosAdmin.post('/admin/topics', data).then(r => r.data),
  adminUpdateTopic: (topicId, data) => axiosAdmin.put(`/admin/topics/${topicId}`, data).then(r => r.data),
  adminDeleteTopic: (topicId) => axiosAdmin.delete(`/admin/topics/${topicId}`).then(r => r.data),

  // Admin - Scheduler & Publisher
  adminGetScheduler: () => axiosAdmin.get('/admin/scheduler').then(r => r.data),
  adminGetPublished: () => axiosAdmin.get('/admin/published').then(r => r.data),
  adminPublishNow: () => axiosAdmin.post('/admin/publish-now').then(r => r.data),
  getSchedulerStatus: () => axios.get(`${API}/scheduler/status`).then(r => r.data),
};

export default api;
