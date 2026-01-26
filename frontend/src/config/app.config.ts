/**
 * Configuration de l'application
 */

export const config = {
  // Mode de l'application: 'mock' ou 'api'
  mode: (import.meta.env.VITE_MODE || 'mock') as 'mock' | 'api',
  
  // URL de l'API backend
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  
  // Est-ce qu'on utilise le mode mock ?
  isMockMode: () => config.mode === 'mock',
  
  // Est-ce qu'on utilise l'API réelle ?
  isApiMode: () => config.mode === 'api',
};

// Log de la configuration au démarrage
console.log('🔧 Configuration:', {
  mode: config.mode,
  apiUrl: config.apiUrl,
  isMock: config.isMockMode(),
});
