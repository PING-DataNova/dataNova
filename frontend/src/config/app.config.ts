/**
 * Configuration de l'application
 * 
 * Le proxy Vite est configuré pour rediriger /api vers http://localhost:8000
 * En dev, on utilise des chemins relatifs qui passent par le proxy
 * En prod, on utilise l'URL complète de l'API
 */

export const config = {
  // URL de l'API backend
  // - En dev: vide pour utiliser le proxy Vite (/api → localhost:8000)
  // - En prod: URL complète de l'API
  apiUrl: import.meta.env.VITE_API_URL || '',
  
  // Mode de données mock (fallback si backend vide)
  useMockData: import.meta.env.VITE_USE_MOCK_DATA === 'true' || true,
  
  // Debug mode
  debug: import.meta.env.VITE_DEBUG === 'true' || import.meta.env.DEV,
};

// Log de la configuration au démarrage
if (config.debug) {
  console.log('🔧 Configuration DataNova:', {
    apiUrl: config.apiUrl || '(proxy → localhost:8000)',
    useMockData: config.useMockData,
    debug: config.debug,
  });
}
