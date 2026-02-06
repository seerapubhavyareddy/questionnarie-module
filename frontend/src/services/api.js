import axios from 'axios';

// API Base URL - adjust based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================================================
// Questionnaire API
// ============================================================================

export const questionnaireApi = {
  /**
   * List all questionnaires with pagination and filters
   */
  list: async (params = {}) => {
    const { page = 1, pageSize = 20, search, type, status, sortBy, sortOrder } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (search) queryParams.append('search', search);
    if (type) queryParams.append('type', type);
    if (status) queryParams.append('status', status);
    if (sortBy) queryParams.append('sort_by', sortBy);
    if (sortOrder) queryParams.append('sort_order', sortOrder);
    
    const response = await api.get(`/questionnaires?${queryParams}`);
    return response.data;
  },

  /**
   * Get a single questionnaire by ID
   */
  get: async (id) => {
    const response = await api.get(`/questionnaires/${id}`);
    return response.data;
  },

  /**
   * Create a new questionnaire
   */
  create: async (data) => {
    const response = await api.post('/questionnaires', data);
    return response.data;
  },

  /**
   * Update an existing questionnaire
   */
  update: async (id, data) => {
    const response = await api.put(`/questionnaires/${id}`, data);
    return response.data;
  },

  /**
   * Delete (soft delete) a questionnaire
   */
  delete: async (id) => {
    await api.delete(`/questionnaires/${id}`);
  },

  /**
   * Clone a questionnaire
   */
  clone: async (id, newName = null) => {
    const response = await api.post(`/questionnaires/${id}/clone`, {
      new_name: newName,
    });
    return response.data;
  },

  /**
   * Get version history for a questionnaire
   */
  getVersions: async (id) => {
    const response = await api.get(`/questionnaires/${id}/versions`);
    return response.data;
  },

  /**
   * Bulk delete questionnaires
   */
  bulkDelete: async (ids) => {
    const response = await api.post('/questionnaires/bulk-delete', { ids });
    return response.data;
  },

  /**
   * Bulk update status
   */
  bulkUpdateStatus: async (ids, status) => {
    const response = await api.post('/questionnaires/bulk-status', { ids, status });
    return response.data;
  },

  /**
   * Get available questionnaire types
   */
  getTypes: async () => {
    const response = await api.get('/questionnaires/types/list');
    return response.data;
  },

  /**
   * Get available question types
   */
  getQuestionTypes: async () => {
    const response = await api.get('/questionnaires/question-types/list');
    return response.data;
  },

  /**
   * Calculate score for questionnaire responses
   * @param {number} id - Questionnaire ID
   * @param {object} responses - Map of question ID to answer value
   * @param {array} questions - Optional: current questions (for accurate preview scoring with unsaved changes)
   */
  calculateScore: async (id, responses, questions = null) => {
    const payload = { responses };
    if (questions) {
      payload.questions = questions;
    }
    const response = await api.post(`/questionnaires/${id}/calculate-score`, payload);
    return response.data;
  },

  /**
   * Get scoring configuration for a questionnaire
   */
  getScoringConfig: async (id) => {
    const response = await api.get(`/questionnaires/${id}/scoring-config`);
    return response.data;
  },

  /**
   * Update scoring configuration for a questionnaire
   */
  updateScoringConfig: async (id, scoringConfig) => {
    const response = await api.put(`/questionnaires/${id}/scoring-config`, scoringConfig);
    return response.data;
  },
};

export default api;
