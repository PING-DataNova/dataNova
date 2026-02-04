/**
 * Données de démonstration pour le Dashboard
 * 
 * ⚠️ Ces données sont utilisées UNIQUEMENT quand le backend ne retourne aucun impact.
 * Elles seront automatiquement remplacées par les vraies données de l'Agent 2
 * dès que le pipeline sera fonctionnel.
 * 
 * Pour désactiver les mocks : mettre USE_MOCK_DATA = false
 */

export const USE_MOCK_DATA = true; // Mettre à false pour désactiver les données de démo

export interface MockImpact {
  id: string;
  regulation_title: string;
  risk_main: string;
  impact_level: 'faible' | 'moyen' | 'eleve' | 'critique';
  risk_level: 'faible' | 'moyen' | 'eleve';  // Niveau de risque (probabilité)
  impact_gravity: 'faible' | 'moyen' | 'fort';  // Gravité de l'impact
  risk_details: string;
  modality: string;
  deadline: string;
  recommendation: string;
  llm_reasoning: string;
  created_at: string;
  category: 'Réglementations' | 'Climat' | 'Géopolitique';  // Catégorie du risque
}

export const MOCK_IMPACTS: MockImpact[] = [
  // ===== RÉGLEMENTATIONS =====
  {
    id: "mock-001",
    regulation_title: "CBAM - Carbon Border Adjustment Mechanism",
    risk_main: "Déclaration obligatoire des émissions CO2 pour imports",
    impact_level: "critique",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Les importateurs doivent déclarer les émissions de CO2 incorporées dans les produits importés (acier, aluminium, ciment, engrais, électricité, hydrogène). Pénalités en cas de non-conformité.",
    modality: "Déclaration trimestrielle obligatoire dès 2024, achat de certificats CBAM dès 2026",
    deadline: "01-01-2026",
    recommendation: "Cartographier les fournisseurs concernés, collecter les données d'émissions, mettre en place un système de suivi",
    llm_reasoning: "Impact critique car concerne directement la chaîne d'approvisionnement et implique des coûts supplémentaires significatifs",
    created_at: "2026-01-15",
    category: "Réglementations"
  },
  {
    id: "mock-002",
    regulation_title: "EUDR - Règlement Déforestation",
    risk_main: "Traçabilité des matières premières à risque",
    impact_level: "eleve",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Obligation de due diligence pour 7 commodités (bétail, cacao, café, huile de palme, caoutchouc, soja, bois) et produits dérivés. Géolocalisation des parcelles d'origine requise.",
    modality: "Système de diligence raisonnée avec traçabilité géolocalisée",
    deadline: "30-12-2025",
    recommendation: "Identifier les produits concernés, demander les coordonnées GPS aux fournisseurs, vérifier l'absence de déforestation",
    llm_reasoning: "Impact élevé pour Hutchinson en raison de l'utilisation de caoutchouc dans les produits",
    created_at: "2026-01-20",
    category: "Réglementations"
  },
  {
    id: "mock-003",
    regulation_title: "CSRD - Corporate Sustainability Reporting Directive",
    risk_main: "Reporting ESG étendu obligatoire",
    impact_level: "moyen",
    risk_level: "moyen",
    impact_gravity: "moyen",
    risk_details: "Extension des obligations de reporting extra-financier avec standards ESRS. Double matérialité, audit externe obligatoire.",
    modality: "Rapport annuel selon standards ESRS",
    deadline: "01-01-2025",
    recommendation: "Former les équipes RSE, implémenter un outil de collecte de données ESG, préparer l'audit",
    llm_reasoning: "Impact moyen car Hutchinson a déjà des processus RSE en place",
    created_at: "2026-01-10",
    category: "Réglementations"
  },
  {
    id: "mock-004",
    regulation_title: "CS3D - Directive Devoir de Vigilance",
    risk_main: "Due diligence sur toute la chaîne de valeur",
    impact_level: "eleve",
    risk_level: "eleve",
    impact_gravity: "moyen",
    risk_details: "Obligation d'identifier, prévenir et atténuer les impacts négatifs sur les droits humains et l'environnement dans toute la chaîne de valeur.",
    modality: "Plan de vigilance avec mécanisme de plainte",
    deadline: "01-07-2027",
    recommendation: "Cartographier les risques fournisseurs, établir un code de conduite, mettre en place un mécanisme d'alerte",
    llm_reasoning: "Impact élevé en raison de la complexité de la chaîne d'approvisionnement internationale",
    created_at: "2026-01-22",
    category: "Réglementations"
  },
  {
    id: "mock-005",
    regulation_title: "Taxonomie UE - Acte délégué climat",
    risk_main: "Classification des activités durables",
    impact_level: "moyen",
    risk_level: "moyen",
    impact_gravity: "faible",
    risk_details: "Obligation de publier la part d'activités alignées sur la taxonomie (chiffre d'affaires, CapEx, OpEx).",
    modality: "Publication annuelle des indicateurs taxonomie",
    deadline: "01-01-2024",
    recommendation: "Analyser l'éligibilité des activités, calculer les ratios, documenter la méthodologie",
    llm_reasoning: "Impact moyen, reporting déjà en place pour les grandes entreprises",
    created_at: "2026-01-05",
    category: "Réglementations"
  },
  {
    id: "mock-006",
    regulation_title: "Règlement Batteries (2023/1542)",
    risk_main: "Passeport batterie et recyclage obligatoire",
    impact_level: "critique",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Nouvelles exigences pour batteries : empreinte carbone, contenu recyclé minimum, passeport numérique, collecte et recyclage.",
    modality: "Passeport numérique obligatoire, objectifs de recyclage",
    deadline: "18-02-2027",
    recommendation: "Identifier les batteries dans les produits, préparer les données pour le passeport, organiser la filière de recyclage",
    llm_reasoning: "Impact critique pour les produits contenant des batteries (véhicules électriques)",
    created_at: "2026-01-25",
    category: "Réglementations"
  },
  {
    id: "mock-007",
    regulation_title: "REACH - Restriction substances chimiques",
    risk_main: "Nouvelles restrictions PFAS",
    impact_level: "eleve",
    risk_level: "moyen",
    impact_gravity: "fort",
    risk_details: "Proposition de restriction universelle des PFAS (substances per- et polyfluoroalkylées). Impact potentiel sur les revêtements et joints.",
    modality: "Interdiction avec exemptions temporaires possibles",
    deadline: "01-01-2028",
    recommendation: "Inventorier les PFAS utilisés, identifier des alternatives, anticiper la reformulation",
    llm_reasoning: "Impact élevé car les PFAS sont utilisés dans de nombreux produits industriels",
    created_at: "2026-01-28",
    category: "Réglementations"
  },
  {
    id: "mock-008",
    regulation_title: "Eco-conception produits durables",
    risk_main: "Exigences de durabilité et réparabilité",
    impact_level: "faible",
    risk_level: "faible",
    impact_gravity: "faible",
    risk_details: "Futurs critères d'éco-conception pour différentes catégories de produits : durabilité, réparabilité, recyclabilité.",
    modality: "Critères spécifiques par catégorie de produit",
    deadline: "01-01-2030",
    recommendation: "Suivre l'évolution des actes délégués, anticiper les critères pour les produits concernés",
    llm_reasoning: "Impact faible à court terme, réglementations encore en développement",
    created_at: "2026-01-30",
    category: "Réglementations"
  },
  
  // ===== CLIMAT =====
  {
    id: "mock-climat-001",
    regulation_title: "Sécheresse prolongée - Europe du Sud",
    risk_main: "Stress hydrique impactant la production",
    impact_level: "critique",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Périodes de sécheresse de plus en plus longues en Espagne affectant les sites de production. Risque de rationnement d'eau industrielle.",
    modality: "Réduction de la consommation d'eau de 30% requise",
    deadline: "01-06-2026",
    recommendation: "Mettre en place des systèmes de recyclage d'eau, identifier des sources alternatives, optimiser les procédés",
    llm_reasoning: "Impact critique sur le site de Madrid dépendant des ressources hydriques",
    created_at: "2026-01-18",
    category: "Climat"
  },
  {
    id: "mock-climat-002",
    regulation_title: "Inondations - Europe Centrale",
    risk_main: "Risque d'inondation des sites industriels",
    impact_level: "eleve",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Augmentation de la fréquence des crues en Pologne. Sites de Łódź et Bielsko-Biała exposés selon les modèles climatiques.",
    modality: "Plan de continuité d'activité requis",
    deadline: "01-09-2026",
    recommendation: "Auditer la vulnérabilité des sites, renforcer les protections, préparer les plans d'évacuation",
    llm_reasoning: "Impact élevé avec 2 sites majeurs en zone à risque",
    created_at: "2026-01-12",
    category: "Climat"
  },
  {
    id: "mock-climat-003",
    regulation_title: "Canicule extrême - France",
    risk_main: "Interruption de production par chaleur excessive",
    impact_level: "moyen",
    risk_level: "moyen",
    impact_gravity: "moyen",
    risk_details: "Épisodes caniculaires dépassant 40°C impactant le confort des travailleurs et le fonctionnement des équipements.",
    modality: "Adaptation des horaires et climatisation renforcée",
    deadline: "01-05-2026",
    recommendation: "Installer des systèmes de refroidissement, adapter les horaires de travail, former les équipes",
    llm_reasoning: "Impact moyen sur les sites français (Chemillé, Blagnac)",
    created_at: "2026-01-08",
    category: "Climat"
  },
  {
    id: "mock-climat-004",
    regulation_title: "Typhons - Asie de l'Est",
    risk_main: "Perturbation logistique majeure",
    impact_level: "critique",
    risk_level: "moyen",
    impact_gravity: "fort",
    risk_details: "Intensification des typhons en Chine côtière. Impact sur le site de Wuhan et la chaîne logistique maritime.",
    modality: "Stock de sécurité et routes alternatives",
    deadline: "01-07-2026",
    recommendation: "Diversifier les fournisseurs, augmenter les stocks tampons, identifier des ports alternatifs",
    llm_reasoning: "Impact critique sur l'approvisionnement depuis l'Asie",
    created_at: "2026-01-22",
    category: "Climat"
  },
  {
    id: "mock-climat-005",
    regulation_title: "Hausse niveau mer - Ports européens",
    risk_main: "Vulnérabilité des infrastructures portuaires",
    impact_level: "faible",
    risk_level: "faible",
    impact_gravity: "moyen",
    risk_details: "Élévation progressive du niveau de la mer affectant les terminaux portuaires utilisés pour l'import/export.",
    modality: "Surveillance à long terme",
    deadline: "01-01-2035",
    recommendation: "Intégrer le risque dans la planification à long terme, diversifier les routes logistiques",
    llm_reasoning: "Impact faible à court terme mais à surveiller",
    created_at: "2026-01-05",
    category: "Climat"
  },
  
  // ===== GÉOPOLITIQUE =====
  {
    id: "mock-geo-001",
    regulation_title: "Sanctions économiques - Russie",
    risk_main: "Restriction d'accès aux matières premières",
    impact_level: "critique",
    risk_level: "eleve",
    impact_gravity: "fort",
    risk_details: "Sanctions européennes impactant l'approvisionnement en métaux rares et produits chimiques d'origine russe.",
    modality: "Embargo et contrôles à l'exportation",
    deadline: "En vigueur",
    recommendation: "Identifier les fournisseurs alternatifs, vérifier la conformité de la chaîne, documenter l'origine des matériaux",
    llm_reasoning: "Impact critique nécessitant une restructuration des approvisionnements",
    created_at: "2026-01-10",
    category: "Géopolitique"
  },
  {
    id: "mock-geo-002",
    regulation_title: "Tensions commerciales Chine-UE",
    risk_main: "Hausse des droits de douane",
    impact_level: "eleve",
    risk_level: "eleve",
    impact_gravity: "moyen",
    risk_details: "Escalade potentielle des tarifs douaniers sur les produits automobiles et composants. Impact sur les coûts d'import depuis Wuhan.",
    modality: "Droits de douane additionnels de 10-25%",
    deadline: "01-03-2026",
    recommendation: "Évaluer l'impact sur les coûts, étudier la relocalisation partielle, négocier avec les fournisseurs",
    llm_reasoning: "Impact élevé sur la compétitivité des produits fabriqués en Chine",
    created_at: "2026-01-14",
    category: "Géopolitique"
  },
  {
    id: "mock-geo-003",
    regulation_title: "Instabilité politique - Moyen-Orient",
    risk_main: "Perturbation routes maritimes",
    impact_level: "eleve",
    risk_level: "moyen",
    impact_gravity: "fort",
    risk_details: "Tensions en Mer Rouge impactant le transit par Suez. Allongement des délais et surcoûts logistiques.",
    modality: "Contournement par le Cap de Bonne Espérance",
    deadline: "En cours",
    recommendation: "Anticiper les délais supplémentaires, renégocier les contrats logistiques, augmenter les stocks",
    llm_reasoning: "Impact élevé sur les coûts et délais de livraison",
    created_at: "2026-01-20",
    category: "Géopolitique"
  },
  {
    id: "mock-geo-004",
    regulation_title: "Réglementations locales - Chine",
    risk_main: "Nouvelles exigences de localisation des données",
    impact_level: "moyen",
    risk_level: "moyen",
    impact_gravity: "moyen",
    risk_details: "Renforcement des lois sur la souveraineté des données en Chine. Impact sur les systèmes IT et la collaboration avec Wuhan.",
    modality: "Hébergement local obligatoire des données",
    deadline: "01-01-2027",
    recommendation: "Auditer les flux de données, mettre en place des serveurs locaux, adapter les processus",
    llm_reasoning: "Impact moyen mais nécessitant des investissements IT significatifs",
    created_at: "2026-01-16",
    category: "Géopolitique"
  },
  {
    id: "mock-geo-005",
    regulation_title: "Conflits sociaux - Europe de l'Est",
    risk_main: "Risque de grèves et tensions salariales",
    impact_level: "moyen",
    risk_level: "faible",
    impact_gravity: "moyen",
    risk_details: "Pression salariale croissante en Pologne avec risque de mouvements sociaux dans l'industrie automobile.",
    modality: "Négociations salariales annuelles",
    deadline: "01-04-2026",
    recommendation: "Anticiper les revendications, maintenir le dialogue social, prévoir des ajustements budgétaires",
    llm_reasoning: "Impact moyen sur la continuité opérationnelle",
    created_at: "2026-01-25",
    category: "Géopolitique"
  }
];

