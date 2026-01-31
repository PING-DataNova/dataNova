
import { RiskData } from './types';

export const MOCK_RISKS: RiskData[] = [
  {
    id: '1',
    risk_main: 'Taxe Carbone Frontalière (CBAM)',
    impact_level: 'eleve',
    risk_details: 'Nouveaux rapports trimestriels obligatoires sur les émissions intégrées pour l\'importation d\'acier et d\'aluminium.',
    modality: 'Déclaration Fiscale',
    deadline: '12-2025',
    recommendation: 'Mettre en place un système de collecte automatisée des données fournisseurs.',
    llm_reasoning: 'L\'extension du champ d\'application CBAM impactera directement les coûts d\'approvisionnement.',
    created_at: '2026-01-29 14:32:43',
    category: 'Climat'
  },
  {
    id: '2',
    risk_main: 'CSRD - Directive Durabilité',
    impact_level: 'critique',
    risk_details: 'Obligation de reporting extra-financier détaillé selon les standards ESRS.',
    modality: 'Audit Juridique',
    deadline: '01-2026',
    recommendation: 'Nommer un responsable de projet CSRD et auditer la chaîne de valeur.',
    llm_reasoning: 'Non-conformité peut entraîner des sanctions pénales et une dégradation de la notation ESG.',
    created_at: '2026-01-28 09:15:20',
    category: 'Réglementations'
  },
  {
    id: '3',
    risk_main: 'Tensions Mer de Chine',
    impact_level: 'critique',
    risk_details: 'Risque de perturbations majeures des routes maritimes affectant les composants électroniques.',
    modality: 'Chaîne Logistique',
    deadline: 'Immédiat',
    recommendation: 'Diversifier les sources d\'approvisionnement hors zone de conflit.',
    llm_reasoning: 'Escalade géopolitique probable augmentant les délais de transit de 30% minimum.',
    created_at: '2026-01-30 11:45:00',
    category: 'Géopolitique'
  },
  {
    id: '4',
    risk_main: 'RGPD 2.0 - IA Act',
    impact_level: 'moyen',
    risk_details: 'Nouvelle réglementation européenne sur l\'usage des algorithmes prédictifs.',
    modality: 'Conformité IT',
    deadline: '06-2026',
    recommendation: 'Auditer tous les outils internes utilisant de l\'IA générative.',
    llm_reasoning: 'L\'IA Act impose des obligations de transparence strictes pour les systèmes à haut risque.',
    created_at: '2026-01-25 16:20:00',
    category: 'Réglementations'
  }
];
