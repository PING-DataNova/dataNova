import { apiCall } from './api';

// ========================================
// Types pour Impact Assessments (Agent 2)
// ========================================

export interface ImpactAssessment {
  id: string;
  analysis_id: string;
  regulation_title: string;
  regulation_type: string | null;
  
  // Métriques d'impact
  risk_main: 'fiscal' | 'operationnel' | 'conformite' | 'reputationnel' | 'juridique';
  impact_level: 'faible' | 'moyen' | 'eleve';
  risk_details: string;
  modality: 'certificat' | 'reporting' | 'taxe' | 'quota' | 'interdiction' | 'autorisation';
  deadline: string; // Format: "MM-YYYY"
  
  // Recommandations
  recommendation: string;
  llm_reasoning: string | null;
  
  // Métadonnées
  created_at: string;
}

export interface ImpactListResponse {
  impacts: ImpactAssessment[];
  total: number;
  page: number;
  limit: number;
}

export interface DashboardStats {
  total_regulations: number;
  total_impacts: number;
  high_risks: number;
  medium_risks: number;
  low_risks: number;
  critical_deadlines: number;
  pending_percentage: number;
  approved_percentage: number;
  by_risk_type: {
    fiscal: number;
    operationnel: number;
    conformite: number;
    reputationnel: number;
    juridique: number;
  };
}

export interface TimelineStats {
  timeline: {
    [deadline: string]: {
      total: number;
      eleve: number;
      moyen: number;
      faible: number;
    };
  };
}

// ========================================
// Service API pour Impact Assessments
// ========================================

export const impactsService = {
  /**
   * Récupère la liste des impact assessments avec filtres
   */
  getImpacts: async (filters?: {
    impact_level?: 'faible' | 'moyen' | 'eleve';
    risk_main?: 'fiscal' | 'operationnel' | 'conformite' | 'reputationnel' | 'juridique';
    page?: number;
    limit?: number;
  }): Promise<ImpactListResponse> => {
    const params = new URLSearchParams();
    
    if (filters?.impact_level) {
      params.append('impact_level', filters.impact_level);
    }
    if (filters?.risk_main) {
      params.append('risk_main', filters.risk_main);
    }
    if (filters?.page) {
      params.append('page', filters.page.toString());
    }
    if (filters?.limit) {
      params.append('limit', filters.limit.toString());
    }

    const queryString = params.toString();
    const endpoint = `/impacts${queryString ? `?${queryString}` : ''}`;
    
    return apiCall(endpoint, {
      method: 'GET',
    });
  },

  /**
   * Récupère un impact assessment spécifique par ID
   */
  getImpactById: async (id: string): Promise<ImpactAssessment> => {
    return apiCall(`/impacts/${id}`, {
      method: 'GET',
    });
  },

  /**
   * Récupère les statistiques pour le Dashboard Décideur
   */
  getDashboardStats: async (): Promise<DashboardStats> => {
    return apiCall('/impacts/stats/dashboard', {
      method: 'GET',
    });
  },

  /**
   * Récupère la répartition des impacts par deadline (timeline)
   */
  getTimelineStats: async (): Promise<TimelineStats> => {
    return apiCall('/impacts/stats/timeline', {
      method: 'GET',
    });
  },

  /**
   * Récupère les impacts avec risque élevé uniquement
   */
  getHighRiskImpacts: async (): Promise<ImpactListResponse> => {
    return impactsService.getImpacts({ 
      impact_level: 'eleve',
      limit: 100 
    });
  },

  /**
   * Récupère les impacts par type de risque
   */
  getImpactsByRiskType: async (
    risk_type: 'fiscal' | 'operationnel' | 'conformite' | 'reputationnel' | 'juridique'
  ): Promise<ImpactListResponse> => {
    return impactsService.getImpacts({ 
      risk_main: risk_type,
      limit: 100 
    });
  },
};
