/**
 * Service API pour l'analyse de fournisseurs
 */

import { 
  SupplierAnalysisRequest, 
  SupplierAnalysisResponse, 
  SupplierAnalysisListResponse 
} from '../types/supplier';
import { config } from '../config/app.config';

// Configuration API - utilise le proxy en dev
const API_BASE_URL = config.apiUrl ? `${config.apiUrl}/api` : '/api';

// Headers par défaut
const getHeaders = (): HeadersInit => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Lance une analyse de risques pour un fournisseur
 * @param request Données du fournisseur à analyser
 * @returns Résultat de l'analyse
 */
export const analyzeSupplier = async (
  request: SupplierAnalysisRequest
): Promise<SupplierAnalysisResponse> => {
  const response = await fetch(`${API_BASE_URL}/supplier/analyze`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

/**
 * Récupère la liste des analyses avec pagination et filtres
 * @param options Options de pagination et filtres
 * @returns Liste paginée des analyses
 */
export const getAnalysesList = async (options: {
  page?: number;
  limit?: number;
  country?: string;
  risk_level?: string;
} = {}): Promise<SupplierAnalysisListResponse> => {
  const params = new URLSearchParams();
  
  if (options.page) params.append('page', options.page.toString());
  if (options.limit) params.append('limit', options.limit.toString());
  if (options.country) params.append('country', options.country);
  if (options.risk_level) params.append('risk_level', options.risk_level);
  
  const url = `${API_BASE_URL}/supplier/analyses?${params.toString()}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

/**
 * Récupère les détails d'une analyse spécifique
 * @param analysisId ID de l'analyse
 * @returns Détails de l'analyse
 */
export const getAnalysisDetails = async (
  analysisId: string
): Promise<SupplierAnalysisResponse> => {
  const response = await fetch(`${API_BASE_URL}/supplier/analyses/${analysisId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

/**
 * Supprime une analyse
 * @param analysisId ID de l'analyse à supprimer
 */
export const deleteAnalysis = async (analysisId: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/supplier/analyses/${analysisId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
};

// ========================================
// API pour les Fournisseurs depuis la BDD
// ========================================

export interface SupplierDBProfile {
  id: string;
  name: string;
  code: string;
  country: string;
  region: string;
  city: string;
  address: string;
  latitude: number;
  longitude: number;
  sector: string;
  products_supplied: string[];
  company_size: string;
  certifications: string[];
  financial_health: string;
  active: boolean;
  annual_purchase_volume: number | null;
  daily_delivery_value: number | null;
  average_stock_at_hutchinson_days: number | null;
  switch_time_days: number | null;
  criticality_score: number | null;
  can_increase_capacity: boolean;
  employee_count: number | null;
  annual_revenue_usd: number | null;
  founded_year: number | null;
  sites_served?: {
    site_id: string;
    site_name: string;
    site_country: string;
    criticality: string;
    products_supplied: string[];
    is_sole_supplier: boolean;
    has_backup_supplier: boolean;
    lead_time_days: number | null;
    annual_volume: number | null;
  }[];
  risk_exposure?: {
    total_sites_served: number;
    critical_relationships: number;
    sole_supplier_for: number;
    backup_coverage: number;
    risk_level: string;
  };
}

export interface SupplierDBListResponse {
  suppliers: SupplierDBProfile[];
  total: number;
}

/**
 * Récupère la liste des fournisseurs depuis la base de données
 */
export const getSuppliersList = async (options: {
  country?: string;
  sector?: string;
  limit?: number;
} = {}): Promise<SupplierDBListResponse> => {
  const params = new URLSearchParams();
  
  if (options.country) params.append('country', options.country);
  if (options.sector) params.append('sector', options.sector);
  if (options.limit) params.append('limit', options.limit.toString());
  
  const url = `${API_BASE_URL}/supplier/db/list${params.toString() ? `?${params.toString()}` : ''}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

/**
 * Récupère le profil complet d'un fournisseur par son ID
 */
export const getSupplierProfile = async (supplierId: string): Promise<SupplierDBProfile> => {
  const response = await fetch(`${API_BASE_URL}/supplier/db/${supplierId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

/**
 * Recherche un fournisseur par nom
 */
export const searchSupplierByName = async (name: string): Promise<SupplierDBProfile> => {
  const response = await fetch(`${API_BASE_URL}/supplier/db/by-name/${encodeURIComponent(name)}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

export default {
  analyzeSupplier,
  getAnalysesList,
  getAnalysisDetails,
  deleteAnalysis,
  // DB Profile APIs
  getSuppliersList,
  getSupplierProfile,
  searchSupplierByName,
};
