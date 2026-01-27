/**
 * Configuration de l'application
 */

export const config = {
  // Mode de l'application: 'mock' ou 'api'
  mode: 'mock' as 'mock' | 'api', // <--- Forcé en mock pour démo locale
  // URL de l'API backend
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  isMockMode: () => true,
  isApiMode: () => false,
};

// Log de la configuration au démarrage
console.log('🔧 Configuration:', {
  mode: config.mode,
  apiUrl: config.apiUrl,
  isMock: config.isMockMode(),
});