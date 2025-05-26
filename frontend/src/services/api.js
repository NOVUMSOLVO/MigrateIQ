import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => api.post('/auth/login/', { username, password }),
  register: (userData) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
};

// Projects API
export const projectsAPI = {
  getAll: () => api.get('/orchestrator/projects/'),
  getById: (id) => api.get(`/orchestrator/projects/${id}/`),
  create: (projectData) => api.post('/orchestrator/projects/', projectData),
  update: (id, projectData) => api.put(`/orchestrator/projects/${id}/`, projectData),
  delete: (id) => api.delete(`/orchestrator/projects/${id}/`),
  start: (id) => api.post(`/orchestrator/projects/${id}/start/`),
  getProgress: (id) => api.get(`/orchestrator/projects/${id}/progress/`),
};

// Source System API
export const sourceSystemAPI = {
  getAll: () => api.get('/analyzer/source-systems/'),
  getById: (id) => api.get(`/analyzer/source-systems/${id}/`),
  getSchema: (id) => api.get(`/analyzer/source-systems/${id}/schema/`),
};

// Entities API
export const entitiesAPI = {
  getAll: () => api.get('/analyzer/entities/'),
  getById: (id) => api.get(`/analyzer/entities/${id}/`),
  getSampleData: (id) => api.get(`/analyzer/entities/${id}/sample-data/`),
};

// Fields API
export const fieldsAPI = {
  getAll: () => api.get('/analyzer/fields/'),
  getById: (id) => api.get(`/analyzer/fields/${id}/`),
  getStatistics: (id) => api.get(`/analyzer/fields/${id}/statistics/`),
};

// Mappings API
export const mappingsAPI = {
  getAll: () => api.get('/mapping-engine/mappings/'),
  getById: (id) => api.get(`/mapping-engine/mappings/${id}/`),
  create: (mappingData) => api.post('/mapping-engine/mappings/', mappingData),
  update: (id, mappingData) => api.put(`/mapping-engine/mappings/${id}/`, mappingData),
  delete: (id) => api.delete(`/mapping-engine/mappings/${id}/`),
  generate: (data) => api.post('/mapping-engine/mappings/generate/', data),
};

// Field Mappings API
export const fieldMappingsAPI = {
  getAll: () => api.get('/mapping-engine/field-mappings/'),
  getById: (id) => api.get(`/mapping-engine/field-mappings/${id}/`),
  create: (mappingData) => api.post('/mapping-engine/field-mappings/', mappingData),
  update: (id, mappingData) => api.put(`/mapping-engine/field-mappings/${id}/`, mappingData),
  delete: (id) => api.delete(`/mapping-engine/field-mappings/${id}/`),
  verify: (id) => api.post(`/mapping-engine/field-mappings/${id}/verify/`),
};

// Transformation API
export const transformationAPI = {
  getRules: () => api.get('/transformation/rules/'),
  getJobs: () => api.get('/transformation/jobs/'),
  getErrors: () => api.get('/transformation/errors/'),
  createRule: (ruleData) => api.post('/transformation/rules/', ruleData),
  updateRule: (id, ruleData) => api.put(`/transformation/rules/${id}/`, ruleData),
  deleteRule: (id) => api.delete(`/transformation/rules/${id}/`),
  startJob: (id) => api.post(`/transformation/jobs/${id}/start/`),
};

// Validation API
export const validationAPI = {
  getRules: () => api.get('/validation/rules/'),
  getJobs: () => api.get('/validation/jobs/'),
  getErrors: () => api.get('/validation/errors/'),
  createRule: (ruleData) => api.post('/validation/rules/', ruleData),
  updateRule: (id, ruleData) => api.put(`/validation/rules/${id}/`, ruleData),
  deleteRule: (id) => api.delete(`/validation/rules/${id}/`),
  startJob: (id) => api.post(`/validation/jobs/${id}/start/`),
};

export default api;
