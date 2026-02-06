import { config } from '../config/app.config';

const API_BASE_URL = config.apiUrl ? `${config.apiUrl}` : '';

// Types
export interface Subscription {
  id: string;
  email: string;
  name?: string;
  subscription_name: string;
  event_types: string[];
  supplier_ids?: string[];
  supplier_names?: string[];
  site_ids?: string[];
  site_names?: string[];
  countries?: string[];
  min_criticality: string;
  notify_immediately: boolean;
  digest_frequency?: string;
  include_weather_alerts: boolean;
  include_regulatory: boolean;
  include_geopolitical: boolean;
  is_active: boolean;
  verified: boolean;
  notification_count: number;
  last_notified_at?: string;
  created_at: string;
}

export interface SubscriptionCreate {
  email: string;
  name?: string;
  subscription_name?: string;
  event_types?: string[];
  supplier_ids?: string[];
  site_ids?: string[];
  countries?: string[];
  min_criticality?: string;
  notify_immediately?: boolean;
  digest_frequency?: string;
  include_weather_alerts?: boolean;
  include_regulatory?: boolean;
  include_geopolitical?: boolean;
}

export interface SubscriptionUpdate {
  subscription_name?: string;
  event_types?: string[];
  supplier_ids?: string[];
  site_ids?: string[];
  countries?: string[];
  min_criticality?: string;
  notify_immediately?: boolean;
  digest_frequency?: string;
  include_weather_alerts?: boolean;
  include_regulatory?: boolean;
  include_geopolitical?: boolean;
  is_active?: boolean;
}

export interface SupplierOption {
  id: string;
  name: string;
  country: string;
  sector: string;
}

export interface SiteOption {
  id: string;
  name: string;
  code: string;
  country: string;
  city: string;
}

export interface EventTypeOption {
  value: string;
  label: string;
  description: string;
}

export interface CriticalityOption {
  value: string;
  label: string;
  description: string;
}

// API Functions
export const subscriptionService = {
  // Récupérer les abonnements d'un email
  async getSubscriptions(email?: string): Promise<Subscription[]> {
    const params = new URLSearchParams();
    if (email) params.append('email', email);
    
    const response = await fetch(`${API_BASE_URL}/api/subscriptions?${params.toString()}`);
    if (!response.ok) throw new Error('Erreur lors de la récupération des abonnements');
    const data = await response.json();
    return data.subscriptions;
  },

  // Créer un nouvel abonnement
  async createSubscription(data: SubscriptionCreate): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors de la création de l\'abonnement');
    }
    return response.json();
  },

  // Mettre à jour un abonnement
  async updateSubscription(id: string, data: SubscriptionUpdate): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Erreur lors de la mise à jour');
    return response.json();
  },

  // Supprimer un abonnement
  async deleteSubscription(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Erreur lors de la suppression');
  },

  // Activer/Désactiver un abonnement
  async toggleSubscription(id: string): Promise<{ is_active: boolean }> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/${id}/toggle`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Erreur lors du basculement');
    return response.json();
  },

  // Options pour les filtres
  async getSupplierOptions(): Promise<SupplierOption[]> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/options/suppliers`);
    if (!response.ok) return [];
    return response.json();
  },

  async getSiteOptions(): Promise<SiteOption[]> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/options/sites`);
    if (!response.ok) return [];
    return response.json();
  },

  async getCountryOptions(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/options/countries`);
    if (!response.ok) return [];
    return response.json();
  },

  async getEventTypeOptions(): Promise<EventTypeOption[]> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/options/event-types`);
    if (!response.ok) return [];
    return response.json();
  },

  async getCriticalityOptions(): Promise<CriticalityOption[]> {
    const response = await fetch(`${API_BASE_URL}/api/subscriptions/options/criticality-levels`);
    if (!response.ok) return [];
    return response.json();
  },
};
