/**
 * Configuration de l'application
 */

export const config = {
  // URL de l'API backend - vide pour utiliser le proxy Vite en dev
  apiUrl: import.meta.env.VITE_API_URL || '',
};

// Log de la configuration au démarrage
console.log('🔧 Configuration:', {
  apiUrl: config.apiUrl || '(proxy)',
});
