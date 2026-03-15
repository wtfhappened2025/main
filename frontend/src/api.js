import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = {
  getFeed: (category) => 
    axios.get(`${API}/feed`, { params: { limit: 20, category } }).then(r => r.data),

  getExplanation: (topicId) =>
    axios.get(`${API}/explanation/${topicId}`).then(r => r.data),

  explain: (input) =>
    axios.post(`${API}/explain`, { input }).then(r => r.data),

  getTrending: () =>
    axios.get(`${API}/trending`).then(r => r.data),

  saveTopic: (topicId) =>
    axios.post(`${API}/save/${topicId}`).then(r => r.data),

  getSaved: () =>
    axios.get(`${API}/saved`).then(r => r.data),

  getRenderCard: (topicId, templateType = 'standard') =>
    axios.get(`${API}/render-card/${topicId}`, { params: { template_type: templateType } }).then(r => r.data),

  refreshTrending: () =>
    axios.post(`${API}/refresh-trending`).then(r => r.data),
};

export default api;
