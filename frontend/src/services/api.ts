// Configuration de l'API
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000'),
  DEBUG: import.meta.env.VITE_DEBUG === 'true',
};

// Headers par défaut
const getDefaultHeaders = () => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  // Ajoutez ici le token d'auth si nécessaire
  // 'Authorization': `Bearer ${getAuthToken()}`
});

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