
export type ImpactLevel = 'faible' | 'moyen' | 'eleve' | 'critique';
export type RiskLevel = 'faible' | 'moyen' | 'eleve';  // Pour la matrice
export type ImpactGravity = 'faible' | 'moyen' | 'fort';  // Pour la matrice
export type RiskCategory = 'Réglementations' | 'Climat' | 'Géopolitique';

export interface RiskData {
  id: string;
  risk_main: string;
  impact_level: ImpactLevel;
  risk_level?: RiskLevel;  // Niveau de risque (probabilité)
  impact_gravity?: ImpactGravity;  // Gravité de l'impact
  risk_details: string;
  modality: string;
  deadline: string;
  recommendation: string;
  llm_reasoning: string;
  created_at: string;
  category: RiskCategory;
}

export interface User {
  email: string;
  fullName: string;
  role: string;
}

export interface Notification {
  id: string;
  title: string;
  description: string;
  category: string;
  timestamp: Date;
  isRead: boolean;
}
