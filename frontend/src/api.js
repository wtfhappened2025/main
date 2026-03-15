import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with auth interceptor
const axiosAuth = axios.create({ baseURL: API });

axiosAuth.interceptors.request.use((config) => {
  const token = localStorage.getItem('wtf_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
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

const api = {
  // Auth
  register: (data) =>
    axios.post(`${API}/auth/register`, data).then(r => r.data),

  login: (data) =>
    axios.post(`${API}/auth/login`, data).then(r => r.data),

  getMe: () =>
    axiosAuth.get('/auth/me').then(r => r.data),

  saveOnboarding: (data) =>
    axiosAuth.put('/auth/onboarding', data).then(r => r.data),

  // Content
  getFeed: (category) =>
    axios.get(`${API}/feed`, { params: { limit: 20, category } }).then(r => r.data),

  getExplanation: (topicId) =>
    axios.get(`${API}/explanation/${topicId}`).then(r => r.data),

  explain: (input) =>
    axiosAuth.post('/explain', { input }).then(r => r.data),

  getTrending: () =>
    axios.get(`${API}/trending`).then(r => r.data),

  saveTopic: (topicId) =>
    axiosAuth.post(`/save/${topicId}`).then(r => r.data),

  getSaved: () =>
    axiosAuth.get('/saved').then(r => r.data),

  getRenderCard: (topicId, templateType = 'standard') =>
    axios.get(`${API}/render-card/${topicId}`, { params: { template_type: templateType } }).then(r => r.data),

  refreshTrending: () =>
    axios.post(`${API}/refresh-trending`).then(r => r.data),
};

export default api;
