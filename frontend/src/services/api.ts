import { config } from '../config/app.config';

// Configuration de l'API
const API_CONFIG = {
  // En dev, utilise le proxy Vite: /api → localhost:8000/api
  // En prod, utilise l'URL complète
  BASE_URL: config.apiUrl ? `${config.apiUrl}/api` : '/api',
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000'),
  DEBUG: config.debug,
};

// Headers par défaut
const getDefaultHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  // Ajouter le token JWT si disponible
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// Fonction générique pour les appels API
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...getDefaultHeaders(),
      ...options.headers,
    },
  };

  try {
    if (API_CONFIG.DEBUG) {
      console.log(`API Call: ${config.method || 'GET'} ${url}`, config.body);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

    const response = await fetch(url, {
      ...config,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    if (API_CONFIG.DEBUG) {
      console.log(`API Response: ${url}`, data);
    }
    
    return data;
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};

export { apiCall, API_CONFIG };