/**
 * Statistiques calculées depuis les données mock
 */
export const MOCK_IMPACT_STATS = [
  { name: 'Faible', value: MOCK_IMPACTS.filter(i => i.impact_level === 'faible').length, color: '#10B981' },
  { name: 'Moyen', value: MOCK_IMPACTS.filter(i => i.impact_level === 'moyen').length, color: '#F59E0B' },
  { name: 'Elevé', value: MOCK_IMPACTS.filter(i => i.impact_level === 'eleve').length, color: '#F97316' },
  { name: 'Critique', value: MOCK_IMPACTS.filter(i => i.impact_level === 'critique').length, color: '#EF4444' },
];

/**
 * Tendance mensuelle mock
 */
export const MOCK_TREND_DATA = [
  { name: 'Oct 2025', val: 2 },
  { name: 'Nov 2025', val: 3 },
  { name: 'Déc 2025', val: 4 },
  { name: 'Jan 2026', val: 6 },
  { name: 'Fév 2026', val: 8 },
];

/**
 * Données des sites Hutchinson avec géolocalisation
 * Source: PING_Collecte_Donnees - Sample1.xlsx
 */
export interface MockSupplier {
  id: string;
  name: string;
  country: string;
  city?: string;
  lat: number;
  lng: number;
  riskLevel: 'faible' | 'moyen' | 'eleve';
  riskCount: number;
  regulations: string[];
  sector?: string;
  employees?: number;
}

