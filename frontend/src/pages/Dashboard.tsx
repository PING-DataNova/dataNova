
import React, { useState, useEffect } from 'react';
import { User, RiskData, Notification } from '../types';
import RiskTable from '../components/RiskTable';
import NotificationCenter from '../components/NotificationCenter';
import RiskMatrix, { RiskMatrixItem } from '../components/RiskMatrix';
import RiskMatrixAdvanced from '../components/RiskMatrixAdvanced';
import RiskDonutChart from '../components/RiskDonutChart';
import SupplierMap, { SupplierLocation } from '../components/SupplierMap';
import RiskDetailModal from '../components/RiskDetailModal';
import SupplierProfileModal from '../components/SupplierProfileModal';
import { impactsService, RiskDetailResponse } from '../services/impactsService';
import { getSupplierProfile, searchSupplierByName, SupplierDBProfile } from '../services/supplierService';
import { USE_MOCK_DATA, MOCK_IMPACTS, MOCK_IMPACT_STATS, MOCK_TREND_DATA, MOCK_SUPPLIERS } from '../data/mockImpacts';

interface DashboardProps {
  user: User;
  onLogout: () => void;
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard' | 'agent' | 'supplier-analysis' | 'admin') => void;
}

// Interface pour les utilisateurs en attente (Admin)
interface PendingUser {
  id: string;
  fullName: string;
  email: string;
  role: string;
  department?: string;
  requestDate: Date;
  status: 'pending' | 'approved' | 'rejected';
}

