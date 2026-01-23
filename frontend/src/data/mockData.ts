import { Regulation } from '../types';

// Données de test basées sur les images fournies
// Format correspondant à la structure backend (documents + analyses)
export const mockRegulations: Regulation[] = [
  {
    id: '1',
    title: 'Règlement sur les produits biocides (EU) 528/2012',
    description: 'Règlemente la mise sur le marché et l\'utilisation des biocides.',
    status: 'pending',
    type: 'EU',
    dateCreated: new Date('2024-12-15'),
    reference: 'EU 528/2012'
  },
  {
    id: '2',
    title: 'Directive sur la protection des travailleurs contre les risques liés à l\'exposition à des agents chimiques (98/24/CE)',
    description: 'Protège les travailleurs exposés aux substances chimiques dangereuses.',
    status: 'pending',
    type: 'Directive',
    dateCreated: new Date('2024-12-10'),
    reference: '98/24/CE'
  },
  {
    id: '3',
    title: 'Règlement REACH (CE) N° 1907/2006',
    description: 'Enregistrement, évaluation, autorisation et restriction des substances chimiques.',
    status: 'validated',
    type: 'EU',
    dateCreated: new Date('2024-12-05'),
    reference: 'CE 1907/2006'
  },
  {
    id: '4',
    title: 'Directive CLP (CE) N° 1272/2008',
    description: 'Classification, étiquetage et emballage des substances et mélanges.',
    status: 'to-review',
    type: 'Directive',
    dateCreated: new Date('2024-12-01'),
    reference: 'CE 1272/2008'
  }
];

/**
 * Format JSON des données validées pour l'équipe juridique
 * Structure compatible avec la base de données backend (documents + analyses)
 */
export interface ValidatedRegulationJSON {
  document_id: string;
  title: string;
  reference: string;
  regulation_type: string;
  source_url: string;
  publication_date: string;
  workflow_status: 'analyzed' | 'validated' | 'rejected_validation';
  validated_at?: string;
  validated_by?: string;
  analysis?: {
    is_relevant: boolean;
    confidence: number;
    matched_keywords: string[];
    matched_nc_codes: string[];
    validation_status: 'pending' | 'approved' | 'rejected';
    validation_comment?: string;
  };
}

/**
 * Liste des réglementations validées au format JSON
 * Correspond au format attendu du backend
 */
export const getValidatedRegulationsJSON = (): ValidatedRegulationJSON[] => {
  return mockRegulations
    .filter(reg => reg.status === 'validated')
    .map(reg => ({
      document_id: reg.id,
      title: reg.title,
      reference: reg.reference,
      regulation_type: reg.type,
      source_url: `https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:${reg.reference}`,
      publication_date: reg.dateCreated.toISOString(),
      workflow_status: 'validated',
      validated_at: new Date().toISOString(),
      validated_by: 'juriste@ping.com',
      analysis: {
        is_relevant: true,
        confidence: 0.95,
        matched_keywords: ['biocides', 'substances chimiques', 'protection'],
        matched_nc_codes: ['2804', '2805', '2806'],
        validation_status: 'approved',
        validation_comment: 'Document pertinent pour notre activité'
      }
    }));
};

/**
 * Exporte les données validées au format JSON
 */
export const exportValidatedRegulationsJSON = (): string => {
  const data = getValidatedRegulationsJSON();
  return JSON.stringify(data, null, 2);
};