export const MOCK_SUPPLIERS: MockSupplier[] = [
  // Sites Hutchinson réels (depuis le fichier Excel)
  {
    id: "site-chemille",
    name: "Hutchinson Chemille",
    country: "France",
    city: "Chemillé-en-Anjou",
    lat: 47.221786,
    lng: -0.734457,
    riskLevel: "faible",
    riskCount: 1,
    regulations: ["CSRD"],
    sector: "ADI",
    employees: 354
  },
  {
    id: "site-lodz1a",
    name: "Hutchinson Lodz 1A",
    country: "Pologne",
    city: "Lodz",
    lat: 51.736948,
    lng: 19.577903,
    riskLevel: "moyen",
    riskCount: 2,
    regulations: ["CSRD", "CS3D"],
    sector: "BSS",
    employees: 1700
  },
  {
    id: "site-blagnac",
    name: "Hutchinson Blagnac",
    country: "France",
    city: "Blagnac",
    lat: 43.640556,
    lng: 1.369784,
    riskLevel: "faible",
    riskCount: 1,
    regulations: ["CSRD"],
    sector: "ADI",
    employees: 50
  },
  {
    id: "site-madrid",
    name: "Hutchinson Madrid",
    country: "Espagne",
    city: "Arganda del Rey",
    lat: 40.318950,
    lng: -3.463259,
    riskLevel: "moyen",
    riskCount: 2,
    regulations: ["CSRD", "Taxonomie UE"],
    sector: "BSS",
    employees: 607
  },
  {
    id: "site-bielsko",
    name: "Hutchinson Bielsko Biala",
    country: "Pologne",
    city: "Bielsko Biala",
    lat: 49.833917,
    lng: 18.974672,
    riskLevel: "moyen",
    riskCount: 2,
    regulations: ["CSRD", "CS3D"],
    sector: "FMS",
    employees: 1072
  },
  {
    id: "site-wuhan",
    name: "Hutchinson Wuhan",
    country: "Chine",
    city: "Wuhan",
    lat: 30.485835,
    lng: 114.188638,
    riskLevel: "eleve",
    riskCount: 4,
    regulations: ["CBAM", "CS3D", "CSRD", "Batteries"],
    sector: "FMS",
    employees: 1291
  },
  // Fournisseurs tiers à risque (pour la démonstration)
  {
    id: "supplier-rubber-my",
    name: "RubberTech Malaysia",
    country: "Malaisie",
    city: "Kuala Lumpur",
    lat: 3.1390,
    lng: 101.6869,
    riskLevel: "eleve",
    riskCount: 2,
    regulations: ["EUDR", "CS3D"]
  },
  {
    id: "supplier-rubber-id",
    name: "Caoutchouc Naturel Sumatra",
    country: "Indonésie",
    city: "Medan",
    lat: 3.5952,
    lng: 98.6722,
    riskLevel: "eleve",
    riskCount: 3,
    regulations: ["EUDR", "CS3D", "Déforestation"]
  },
  {
    id: "supplier-steel-de",
    name: "SteelWorks GmbH",
    country: "Allemagne",
    city: "Duisburg",
    lat: 51.4344,
    lng: 6.7623,
    riskLevel: "moyen",
    riskCount: 2,
    regulations: ["CBAM", "CSRD"]
  },
  {
    id: "supplier-rubber-ci",
    name: "Caoutchouc Côte d'Ivoire",
    country: "Côte d'Ivoire",
    city: "Abidjan",
    lat: 5.3600,
    lng: -4.0083,
    riskLevel: "eleve",
    riskCount: 2,
    regulations: ["EUDR", "CS3D"]
  },
  {
    id: "supplier-chem-in",
    name: "ChemPro India",
    country: "Inde",
    city: "Mumbai",
    lat: 19.0760,
    lng: 72.8777,
    riskLevel: "moyen",
    riskCount: 2,
    regulations: ["REACH", "CS3D"]
  }
];
