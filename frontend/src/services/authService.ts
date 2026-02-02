/**
 * Service d'authentification - Appels API au backend
 */

import { config } from '../config/app.config';

const API_BASE_URL = config.apiUrl;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role: 'juridique' | 'decisive';
}

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface LoginResponse {
  token: string;
  user: UserResponse;
}

/**
 * Connecter un utilisateur
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur de connexion' }));
    throw new Error(error.detail || 'Identifiants incorrects');
  }

  return response.json();
}

/**
 * Inscrire un nouvel utilisateur
 */
export async function register(data: RegisterRequest): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur d\'inscription' }));
    throw new Error(error.detail || 'Impossible de créer le compte');
  }

  return response.json();
}

/**
 * Sauvegarder le token dans le localStorage
 */
export function saveToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

/**
 * Récupérer le token depuis le localStorage
 */
export function getToken(): string | null {
  return localStorage.getItem('auth_token');
}

/**
 * Supprimer le token (déconnexion)
 */
export function removeToken(): void {
  localStorage.removeItem('auth_token');
}

/**
 * Vérifier si l'utilisateur est connecté
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}
