// ============================================================================
// TYPES POUR L'ANALYSE FOURNISSEUR (Agent 1A - Scénario 2)
// ============================================================================

// ========== REQUEST ==========

export interface SupplierAnalysisRequest {
  name: string;                    // Obligatoire
  country: string;                 // Obligatoire
  city?: string;
  latitude?: number;
  longitude?: number;
  materials: string[];             // Obligatoire, min 1
  nc_codes?: string[];
  criticality?: 'Standard' | 'Important' | 'Critique';
  annual_volume?: number;
}

// ========== RESPONSE ==========

export interface SupplierInfo {
  name: string;
  country: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  nc_codes: string[];
  materials: string[];
  criticality: string;
  annual_volume?: number;
}

export interface RegulatoryRiskItem {
  celex_id: string;
  title: string;
  publication_date?: string;
  document_type?: string;
  source_url: string;
  matched_keyword: string;
  relevance: 'high' | 'medium' | 'low';
}

export interface WeatherRiskItem {
  alert_type: 'snow' | 'heavy_rain' | 'extreme_heat' | 'extreme_cold' | 'high_wind' | string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  date: string;
  value: number;
  threshold: number;
  unit: string;
  description: string;
  supply_chain_risk: string;
}

export interface RecommendationItem {
  type: 'regulatory' | 'weather' | 'general';
  priority: 'high' | 'medium' | 'low';
  action: string;
  details: string;
}

export interface SupplierAnalysisResponse {
  id: string;
  status: 'pending' | 'completed' | 'error';
  supplier_info: SupplierInfo;
  regulatory_risks: {
    count: number;
    items: RegulatoryRiskItem[];
  };
  weather_risks: {
    count: number;
    items: WeatherRiskItem[];
  };
  risk_score: number;              // 0-10
  risk_level: 'Faible' | 'Moyen' | 'Fort' | 'Critique';
  recommendations: RecommendationItem[];
  processing_time_ms: number;
  created_at: string;
}

// ========== LIST RESPONSE ==========

export interface SupplierAnalysisListResponse {
  analyses: SupplierAnalysisResponse[];
  total: number;
  page: number;
  limit: number;
}

// ========== HELPERS ==========

export const RISK_LEVEL_COLORS: Record<string, string> = {
  'Critique': '#DC2626',  // Rouge vif
  'Fort': '#EF4444',      // Rouge
  'Moyen': '#F59E0B',     // Orange
  'Faible': '#10B981',    // Vert
};

export const SEVERITY_COLORS: Record<string, string> = {
  'critical': '#DC2626',
  'high': '#EF4444',
  'medium': '#F59E0B',
  'low': '#10B981',
};

export const PRIORITY_COLORS: Record<string, string> = {
  'high': '#DC2626',
  'medium': '#F59E0B',
  'low': '#10B981',
};

// Liste des pays courants pour le select
export const COUNTRIES = [
  'France', 'Germany', 'Italy', 'Spain', 'Poland', 'Belgium',
  'Thailand', 'China', 'Vietnam', 'Indonesia', 'India', 'Japan',
  'USA', 'Mexico', 'Brazil', 'Argentina',
  'Ukraine', 'Turkey', 'Morocco', 'South Africa'
];

// Matériaux courants pour suggestions
export const COMMON_MATERIALS = [
  'Caoutchouc naturel',
  'Latex',
  'Acier',
  'Aluminium',
  'Plastique',
  'Polymères',
  'Composites',
  'Titane',
  'Cuivre',
  'Électronique',
  'Textile',
  'Verre'
];

// Codes NC courants
export const COMMON_NC_CODES = [
  { code: '4001', label: 'Caoutchouc naturel' },
  { code: '400121', label: 'Feuilles fumées de caoutchouc' },
  { code: '400122', label: 'Caoutchouc naturel techniquement spécifié' },
  { code: '7208', label: 'Produits laminés plats en fer/acier' },
  { code: '7606', label: 'Tôles et bandes en aluminium' },
  { code: '8544', label: 'Fils et câbles électriques' },
  { code: '2804', label: 'Hydrogène, gaz rares' },
  { code: '2901', label: 'Hydrocarbures acycliques' },
];
