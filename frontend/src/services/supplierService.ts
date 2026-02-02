/**
 * Service API pour l'analyse de fournisseurs
 */

import { 
  SupplierAnalysisRequest, 
  SupplierAnalysisResponse, 
  SupplierAnalysisListResponse 
} from '../types/supplier';

// Configuration API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

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

export default {
  analyzeSupplier,
  getAnalysesList,
  getAnalysisDetails,
  deleteAnalysis,
};
