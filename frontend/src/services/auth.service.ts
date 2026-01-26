/**
 * Service API pour l'authentification
 */

import { config } from '../config/app.config';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'juridique' | 'decisive';
}

export interface LoginResponse {
  user: User;
  token?: string;
}

class AuthService {
  /**
   * Connexion utilisateur
   * TODO: Implémenter l'auth API plus tard
   * Pour l'instant, toujours en mode mock
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    // Toujours utiliser le mock pour l'auth (API auth pas encore implémentée)
    return this.mockLogin(credentials);
  }

  /**
   * Mode MOCK - Simulation de connexion
   */
  private async mockLogin(credentials: LoginCredentials): Promise<LoginResponse> {
    console.log('🎭 Mode MOCK - Simulation de connexion');
    
    // Simulation d'un délai réseau
    await new Promise(resolve => setTimeout(resolve, 1000));

    const { email } = credentials;

    // Logique de connexion basée sur l'email
    if (email.includes('juriste') || email.includes('legal')) {
      return {
        user: {
          id: '1',
          name: 'Juriste Hutchinson',
          email: email,
          role: 'juridique',
        },
      };
    } else if (email.includes('decideur') || email.includes('decision')) {
      return {
        user: {
          id: '2',
          name: 'Décideur Hutchinson',
          email: email,
          role: 'decisive',
        },
      };
    } else {
      throw new Error('Utilisateur non reconnu. Utilisez un email avec "juriste" ou "decideur".');
    }
  }

  /**
   * Mode API - Appel réel au backend
   */
  private async apiLogin(credentials: LoginCredentials): Promise<LoginResponse> {
    console.log('🌐 Mode API - Appel au backend:', config.apiUrl);

    try {
      const response = await fetch(`${config.apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Erreur de connexion');
      }

      const data = await response.json();
      
      return {
        user: data.user,
        token: data.token,
      };
    } catch (error) {
      console.error('❌ Erreur API:', error);
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Impossible de se connecter au serveur'
      );
    }
  }

  /**
   * Déconnexion
   */
  async logout(): Promise<void> {
    if (config.isApiMode()) {
      // Appel API de déconnexion si nécessaire
      console.log('🌐 Déconnexion API');
    }
    // Nettoyer le token local, etc.
  }
}

export const authService = new AuthService();