// Données mock des utilisateurs en attente
const MOCK_PENDING_USERS: PendingUser[] = [
  {
    id: '1',
    fullName: 'Marie Dupont',
    email: 'marie.dupont@hutchinson.com',
    role: 'Analyste',
    department: 'Supply Chain',
    requestDate: new Date('2026-02-03T14:30:00'),
    status: 'pending',
  },
  {
    id: '2',
    fullName: 'Pierre Martin',
    email: 'pierre.martin@hutchinson.com',
    role: 'Manager',
    department: 'Achats',
    requestDate: new Date('2026-02-02T09:15:00'),
    status: 'pending',
  },
  {
    id: '3',
    fullName: 'Sophie Bernard',
    email: 'sophie.bernard@hutchinson.com',
    role: 'Analyste',
    department: 'Qualité',
    requestDate: new Date('2026-02-01T16:45:00'),
    status: 'pending',
  },
  {
    id: '4',
    fullName: 'Lucas Petit',
    email: 'lucas.petit@hutchinson.com',
    role: 'Viewer',
    department: 'Production',
    requestDate: new Date('2026-01-31T11:20:00'),
    status: 'pending',
  },
  {
    id: '5',
    fullName: 'Emma Leroy',
    email: 'emma.leroy@hutchinson.com',
    role: 'Analyste',
    department: 'R&D',
    requestDate: new Date('2026-01-30T08:00:00'),
    status: 'approved',
  },
  {
    id: '6',
    fullName: 'Thomas Moreau',
    email: 'thomas.moreau@external.com',
    role: 'Viewer',
    department: 'Externe',
    requestDate: new Date('2026-01-29T15:30:00'),
    status: 'rejected',
  },
];

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout, onNavigate }) => {
  const [activeTab, setActiveTab] = useState<'Dashboard' | 'Réglementations' | 'Climat' | 'Géopolitique' | 'Administration'>('Dashboard');
  const [notifications] = useState<Notification[]>([]);
  const [showRealTimeToast, setShowRealTimeToast] = useState<string | null>(null);
  
  // États pour l'onglet Administration
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>(MOCK_PENDING_USERS);
  const [adminFilter, setAdminFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [adminSearchQuery, setAdminSearchQuery] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState<{ action: 'approve' | 'reject'; user: PendingUser } | null>(null);

  // États pour le modal de détails de risque
  const [selectedRiskDetails, setSelectedRiskDetails] = useState<RiskDetailResponse | null>(null);
  const [loadingRiskDetails, setLoadingRiskDetails] = useState(false);
  const [showRiskModal, setShowRiskModal] = useState(false);

  // Fonction pour charger les détails d'un risque
  const handleViewRiskDetails = async (riskId: string) => {
    setShowRiskModal(true);
    setLoadingRiskDetails(true);
    setSelectedRiskDetails(null);
    
    try {
      const details = await impactsService.getRiskDetails(riskId);
      setSelectedRiskDetails(details);
    } catch (error) {
      console.error('Erreur chargement détails risque:', error);
    } finally {
      setLoadingRiskDetails(false);
    }
  };

  const handleCloseRiskModal = () => {
    setShowRiskModal(false);
    setSelectedRiskDetails(null);
  };

  // Fonctions Admin
  const handleApprove = (userId: string) => {
    setPendingUsers(prev => prev.map(u => 
      u.id === userId ? { ...u, status: 'approved' as const } : u
    ));
    setShowConfirmModal(null);
  };

  const handleReject = (userId: string) => {
    setPendingUsers(prev => prev.map(u => 
      u.id === userId ? { ...u, status: 'rejected' as const } : u
    ));
    setShowConfirmModal(null);
  };

  const filteredPendingUsers = pendingUsers.filter(u => {
    const matchesFilter = adminFilter === 'all' || u.status === adminFilter;
    const matchesSearch = u.fullName.toLowerCase().includes(adminSearchQuery.toLowerCase()) ||
                         u.email.toLowerCase().includes(adminSearchQuery.toLowerCase()) ||
                         (u.department?.toLowerCase().includes(adminSearchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const pendingCount = pendingUsers.filter(u => u.status === 'pending').length;
  const approvedCount = pendingUsers.filter(u => u.status === 'approved').length;
  const rejectedCount = pendingUsers.filter(u => u.status === 'rejected').length;

  const formatAdminDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const [risks, setRisks] = useState<RiskData[]>([]);
  const [, setLoadingRisks] = useState(true);
  const [, setImpactStats] = useState<{ name: string; value: number; color: string }[]>([]);
  const [, setTrendData] = useState<{ name: string; val: number }[]>([]);
  const [riskMatrixItems, setRiskMatrixItems] = useState<RiskMatrixItem[]>([]);
  
  // États pour les KPI du dashboard
  const [dashboardStats, setDashboardStats] = useState<{
    total_regulations: number;
    total_impacts: number;
    high_risks: number;
    medium_risks: number;
    low_risks: number;
    critical_deadlines: number;
    average_score?: number;
    by_risk_type: { [key: string]: number };
  } | null>(null);

  // Filtre des risques selon l'onglet actif
  const filteredRisks = risks.filter(r => r.category === activeTab);
  
  // Filtre de la matrice selon l'onglet (pour les onglets individuels)
  const filteredMatrixItems = riskMatrixItems.filter(item => item.category === activeTab);

  // Fonction pour obtenir le poids numérique du niveau de risque
  const getRiskWeight = (level: string): number => {
    const weights: Record<string, number> = {
      'critique': 4,
      'eleve': 3,
      'élevé': 3,
      'moyen': 2,
      'faible': 1,
    };
    return weights[level.toLowerCase()] || 0;
  };

  // Tous les risques triés pour le Dashboard (tri par risque décroissant par défaut)
  const allRisksSorted = [...risks].sort((a, b) => {
    const weightA = getRiskWeight(a.impact_level);
    const weightB = getRiskWeight(b.impact_level);
    return weightB - weightA;
  });

  // Load dashboard stats from backend
  useEffect(() => {
    const loadDashboardStats = async () => {
      try {
        const stats = await impactsService.getDashboardStats();
        setDashboardStats(stats);
      } catch (err) {
        console.error('Erreur chargement stats dashboard:', err);
      }
    };
    loadDashboardStats();
  }, []);

  // Load impacts from backend and compute stats
  // Si le backend ne retourne rien, utilise les données mock (désactivable via USE_MOCK_DATA)
  useEffect(() => {
    const loadImpacts = async () => {
      setLoadingRisks(true);
      try {
        const resp = await impactsService.getImpacts({ limit: 200 });
        
        // Si le backend retourne des données, les utiliser
        if (resp.impacts && resp.impacts.length > 0) {
          console.log('📊 Données backend reçues:', resp.impacts.length, 'impacts');
          
          const mapped: RiskData[] = resp.impacts.map(i => ({
            id: i.id,
            risk_main: i.regulation_title || i.risk_main,
            impact_level: i.impact_level as any,
            risk_details: i.risk_details || '',
            modality: i.modality || '',
            deadline: i.deadline || '',
            recommendation: i.recommendation || '',
            llm_reasoning: i.llm_reasoning || '',
            created_at: i.created_at,
            category: i.category || 'Réglementations',
          }));

          setRisks(mapped);

          // compute impactStats
          const counts: Record<string, number> = {};
          resp.impacts.forEach(it => { counts[it.impact_level] = (counts[it.impact_level] || 0) + 1; });
          const stats = [
            { name: 'Faible', value: counts['faible'] || 0, color: '#10B981' },
            { name: 'Moyen', value: counts['moyen'] || 0, color: '#F59E0B' },
            { name: 'Elevé', value: counts['eleve'] || 0, color: '#F97316' },
            { name: 'Critique', value: counts['critique'] || 0, color: '#EF4444' },
          ];
          setImpactStats(stats);

          // compute simple monthly trend from deadline (MM-YYYY or other)
          const months: Record<string, number> = {};
          resp.impacts.forEach(it => {
            const key = it.deadline || it.created_at || 'unknown';
            months[key] = (months[key] || 0) + 1;
          });
          const trend = Object.keys(months).slice(0,6).map(k => ({ name: k, val: months[k] }));
          setTrendData(trend);
          
          // Construire les données pour la matrice de risque depuis le backend
          // Mapper impact_level vers riskLevel et impactLevel pour la matrice
          const matrixItems: RiskMatrixItem[] = resp.impacts.map(i => {
            // Mapper impact_level vers les deux axes de la matrice
            // Par défaut: on utilise le même niveau pour risque et impact
            let riskLevel: 'faible' | 'moyen' | 'eleve' = 'moyen';
            let impactGravity: 'faible' | 'moyen' | 'fort' = 'moyen';
            
            if (i.impact_level === 'critique') {
              riskLevel = 'eleve';
              impactGravity = 'fort';
            } else if (i.impact_level === 'eleve') {
              riskLevel = 'eleve';
              impactGravity = 'moyen';
            } else if (i.impact_level === 'moyen') {
              riskLevel = 'moyen';
              impactGravity = 'moyen';
            } else {
              riskLevel = 'faible';
              impactGravity = 'faible';
            }
            
            return {
              id: i.id,
              title: i.regulation_title || i.risk_main,
              riskLevel,
              impactLevel: impactGravity,
              category: i.category || 'Réglementations',
            };
          });
          setRiskMatrixItems(matrixItems);
        } 
        // Sinon, utiliser les données mock si activées
        else if (USE_MOCK_DATA) {
          console.log('📊 Utilisation des données de démonstration (backend vide)');
          const mapped: RiskData[] = MOCK_IMPACTS.map(i => ({
            id: i.id,
            risk_main: i.regulation_title || i.risk_main,
            impact_level: i.impact_level as any,
            risk_details: i.risk_details || '',
            modality: i.modality,
            deadline: i.deadline,
            recommendation: i.recommendation || '',
            llm_reasoning: i.llm_reasoning || '',
            created_at: i.created_at,
            category: i.category,
          }));
          setRisks(mapped);
          setImpactStats(MOCK_IMPACT_STATS);
          setTrendData(MOCK_TREND_DATA);
          
          // Données pour la matrice de risque (toutes catégories)
          const matrixItems: RiskMatrixItem[] = MOCK_IMPACTS.map(i => ({
            id: i.id,
            title: i.regulation_title,
            riskLevel: i.risk_level,
            impactLevel: i.impact_gravity,
            category: i.category,
          }));
          setRiskMatrixItems(matrixItems);
        }
      } catch (err) {
        console.error('Erreur récupération impacts:', err);
        // En cas d'erreur, utiliser les données mock si activées
        if (USE_MOCK_DATA) {
          console.log('📊 Utilisation des données de démonstration (erreur backend)');
          const mapped: RiskData[] = MOCK_IMPACTS.map(i => ({
            id: i.id,
            risk_main: i.regulation_title || i.risk_main,
            impact_level: i.impact_level as any,
            risk_details: i.risk_details || '',
            modality: i.modality,
            deadline: i.deadline,
            recommendation: i.recommendation || '',
            llm_reasoning: i.llm_reasoning || '',
            created_at: i.created_at,
            category: i.category,
          }));
          setRisks(mapped);
          setImpactStats(MOCK_IMPACT_STATS);
          setTrendData(MOCK_TREND_DATA);
          
          // Données pour la matrice de risque (toutes catégories)
          const matrixItems: RiskMatrixItem[] = MOCK_IMPACTS.map(i => ({
            id: i.id,
            title: i.regulation_title,
            riskLevel: i.risk_level,
            impactLevel: i.impact_gravity,
            category: i.category,
          }));
          setRiskMatrixItems(matrixItems);
        }
      } finally {
        setLoadingRisks(false);
      }
    };
    loadImpacts();
  }, []);

  // État pour le modal de détails de la matrice
  const [matrixModalOpen, setMatrixModalOpen] = useState(false);
  const [selectedCellItems, setSelectedCellItems] = useState<RiskMatrixItem[]>([]);
  const [selectedCellInfo, setSelectedCellInfo] = useState<{ riskLevel: string; impactLevel: string }>({ riskLevel: '', impactLevel: '' });

  // État pour les fournisseurs et leur modal
  const [suppliers] = useState<SupplierLocation[]>(MOCK_SUPPLIERS);
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierLocation | null>(null);

  // États pour le modal de profil complet du fournisseur (depuis BDD)
  const [supplierProfileModalOpen, setSupplierProfileModalOpen] = useState(false);
  const [supplierProfile, setSupplierProfile] = useState<SupplierDBProfile | null>(null);
  const [loadingSupplierProfile, setLoadingSupplierProfile] = useState(false);
  const [supplierProfileError, setSupplierProfileError] = useState<string | null>(null);

  // Fonction pour charger le profil complet d'un fournisseur depuis la BDD
  const handleViewSupplierProfile = async (supplierId: string, supplierName?: string) => {
    setSupplierModalOpen(false); // Fermer le modal simple
    setSupplierProfileModalOpen(true);
    setLoadingSupplierProfile(true);
    setSupplierProfile(null);
    setSupplierProfileError(null);
    
    try {
      // D'abord essayer par ID
      const profile = await getSupplierProfile(supplierId);
      setSupplierProfile(profile);
    } catch (error) {
      // Si l'ID échoue et qu'on a un nom, essayer par nom
      if (supplierName) {
        try {
          const profile = await searchSupplierByName(supplierName);
          setSupplierProfile(profile);
          return;
        } catch (nameError) {
          console.error('Erreur recherche par nom:', nameError);
        }
      }
      console.error('Erreur chargement profil fournisseur:', error);
      setSupplierProfileError(
        'Fournisseur non trouvé dans la base de données. ' +
        'Ce fournisseur n\'a peut-être pas encore été enregistré.'
      );
    } finally {
      setLoadingSupplierProfile(false);
    }
  };

  const handleCloseSupplierProfile = () => {
    setSupplierProfileModalOpen(false);
    setSupplierProfile(null);
    setSupplierProfileError(null);
  };

  const handleSupplierClick = (supplier: SupplierLocation) => {
    setSelectedSupplier(supplier);
    setSupplierModalOpen(true);
  };

  const handleMatrixCellClick = (riskLevel: string, impactLevel: string, items: RiskMatrixItem[]) => {
    if (items.length > 0) {
      setSelectedCellItems(items);
      setSelectedCellInfo({ riskLevel, impactLevel });
      setMatrixModalOpen(true);
    }
  };

  // Labels pour l'affichage
  const riskLevelLabels: Record<string, string> = { eleve: 'Élevé', moyen: 'Moyen', faible: 'Faible' };
  const impactLevelLabels: Record<string, string> = { fort: 'Fort', moyen: 'Moyen', faible: 'Faible' };

  // Trouver les détails complets d'un risque par son ID
  const getFullRiskDetails = (id: string) => {
    return risks.find(r => r.id === id) || MOCK_IMPACTS.find(i => i.id === id);
  };

  return (
    <div className="flex h-screen bg-[#F8FAFC] font-sans selection:bg-lime-200">
      
      {/* Modal Détails Fournisseur */}
      {supplierModalOpen && selectedSupplier && (
        <div 
          className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm" 
          style={{ zIndex: 10000 }}
          onClick={() => setSupplierModalOpen(false)}
        >
          <div 
            className="bg-white rounded-3xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden relative"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className={`p-6 ${
              selectedSupplier.riskLevel === 'eleve' 
                ? 'bg-gradient-to-r from-red-500 to-red-600' 
                : selectedSupplier.riskLevel === 'moyen'
                  ? 'bg-gradient-to-r from-amber-400 to-amber-500'
                  : 'bg-gradient-to-r from-emerald-400 to-emerald-500'
            }`}>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-black text-white">{selectedSupplier.name}</h2>
                  <p className="text-white/80 text-sm">{selectedSupplier.city}, {selectedSupplier.country}</p>
                </div>
              </div>
              <button 
                onClick={() => setSupplierModalOpen(false)}
                className="absolute top-4 right-4 w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-colors"
              >
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${
                  selectedSupplier.riskLevel === 'eleve' 
                    ? 'bg-red-100 text-red-700' 
                    : selectedSupplier.riskLevel === 'moyen'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-emerald-100 text-emerald-700'
                }`}>
                  Risque {riskLevelLabels[selectedSupplier.riskLevel] || selectedSupplier.riskLevel}
                </span>
                <span className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-full text-sm font-bold">
                  {selectedSupplier.riskCount} réglementation{selectedSupplier.riskCount > 1 ? 's' : ''}
                </span>
              </div>

              <div className="space-y-3">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-400">Réglementations impactantes</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedSupplier.regulations?.map((reg: string, idx: number) => (
                    <span key={idx} className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700">
                      {reg}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex gap-2">
                <button 
                  onClick={() => {
                    // Charger le profil complet depuis la BDD
                    if (selectedSupplier.id) {
                      handleViewSupplierProfile(selectedSupplier.id, selectedSupplier.name);
                    }
                  }}
                  className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-colors"
                >
                  Voir profil complet
                </button>
                <button 
                  onClick={() => setSupplierModalOpen(false)}
                  className="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-200 transition-colors"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Détails Matrice */}
      {matrixModalOpen && (
        <div 
          className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm" 
          style={{ zIndex: 10000 }}
          onClick={() => setMatrixModalOpen(false)}
        >
          <div 
            className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className={`p-6 ${
              selectedCellInfo.riskLevel === 'eleve' && selectedCellInfo.impactLevel === 'fort' 
                ? 'bg-gradient-to-r from-red-500 to-red-600' 
                : selectedCellInfo.riskLevel === 'eleve' || selectedCellInfo.impactLevel === 'fort'
                  ? 'bg-gradient-to-r from-orange-400 to-orange-500'
                  : 'bg-gradient-to-r from-slate-600 to-slate-700'
            }`}>
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-white text-xl font-black mb-1">
                    Risque {riskLevelLabels[selectedCellInfo.riskLevel]} / Impact {impactLevelLabels[selectedCellInfo.impactLevel]}
                  </h2>
                  <p className="text-white/80 text-sm">
                    {selectedCellItems.length} réglementation{selectedCellItems.length > 1 ? 's' : ''} concernée{selectedCellItems.length > 1 ? 's' : ''}
                  </p>
                </div>
                <button 
                  onClick={() => setMatrixModalOpen(false)}
                  className="text-white/80 hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Liste des risques */}
            <div className="p-6 overflow-y-auto max-h-[60vh] space-y-4">
              {selectedCellItems.map(item => {
                const details = getFullRiskDetails(item.id);
                return (
                  <div key={item.id} className="border border-slate-200 rounded-2xl p-5 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-bold text-slate-900 text-lg">{item.title}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                        selectedCellInfo.riskLevel === 'eleve' && selectedCellInfo.impactLevel === 'fort'
                          ? 'bg-red-100 text-red-700'
                          : selectedCellInfo.riskLevel === 'eleve' || selectedCellInfo.impactLevel === 'fort'
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {selectedCellInfo.riskLevel === 'eleve' && selectedCellInfo.impactLevel === 'fort' ? 'Critique' : 'À surveiller'}
                      </span>
                    </div>
                    
                    {details && (
                      <>
                        <p className="text-slate-600 text-sm mb-4">
                          {('risk_details' in details ? details.risk_details : '') || ('risk_main' in details ? details.risk_main : '')}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-slate-400 font-medium block mb-1">Échéance</span>
                            <span className="text-slate-700 font-bold">
                              {('deadline' in details ? details.deadline : 'N/A') || 'Non définie'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400 font-medium block mb-1">Modalité</span>
                            <span className="text-slate-700">
                              {('modality' in details ? details.modality : 'N/A') || 'Non définie'}
                            </span>
                          </div>
                        </div>
                        
                        {('recommendation' in details && details.recommendation) && (
                          <div className="mt-4 p-3 bg-lime-50 rounded-xl border border-lime-200">
                            <span className="text-lime-700 font-bold text-xs uppercase block mb-1">Recommandation</span>
                            <p className="text-lime-800 text-sm">{details.recommendation}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification Pop-up */}
      {showRealTimeToast && (
        <div className="fixed top-8 right-8 z-[100] animate-bounce">
           <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-2xl flex items-center space-x-4 border border-lime-400/30 backdrop-blur-xl">
              <div className="w-10 h-10 bg-lime-400 rounded-xl flex items-center justify-center">
                 <svg className="w-6 h-6 text-slate-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-lime-400">Nouveau Risque</p>
                 <p className="text-sm font-bold">{showRealTimeToast}</p>
              </div>
              <button onClick={() => setShowRealTimeToast(null)} className="text-slate-500 hover:text-white transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
           </div>
        </div>
      )}

      {/* Modern Slim Sidebar */}
      <aside className="w-20 lg:w-72 flex-shrink-0 bg-slate-950 text-slate-300 flex flex-col">
        <div className="p-6 flex flex-col items-center lg:items-start mb-10">
          <img src="/hutchinson-logo-white.svg" alt="Hutchinson" className="hidden lg:block h-8 object-contain mb-4" />
          <img src="/hutchinson-logo.svg" alt="Hutchinson" className="lg:hidden w-12 h-12 object-contain" />
          <span className="hidden lg:block text-[10px] text-lime-400 font-medium tracking-widest">DATANOVA RISK PLATFORM</span>
        </div>

        <nav className="flex-grow px-4 space-y-3">
          {(['Dashboard', 'Réglementations', 'Climat', 'Géopolitique'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full group relative flex items-center lg:space-x-4 p-3 lg:px-5 lg:py-4 rounded-2xl transition-all duration-300 ${
                activeTab === tab 
                  ? 'bg-slate-800 text-lime-400' 
                  : 'hover:bg-slate-900 text-slate-500 hover:text-white'
              }`}
            >
              <div className="flex-shrink-0">
                {tab === 'Dashboard' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"/></svg>}
                {tab === 'Réglementations' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>}
                {tab === 'Climat' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"/></svg>}
                {tab === 'Géopolitique' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9h18"/></svg>}
              </div>
              <span className="hidden lg:block font-bold text-sm tracking-tight">{tab}</span>
              {activeTab === tab && <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-lime-400 rounded-l-full hidden lg:block"></div>}
            </button>
          ))}
          
          {/* Onglet Administration - visible uniquement pour les admins */}
          {user.role === 'admin' && (
            <button
              onClick={() => onNavigate('admin')}
              className={`w-full group relative flex items-center lg:space-x-4 p-3 lg:px-5 lg:py-4 rounded-2xl transition-all duration-300 hover:bg-slate-900 text-amber-500/60 hover:text-amber-400`}
            >
              <div className="flex-shrink-0">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              </div>
              <span className="hidden lg:block font-bold text-sm tracking-tight">Administration</span>
              {pendingCount > 0 && (
                <span className="hidden lg:flex ml-auto bg-amber-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>
          )}
        </nav>

        <div className="p-6">
           <div className="hidden lg:block bg-slate-900 p-4 rounded-2xl mb-6">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Utilisateur</p>
              <div className="flex items-center space-x-3">
                 <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-black text-xs text-white">JD</div>
                 <div className="overflow-hidden">
                    <p className="text-sm font-bold text-white truncate">{user.fullName}</p>
                    <p className="text-[10px] text-lime-400 font-bold uppercase">{user.role}</p>
                 </div>
              </div>
           </div>
           <button 
             onClick={onLogout}
             className="w-full flex items-center lg:space-x-3 p-3 lg:px-4 text-slate-500 hover:text-red-400 transition-colors"
           >
             <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
             <span className="hidden lg:block text-xs font-black uppercase tracking-widest">Logout</span>
           </button>
        </div>
      </aside>

      {/* Dashboard Main View */}
      <main className="flex-grow flex flex-col overflow-hidden">
        {/* Header Navigation */}
        <header className="px-10 py-6 flex justify-between items-center bg-white border-b border-slate-100">
          <div>
             <h1 className="text-3xl font-black text-slate-900 tracking-tighter">{activeTab}</h1>
          </div>
          <div className="flex items-center space-x-8">
             <div className="hidden md:flex bg-slate-50 px-4 py-2 rounded-xl border border-slate-100 items-center">
                <svg className="w-4 h-4 text-slate-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <input type="text" placeholder="Rechercher un dossier..." className="bg-transparent text-sm font-medium outline-none w-48" />
             </div>
             <NotificationCenter notifications={notifications} />
          </div>
        </header>

        {/* Dynamic Content */}
        <div className="flex-grow overflow-y-auto p-10 space-y-10 custom-scrollbar">
          
          {/* Dashboard View - Vue globale avec KPIs */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-8">
              
              {/* KPI Cards Row - Comme dans la maquette */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Active Alerts */}
                <div className="bg-white rounded-2xl p-6 border-2 border-amber-200 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-amber-100 rounded-xl flex items-center justify-center">
                      <svg className="w-7 h-7 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                    </div>
                    <div>
                      <p className="text-4xl font-black text-amber-600">{dashboardStats?.total_impacts || 0}</p>
                      <p className="text-sm font-medium text-slate-600">Alertes Actives</p>
                      <p className="text-xs text-amber-600">{dashboardStats?.high_risks || 0} critiques</p>
                    </div>
                  </div>
                </div>

                {/* Critical Risk */}
                <div className="bg-white rounded-2xl p-6 border-2 border-red-200 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center">
                      <svg className="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                    </div>
                    <div>
                      <p className="text-4xl font-black text-red-600">{dashboardStats?.high_risks || 0}</p>
                      <p className="text-sm font-medium text-slate-600">Risques Critiques</p>
                      <p className="text-xs text-red-600">Action requise</p>
                    </div>
                  </div>
                </div>

                {/* Avg Risk Score */}
                <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center">
                      <svg className="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                    </div>
                    <div>
                      <p className="text-4xl font-black text-blue-600">
                        {dashboardStats?.average_score ? Math.round(dashboardStats.average_score) : 0}
                        <span className="text-lg text-slate-400">/100</span>
                      </p>
                      <p className="text-sm font-medium text-slate-600">Score Moyen</p>
                      <p className="text-xs text-blue-600">
                        {dashboardStats?.average_score && dashboardStats.average_score >= 70 ? 'Niveau élevé' : 
                         dashboardStats?.average_score && dashboardStats.average_score >= 40 ? 'Niveau modéré' : 'Niveau faible'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Documents Processed */}
                <div className="bg-white rounded-2xl p-6 border-2 border-emerald-200 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <svg className="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    </div>
                    <div>
                      <p className="text-4xl font-black text-emerald-600">{dashboardStats?.total_regulations || 0}</p>
                      <p className="text-sm font-medium text-slate-600">Documents Traités</p>
                      <p className="text-xs text-emerald-600">Dernières 24h</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Main Content Row: Map + Recent Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* World Map Section - 2/3 width */}
                <div className="lg:col-span-2 bg-white rounded-[2rem] p-6 shadow-sm border border-slate-100">
                  <h3 className="text-xl font-black text-slate-900 mb-4">Carte des Risques Mondiaux</h3>
                  <div className="h-[400px] rounded-2xl overflow-hidden">
                    <SupplierMap 
                      suppliers={suppliers} 
                      onSupplierClick={handleSupplierClick}
                    />
                  </div>
                </div>

                {/* Recent Alerts Panel - 1/3 width */}
                <div className="bg-white rounded-[2rem] p-6 shadow-sm border border-slate-100">
                  <h3 className="text-lg font-black text-slate-900 mb-4">Alertes Récentes</h3>
                  <div className="space-y-3 max-h-[400px] overflow-y-auto">
                    {allRisksSorted.slice(0, 5).map((risk, idx) => (
                      <div key={risk.id || idx} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <div className="flex items-start gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            risk.impact_level === 'critique' ? 'bg-red-100' :
                            risk.impact_level === 'eleve' ? 'bg-orange-100' :
                            risk.impact_level === 'moyen' ? 'bg-yellow-100' : 'bg-green-100'
                          }`}>
                            <span className={`w-3 h-3 rounded-full ${
                              risk.impact_level === 'critique' ? 'bg-red-500' :
                              risk.impact_level === 'eleve' ? 'bg-orange-500' :
                              risk.impact_level === 'moyen' ? 'bg-yellow-500' : 'bg-green-500'
                            }`}></span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-slate-400">{new Date(risk.created_at || '').toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })}</p>
                            <p className="font-bold text-sm text-slate-900 truncate">{risk.impact_level?.toUpperCase()}</p>
                            <p className="text-xs text-slate-600 line-clamp-2">{risk.risk_main}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                    {allRisksSorted.length === 0 && (
                      <div className="text-center py-8 text-slate-400">
                        <p>Aucune alerte</p>
                      </div>
                    )}
                  </div>
                  <button 
                    onClick={() => setActiveTab('Réglementations')}
                    className="w-full mt-4 py-3 bg-blue-500 text-white rounded-xl font-bold hover:bg-blue-600 transition-colors"
                  >
                    Voir Toutes les Alertes
                  </button>
                </div>
              </div>

              {/* TOP 10 Risques - Comme demandé par le client */}
              <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-xl font-black text-slate-900">Top 10 Risques Critiques</h3>
                    <p className="text-sm text-slate-500">Les impacts les plus importants à traiter en priorité</p>
                  </div>
                  <div className="flex gap-2">
                    <span className="px-3 py-1 bg-red-100 text-red-600 rounded-full text-xs font-bold">
                      {allRisksSorted.filter(r => r.impact_level === 'critique').length} critiques
                    </span>
                    <span className="px-3 py-1 bg-orange-100 text-orange-600 rounded-full text-xs font-bold">
                      {allRisksSorted.filter(r => r.impact_level === 'eleve').length} élevés
                    </span>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">#</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Risque</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Catégorie</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Niveau</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Date</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allRisksSorted.slice(0, 10).map((risk, idx) => (
                        <tr key={risk.id || idx} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                          <td className="py-4 px-4">
                            <span className={`w-8 h-8 flex items-center justify-center rounded-full font-black text-sm ${
                              idx < 3 ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'
                            }`}>
                              {idx + 1}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <p className="font-bold text-slate-900 line-clamp-1">{risk.risk_main}</p>
                            <p className="text-xs text-slate-500 line-clamp-1">{risk.risk_details}</p>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                              risk.category === 'Climat' ? 'bg-emerald-100 text-emerald-700' :
                              risk.category === 'Géopolitique' ? 'bg-purple-100 text-purple-700' :
                              'bg-orange-100 text-orange-700'
                            }`}>
                              {risk.category}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                              risk.impact_level === 'critique' ? 'bg-red-100 text-red-700' :
                              risk.impact_level === 'eleve' ? 'bg-orange-100 text-orange-700' :
                              risk.impact_level === 'moyen' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              {risk.impact_level?.toUpperCase()}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-sm text-slate-600">
                            {new Date(risk.created_at || '').toLocaleDateString('fr-FR')}
                          </td>
                          <td className="py-4 px-4">
                            <button 
                              onClick={() => handleViewRiskDetails(risk.id)}
                              className="px-4 py-2 bg-blue-500 text-white rounded-lg text-xs font-bold hover:bg-blue-600 transition-colors"
                            >
                              Détails
                            </button>
                          </td>
                        </tr>
                      ))}
                      {allRisksSorted.length === 0 && (
                        <tr>
                          <td colSpan={6} className="py-12 text-center text-slate-400">
                            Aucun risque identifié pour le moment
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Visualisation Risques - Style sombre comme la maquette */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Donut Chart - Classification des Risques */}
                <div className="h-[350px]">
                  <RiskDonutChart 
                    title="Classification des Risques"
                    data={[
                      { 
                        label: 'Critique', 
                        value: allRisksSorted.filter(r => r.impact_level === 'critique').length, 
                        color: '#ef4444' 
                      },
                      { 
                        label: 'Élevé', 
                        value: allRisksSorted.filter(r => r.impact_level === 'eleve').length, 
                        color: '#f97316' 
                      },
                      { 
                        label: 'Moyen', 
                        value: allRisksSorted.filter(r => r.impact_level === 'moyen').length, 
                        color: '#eab308' 
                      },
                      { 
                        label: 'Faible', 
                        value: allRisksSorted.filter(r => r.impact_level === 'faible').length, 
                        color: '#22c55e' 
                      },
                    ]}
                  />
                </div>

                {/* Matrice de Risque Avancée */}
                <div className="h-[350px]">
                  <RiskMatrixAdvanced 
                    title="Matrice Risque / Impact"
                    items={allRisksSorted.map((risk, idx) => ({
                      id: risk.id || String(idx),
                      title: risk.risk_main,
                      probability: risk.impact_level === 'critique' ? 85 + Math.random() * 15 :
                                   risk.impact_level === 'eleve' ? 60 + Math.random() * 25 :
                                   risk.impact_level === 'moyen' ? 30 + Math.random() * 30 :
                                   5 + Math.random() * 25,
                      impact: risk.impact_level === 'critique' ? 80 + Math.random() * 20 :
                              risk.impact_level === 'eleve' ? 55 + Math.random() * 25 :
                              risk.impact_level === 'moyen' ? 30 + Math.random() * 25 :
                              5 + Math.random() * 25,
                      category: risk.category as any
                    }))}
                    onPointClick={(point) => {
                      alert(`${point.title}\nProbabilité: ${Math.round(point.probability)}%\nImpact: ${Math.round(point.impact)}%`);
                    }}
                  />
                </div>
              </div>

              {/* Quick Access Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <button 
                  onClick={() => setActiveTab('Réglementations')}
                  className="bg-white p-6 rounded-[2rem] border border-slate-100 hover:shadow-lg hover:-translate-y-1 transition-all text-left group"
                >
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-orange-200 transition-colors">
                    <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                  </div>
                  <h4 className="font-bold text-slate-900 mb-1">Réglementations</h4>
                  <p className="text-sm text-slate-500">{dashboardStats?.by_risk_type?.reglementaire || 0} risques actifs</p>
                </button>
                
                <button 
                  onClick={() => setActiveTab('Climat')}
                  className="bg-white p-6 rounded-[2rem] border border-slate-100 hover:shadow-lg hover:-translate-y-1 transition-all text-left group"
                >
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-200 transition-colors">
                    <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"/></svg>
                  </div>
                  <h4 className="font-bold text-slate-900 mb-1">Risques Climat</h4>
                  <p className="text-sm text-slate-500">{dashboardStats?.by_risk_type?.climat || 0} alertes climat</p>
                </button>
                
                <button 
                  onClick={() => setActiveTab('Géopolitique')}
                  className="bg-white p-6 rounded-[2rem] border border-slate-100 hover:shadow-lg hover:-translate-y-1 transition-all text-left group"
                >
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9h18"/></svg>
                  </div>
                  <h4 className="font-bold text-slate-900 mb-1">Géopolitique</h4>
                  <p className="text-sm text-slate-500">{dashboardStats?.by_risk_type?.geopolitique || 0} risques géopolitiques</p>
                </button>
              </div>

              {/* Bouton Analyse Fournisseur */}
              <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2rem] p-8 text-center">
                <h3 className="text-2xl font-black text-white mb-4">Analyser un Fournisseur</h3>
                <p className="text-slate-400 mb-6">Lancez une analyse complète de risques pour un fournisseur spécifique</p>
                <button
                  onClick={() => onNavigate('supplier-analysis')}
                  className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-lime-400 to-emerald-500 text-slate-900 font-black text-lg hover:from-lime-300 hover:to-emerald-400 transition-all"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                  </svg>
                  Lancer une Analyse
                </button>
              </div>

            </div>
          )}

          {/* Other tabs content (Réglementations, Climat, Géopolitique) */}
          {activeTab !== 'Dashboard' && activeTab !== 'Administration' && (
            <>
          {/* Key Stats Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-5 bg-white p-6 rounded-[2.5rem] shadow-sm border border-slate-100">
               <div className="flex items-center justify-between gap-3 mb-4">
                  <h3 className="text-xs font-black uppercase tracking-[0.12em] text-slate-400">Risque / Impact - {activeTab}</h3>
                  {filteredMatrixItems.filter(i => i.riskLevel === 'eleve' && i.impactLevel === 'fort').length > 0 && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-500 text-white rounded-full text-[10px] font-bold whitespace-nowrap">
                      <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                      {filteredMatrixItems.filter(i => i.riskLevel === 'eleve' && i.impactLevel === 'fort').length} critique{filteredMatrixItems.filter(i => i.riskLevel === 'eleve' && i.impactLevel === 'fort').length > 1 ? 's' : ''}
                    </span>
                  )}
               </div>
               <div className="h-72">
                  <RiskMatrix items={filteredMatrixItems} onCellClick={handleMatrixCellClick} />
               </div>
            </div>

            <div className="lg:col-span-7 bg-slate-900 p-6 rounded-[2.5rem] shadow-xl relative overflow-hidden" style={{ minHeight: '380px' }}>
               <div className="relative z-10 flex flex-col h-full">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Localisation des Fournisseurs</h3>
                      <p className="text-lg font-black text-white">
                        <span className="text-red-400">{suppliers.filter(s => s.riskLevel === 'eleve').length}</span> fournisseurs à risque élevé
                      </p>
                    </div>
                    <div className="flex space-x-2">
                       <span className="px-3 py-1 bg-slate-800 rounded-lg text-[10px] font-bold text-slate-400">
                         {suppliers.length} fournisseurs
                       </span>
                    </div>
                  </div>
                  <div className="flex-1" style={{ minHeight: '280px' }}>
                    <SupplierMap 
                      suppliers={suppliers} 
                      onSupplierClick={handleSupplierClick}
                    />
                  </div>
               </div>
            </div>
          </div>

          {/* List Section */}
          <div className="space-y-6">
             <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 tracking-tighter">Inventaire des Menaces: {activeTab}</h2>
                  <p className="text-slate-400 text-sm font-medium">Données actualisées en temps réel par notre moteur de veille.</p>
                </div>
                <div className="flex items-center space-x-3">
                   <button className="px-6 py-3 bg-white border border-slate-200 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50 transition-colors">Filtrer</button>
                   <button className="px-6 py-3 bg-slate-900 text-white rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center space-x-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                      <span>Rapport PDF</span>
                   </button>
                </div>
             </div>

             <div className="group">
                <RiskTable risks={filteredRisks} />
             </div>
          </div>

          {/* Activity Feed / Last Photo Data Context */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
             {[
               { label: 'Risques Actifs', val: '42', color: 'text-blue-600', bg: 'bg-blue-50' },
               { label: 'Niveau d\'Urgence', val: 'Elevé', color: 'text-orange-600', bg: 'bg-orange-50' },
               { label: 'Recommandations', val: '12', color: 'text-emerald-600', bg: 'bg-emerald-50' },
               { label: 'Temps Réponse', val: '2.4s', color: 'text-purple-600', bg: 'bg-purple-50' }
             ].map((stat, i) => (
               <div key={i} className={`${stat.bg} p-6 rounded-[2rem] border border-white/50 shadow-sm flex flex-col justify-between h-32 transform transition-transform hover:-translate-y-1`}>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{stat.label}</p>
                  <p className={`text-3xl font-black ${stat.color}`}>{stat.val}</p>
               </div>
             ))}
          </div>
          </>
          )}

          {/* Administration View */}
          {activeTab === 'Administration' && user.role === 'admin' && (
            <div className="space-y-8">
              {/* Stats cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                      <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-3xl font-black text-slate-900">{pendingCount}</p>
                      <p className="text-sm text-slate-500 font-medium">En attente</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-3xl font-black text-slate-900">{approvedCount}</p>
                      <p className="text-sm text-slate-500 font-medium">Approuvés</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                      <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-3xl font-black text-slate-900">{rejectedCount}</p>
                      <p className="text-sm text-slate-500 font-medium">Rejetés</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Filtres et recherche */}
              <div className="bg-white rounded-[2rem] p-6 border border-slate-100 shadow-sm">
                <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                  {/* Onglets de filtre */}
                  <div className="flex gap-2">
                    {[
                      { key: 'pending', label: 'En attente', count: pendingCount },
                      { key: 'approved', label: 'Approuvés', count: approvedCount },
                      { key: 'rejected', label: 'Rejetés', count: rejectedCount },
                      { key: 'all', label: 'Tous', count: pendingUsers.length },
                    ].map(tab => (
                      <button
                        key={tab.key}
                        onClick={() => setAdminFilter(tab.key as any)}
                        className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                          adminFilter === tab.key
                            ? 'bg-slate-900 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {tab.label} ({tab.count})
                      </button>
                    ))}
                  </div>
                  
                  {/* Barre de recherche */}
                  <div className="relative">
                    <svg className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input
                      type="text"
                      value={adminSearchQuery}
                      onChange={(e) => setAdminSearchQuery(e.target.value)}
                      placeholder="Rechercher..."
                      className="pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-lime-400 w-64"
                    />
                  </div>
                </div>
              </div>

              {/* Liste des utilisateurs */}
              <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden">
                {filteredPendingUsers.length === 0 ? (
                  <div className="p-12 text-center">
                    <svg className="w-16 h-16 mx-auto text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                    </svg>
                    <p className="text-slate-400 font-medium">Aucune demande trouvée</p>
                    <p className="text-slate-300 text-sm mt-1">Modifiez vos filtres ou votre recherche</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {filteredPendingUsers.map(pendingUser => (
                      <div key={pendingUser.id} className="p-6 hover:bg-slate-50 transition-colors">
                        <div className="flex items-center justify-between gap-4">
                          {/* Info utilisateur */}
                          <div className="flex items-center gap-4 flex-1">
                            <div className="w-12 h-12 bg-gradient-to-br from-slate-700 to-slate-900 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                              {pendingUser.fullName.split(' ').map(n => n[0]).join('')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-bold text-slate-900 truncate">{pendingUser.fullName}</h3>
                              <p className="text-sm text-slate-500 truncate">{pendingUser.email}</p>
                            </div>
                          </div>

                          {/* Détails */}
                          <div className="hidden md:flex items-center gap-6 text-sm">
                            <div className="text-center">
                              <p className="text-slate-400 text-xs uppercase font-bold">Rôle</p>
                              <p className="text-slate-700 font-medium">{pendingUser.role}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-slate-400 text-xs uppercase font-bold">Département</p>
                              <p className="text-slate-700 font-medium">{pendingUser.department || '-'}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-slate-400 text-xs uppercase font-bold">Date</p>
                              <p className="text-slate-700 font-medium whitespace-nowrap">{formatAdminDate(pendingUser.requestDate)}</p>
                            </div>
                          </div>

                          {/* Statut et actions */}
                          <div className="flex items-center gap-3">
                            {pendingUser.status === 'pending' ? (
                              <>
                                <button
                                  onClick={() => setShowConfirmModal({ action: 'approve', user: pendingUser })}
                                  className="px-4 py-2 bg-emerald-500 text-white rounded-xl font-bold text-sm hover:bg-emerald-600 transition-colors flex items-center gap-2"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                                  </svg>
                                  Approuver
                                </button>
                                <button
                                  onClick={() => setShowConfirmModal({ action: 'reject', user: pendingUser })}
                                  className="px-4 py-2 bg-red-100 text-red-600 rounded-xl font-bold text-sm hover:bg-red-200 transition-colors flex items-center gap-2"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                                  </svg>
                                  Rejeter
                                </button>
                              </>
                            ) : (
                              <span className={`px-4 py-2 rounded-xl font-bold text-sm ${
                                pendingUser.status === 'approved' 
                                  ? 'bg-emerald-100 text-emerald-700' 
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {pendingUser.status === 'approved' ? '✓ Approuvé' : '✗ Rejeté'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal de confirmation Admin */}
        {showConfirmModal && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowConfirmModal(null)}>
            <div 
              className="bg-white rounded-3xl shadow-2xl max-w-md w-full mx-4 overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <div className={`p-6 ${showConfirmModal.action === 'approve' ? 'bg-emerald-500' : 'bg-red-500'}`}>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    {showConfirmModal.action === 'approve' ? (
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    ) : (
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    )}
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white">
                      {showConfirmModal.action === 'approve' ? 'Approuver l\'accès' : 'Rejeter la demande'}
                    </h2>
                    <p className="text-white/80 text-sm">{showConfirmModal.user.fullName}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <p className="text-slate-600 mb-6">
                  {showConfirmModal.action === 'approve' 
                    ? `Voulez-vous accorder l'accès à ${showConfirmModal.user.email} ? Cette personne pourra se connecter à la plateforme.`
                    : `Voulez-vous rejeter la demande de ${showConfirmModal.user.email} ? Cette personne ne pourra pas accéder à la plateforme.`
                  }
                </p>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowConfirmModal(null)}
                    className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={() => showConfirmModal.action === 'approve' 
                      ? handleApprove(showConfirmModal.user.id)
                      : handleReject(showConfirmModal.user.id)
                    }
                    className={`flex-1 px-4 py-3 rounded-xl font-bold transition-colors ${
                      showConfirmModal.action === 'approve'
                        ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                        : 'bg-red-500 text-white hover:bg-red-600'
                    }`}
                  >
                    Confirmer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal Détails Risque */}
        {showRiskModal && (
          <RiskDetailModal 
            risk={selectedRiskDetails}
            isLoading={loadingRiskDetails}
            onClose={handleCloseRiskModal}
          />
        )}

        {/* Modal Profil Complet Fournisseur (depuis BDD) */}
        <SupplierProfileModal
          isOpen={supplierProfileModalOpen}
          onClose={handleCloseSupplierProfile}
          profile={supplierProfile}
          loading={loadingSupplierProfile}
          error={supplierProfileError}
        />
      </main>
    </div>
  );
};

export default Dashboard;
