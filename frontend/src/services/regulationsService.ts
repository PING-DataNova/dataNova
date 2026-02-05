import { apiCall } from './api';
import { Regulation } from '../types';

export interface RegulationResponse {
  regulations: Regulation[];
  total: number;
  page: number;
  limit: number;
}

export interface UpdateRegulationRequest {
  id: string;
  status: 'validated' | 'rejected' | 'to-review';
  comment?: string;
}

// Service pour les réglementations
export const regulationsService = {
  // Récupérer toutes les réglementations avec filtres
  getRegulations: async (filters?: {
    status?: string;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<RegulationResponse> => {
    const params = new URLSearchParams();
    
    if (filters?.status && filters.status !== 'all') {
      params.append('status', filters.status);
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.page) {
      params.append('page', filters.page.toString());
    }
    if (filters?.limit) {
      params.append('limit', filters.limit.toString());
    }

    const queryString = params.toString();
    const endpoint = `/regulations${queryString ? `?${queryString}` : ''}`;
    
    return apiCall(endpoint, {
      method: 'GET',
    });
  },

  // Mettre à jour le statut d'une réglementation
  updateRegulationStatus: async (data: UpdateRegulationRequest): Promise<Regulation> => {
    return apiCall(`/regulations/${data.id}/status`, {
      method: 'PUT',
      body: JSON.stringify({
        status: data.status,
        comment: data.comment,
      }),
    });
  },

  // Récupérer une réglementation spécifique
  getRegulationById: async (id: string): Promise<Regulation> => {
    return apiCall(`/regulations/${id}`, {
      method: 'GET',
    });
  },

  // Récupérer les statistiques
  getRegulationStats: async () => {
    return apiCall('/regulations/stats', {
      method: 'GET',
    });
  },
};

// Service pour l'authentification (si nécessaire)
export const authService = {
  login: async (credentials: { email: string; password: string }) => {
    return apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  logout: async () => {
    return apiCall('/auth/logout', {
      method: 'POST',
    });
  },

  getCurrentUser: async () => {
    return apiCall('/auth/me', {
      method: 'GET',
    });
  },
};