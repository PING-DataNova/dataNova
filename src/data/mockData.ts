import { Regulation } from '../types';

// Données de test basées sur les images fournies
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