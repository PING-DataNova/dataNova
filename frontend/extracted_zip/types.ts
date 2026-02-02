
export type ImpactLevel = 'faible' | 'moyen' | 'eleve' | 'critique';

export interface RiskData {
  id: string;
  risk_main: string;
  impact_level: ImpactLevel;
  risk_details: string;
  modality: string;
  deadline: string;
  recommendation: string;
  llm_reasoning: string;
  created_at: string;
  category: 'Réglementations' | 'Climat' | 'Géopolitique';
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
