import { apiCall } from './api';

// ========================================
// Types pour Impact Assessments (Agent 2)
// Adapté pour correspondre au backend RiskAnalysis
// ========================================

export interface ImpactAssessment {
  id: string;
  analysis_id: string;
  regulation_title: string;
  regulation_type: string | null;
  
  // Métriques d'impact
  risk_main: string;  // Description du risque principal
  impact_level: 'faible' | 'moyen' | 'eleve' | 'critique';  // Ajout de 'critique'
  risk_details: string;
  modality: string | null;  // Plus flexible pour correspondre au backend
  deadline: string | null; // Format: "MM-YYYY" ou null
  
  // Recommandations
  recommendation: string;
  llm_reasoning: string | null;
  
  // Métadonnées
  created_at: string;
  
  // Catégorie du risque (depuis le backend)
  category: 'Réglementations' | 'Climat' | 'Géopolitique';
}

export interface AffectedEntity {
  id: string;
  name: string;
  risk_score: number;
  reasoning: string;
  weather_summary?: string | null;
  business_interruption_score?: number | null;
}

export interface RiskDetailResponse {
  id: string;
  analysis_id: string;
  
  // Informations sur le document source
  regulation_title: string;
  regulation_type: string | null;
  source_url: string | null;
  source_excerpt: string | null;
  
  // Niveaux de risque
  risk_level: string;
  risk_score: number;  // Score 0-100
  impact_level: string;
  supply_chain_impact: string | null;
  
  // Description
  impacts_description: string;
  reasoning: string | null;
  
  // Entités affectées
  affected_sites: AffectedEntity[];
  affected_suppliers: AffectedEntity[];
  
  // Recommandations
  recommendations: string;
  
  // Métadonnées
  created_at: string;
  category: string;
  
  // Analyse météo si disponible
  weather_risk_summary: {
    entities_with_alerts: number;
    total_alerts: number;
    max_severity: string;
    average_weather_risk_score: number;
    alerts_by_type: { [key: string]: number };
    logistics_recommendations?: Array<{
      entity_name: string;
      entity_type: string;
      location: string;
      alert_type: string;
      severity: string;
      date: string;
      value: string;
      action: string;
      deadline: string;
      priority: string;
    }>;
  } | null;
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
  average_score?: number;
  by_risk_type: {
    [key: string]: number;  // Plus flexible: reglementaire, climat, geopolitique, etc.
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
    impact_level?: 'faible' | 'moyen' | 'eleve' | 'critique';
    risk_main?: string;
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
   * Récupère les détails complets d'un risque (sites, fournisseurs, météo, etc.)
   */
  getRiskDetails: async (id: string): Promise<RiskDetailResponse> => {
    return apiCall(`/impacts/${id}/details`, {
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
   * Récupère les impacts avec risque élevé ou critique uniquement
   */
  getHighRiskImpacts: async (): Promise<ImpactListResponse> => {
    // Récupérer tous les impacts et filtrer côté client
    const all = await impactsService.getImpacts({ limit: 200 });
    const highRisks = all.impacts.filter(i => 
      i.impact_level === 'eleve' || i.impact_level === 'critique'
    );
    return {
      impacts: highRisks,
      total: highRisks.length,
      page: 1,
      limit: 200
    };
  },

  /**
   * Récupère les impacts par catégorie
   */
  getImpactsByCategory: async (
    category: 'Réglementations' | 'Climat' | 'Géopolitique'
  ): Promise<ImpactListResponse> => {
    // Récupérer tous les impacts et filtrer par catégorie
    const all = await impactsService.getImpacts({ limit: 200 });
    const filtered = all.impacts.filter(i => i.category === category);
    return {
      impacts: filtered,
      total: filtered.length,
      page: 1,
      limit: 200
    };
  },

  /**
   * Récupère les impacts par type de risque (legacy - pour compatibilité)
   */
  getImpactsByRiskType: async (
    risk_type: string
  ): Promise<ImpactListResponse> => {
    return impactsService.getImpacts({ 
      risk_main: risk_type,
      limit: 100 
    });
  },
};
