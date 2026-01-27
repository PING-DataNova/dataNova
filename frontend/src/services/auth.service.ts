// Service d'authentification mock pour le frontend
export const authService = {
  login: async (credentials: { email: string; password: string }) => {
    // Simule une réponse de login pour le mode mock
    if (credentials.email.includes('juriste')) {
      return { id: '1', name: 'Juriste', role: 'juridique', avatar: '' };
    }
    if (credentials.email.includes('decideur')) {
      return { id: '2', name: 'Décideur', role: 'decisive', avatar: '' };
    }
    throw new Error('Utilisateur inconnu');
  }
};
