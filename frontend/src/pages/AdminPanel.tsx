/**
 * Panel d'Administration Complet
 * 
 * Fonctionnalités:
 * - Gestion des sources de données (CRUD)
 * - Gestion des catégories de risques
 * - Configuration du scheduler
 * - Statistiques système
 * - Gestion des demandes d'accès utilisateurs
 */

import React, { useState, useEffect } from 'react';

// Types
interface DataSource {
  id: string;
  name: string;
  description: string | null;
  source_type: string;
  risk_type: string | null;
  base_url: string | null;
  api_key_env_var: string | null;
  config: Record<string, any> | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

interface RiskCategory {
  code: string;
  name: string;
  description?: string;
  color: string;
  icon: string;
  is_active: boolean;
}

interface SchedulerConfig {
  frequency: string;
  time: string | null;
  day_of_week: string | null;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
}

interface AdminStats {
  documents: { total: number };
  analyses: { total: number };
  entities: { sites: number; suppliers: number };
  sources: { total: number; active: number; inactive: number };
  scheduler: SchedulerConfig;
}

interface PendingUser {
  id: string;
  fullName: string;
  email: string;
  role: string;
  department?: string;
  requestDate: Date;
  status: 'pending' | 'approved' | 'rejected';
}

interface AdminPanelProps {
  onBack: () => void;
}

// Données mock des utilisateurs en attente
const MOCK_PENDING_USERS: PendingUser[] = [
  { id: '1', fullName: 'Marie Dupont', email: 'marie.dupont@hutchinson.com', role: 'Analyste', department: 'Supply Chain', requestDate: new Date('2026-02-03T14:30:00'), status: 'pending' },
  { id: '2', fullName: 'Pierre Martin', email: 'pierre.martin@hutchinson.com', role: 'Manager', department: 'Achats', requestDate: new Date('2026-02-02T09:15:00'), status: 'pending' },
  { id: '3', fullName: 'Sophie Bernard', email: 'sophie.bernard@hutchinson.com', role: 'Analyste', department: 'Qualité', requestDate: new Date('2026-02-01T16:45:00'), status: 'pending' },
  { id: '4', fullName: 'Lucas Petit', email: 'lucas.petit@hutchinson.com', role: 'Viewer', department: 'Production', requestDate: new Date('2026-01-31T11:20:00'), status: 'pending' },
  { id: '5', fullName: 'Emma Leroy', email: 'emma.leroy@hutchinson.com', role: 'Analyste', department: 'R&D', requestDate: new Date('2026-01-30T08:00:00'), status: 'approved' },
  { id: '6', fullName: 'Thomas Moreau', email: 'thomas.moreau@external.com', role: 'Viewer', department: 'Externe', requestDate: new Date('2026-01-29T15:30:00'), status: 'rejected' },
];

const API_BASE = 'http://localhost:8000/api/admin';

const AdminPanel: React.FC<AdminPanelProps> = ({ onBack }) => {
  // Onglet actif
  const [activeTab, setActiveTab] = useState<'sources' | 'categories' | 'scheduler' | 'stats' | 'users'>('sources');
  
  // États Sources
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loadingSources, setLoadingSources] = useState(false);
  const [showSourceModal, setShowSourceModal] = useState<'create' | 'edit' | null>(null);
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [sourceForm, setSourceForm] = useState({
    name: '',
    description: '',
    source_type: 'api',
    risk_type: 'regulatory',
    base_url: '',
    api_key_env_var: '',
    is_active: true,
    priority: 5
  });

  // États Catégories
  const [categories, setCategories] = useState<RiskCategory[]>([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    code: '',
    description: '',
    color: '#3B82F6',
    icon: '⚠️',
    is_active: true
  });

  // États Scheduler
  const [schedulerConfig, setSchedulerConfig] = useState<SchedulerConfig | null>(null);
  const [schedulerForm, setSchedulerForm] = useState({
    frequency: 'daily',
    time: '06:00',
    day_of_week: 'monday',
    enabled: true
  });
  const [runningAnalysis, setRunningAnalysis] = useState(false);

  // États Stats
  const [stats, setStats] = useState<AdminStats | null>(null);

  // États Utilisateurs
  const [users, setUsers] = useState<PendingUser[]>(MOCK_PENDING_USERS);
  const [userFilter, setUserFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [userSearch, setUserSearch] = useState('');
  const [showUserConfirmModal, setShowUserConfirmModal] = useState<{ action: 'approve' | 'reject'; user: PendingUser } | null>(null);

  // Chargement des données
  useEffect(() => {
    if (activeTab === 'sources') loadSources();
    if (activeTab === 'categories') loadCategories();
    if (activeTab === 'scheduler') loadScheduler();
    if (activeTab === 'stats') loadStats();
  }, [activeTab]);

  // API Calls
  const loadSources = async () => {
    setLoadingSources(true);
    try {
      const res = await fetch(`${API_BASE}/sources`);
      if (res.ok) {
        const data = await res.json();
        setSources(data);
      }
    } catch (err) {
      console.error('Erreur chargement sources:', err);
    } finally {
      setLoadingSources(false);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/risk-categories`);
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (err) {
      console.error('Erreur chargement catégories:', err);
    }
  };

  const loadScheduler = async () => {
    try {
      const res = await fetch(`${API_BASE}/scheduler/config`);
      if (res.ok) {
        const data = await res.json();
        setSchedulerConfig(data);
        setSchedulerForm({
          frequency: data.frequency || 'daily',
          time: data.time || '06:00',
          day_of_week: data.day_of_week || 'monday',
          enabled: data.enabled ?? true
        });
      }
    } catch (err) {
      console.error('Erreur chargement scheduler:', err);
    }
  };

  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Erreur chargement stats:', err);
    }
  };

  // Sources CRUD
  const handleCreateSource = async () => {
    try {
      const res = await fetch(`${API_BASE}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sourceForm)
      });
      if (res.ok) {
        setShowSourceModal(null);
        setSourceForm({ name: '', description: '', source_type: 'api', risk_type: 'regulatory', base_url: '', api_key_env_var: '', is_active: true, priority: 5 });
        loadSources();
        alert('✅ Source créée avec succès !');
      } else {
        const error = await res.json();
        alert(`❌ Erreur: ${error.detail || 'Impossible de créer la source'}`);
      }
    } catch (err) {
      console.error('Erreur création source:', err);
      alert('❌ Erreur réseau lors de la création de la source');
    }
  };

  const handleUpdateSource = async () => {
    if (!editingSource) return;
    try {
      const res = await fetch(`${API_BASE}/sources/${editingSource.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sourceForm)
      });
      if (res.ok) {
        setShowSourceModal(null);
        setEditingSource(null);
        loadSources();
      }
    } catch (err) {
      console.error('Erreur mise à jour source:', err);
    }
  };

  const handleDeleteSource = async (id: string) => {
    if (!confirm('Supprimer cette source ?')) return;
    try {
      const res = await fetch(`${API_BASE}/sources/${id}`, { method: 'DELETE' });
      if (res.ok) {
        loadSources();
        alert('✅ Source supprimée avec succès !');
      } else {
        const error = await res.json();
        alert(`❌ Erreur: ${error.detail || 'Impossible de supprimer la source'}`);
      }
    } catch (err) {
      console.error('Erreur suppression source:', err);
      alert('❌ Erreur réseau lors de la suppression');
    }
  };

  const handleToggleSource = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/sources/${id}/toggle`, { method: 'POST' });
      if (res.ok) loadSources();
    } catch (err) {
      console.error('Erreur toggle source:', err);
    }
  };

  // Catégories
  const handleCreateCategory = async () => {
    try {
      const res = await fetch(`${API_BASE}/risk-categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(categoryForm)
      });
      if (res.ok) {
        setShowCategoryModal(false);
        setCategoryForm({ name: '', code: '', description: '', color: '#3B82F6', icon: '⚠️', is_active: true });
        loadCategories();
        alert('✅ Catégorie créée avec succès !');
      } else {
        const error = await res.json();
        alert(`❌ Erreur: ${error.detail || 'Impossible de créer la catégorie'}`);
      }
    } catch (err) {
      console.error('Erreur création catégorie:', err);
      alert('❌ Erreur réseau lors de la création de la catégorie');
    }
  };

  const handleToggleCategory = async (code: string) => {
    try {
      const res = await fetch(`${API_BASE}/risk-categories/${code}/toggle`, { method: 'POST' });
      if (res.ok) loadCategories();
    } catch (err) {
      console.error('Erreur toggle catégorie:', err);
    }
  };

  // Scheduler
  const handleUpdateScheduler = async () => {
    try {
      const res = await fetch(`${API_BASE}/scheduler/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schedulerForm)
      });
      if (res.ok) {
        loadScheduler();
        alert('Configuration mise à jour !');
      }
    } catch (err) {
      console.error('Erreur mise à jour scheduler:', err);
    }
  };

  const handleRunNow = async () => {
    setRunningAnalysis(true);
    try {
      const res = await fetch(`${API_BASE}/scheduler/run-now`, { method: 'POST' });
      if (res.ok) {
        alert('Analyse lancée !');
        loadScheduler();
      }
    } catch (err) {
      console.error('Erreur lancement analyse:', err);
    } finally {
      setRunningAnalysis(false);
    }
  };

  // Utilisateurs
  const handleApproveUser = (userId: string) => {
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, status: 'approved' as const } : u));
    setShowUserConfirmModal(null);
  };

  const handleRejectUser = (userId: string) => {
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, status: 'rejected' as const } : u));
    setShowUserConfirmModal(null);
  };

  const filteredUsers = users.filter(u => {
    const matchesFilter = userFilter === 'all' || u.status === userFilter;
    const matchesSearch = u.fullName.toLowerCase().includes(userSearch.toLowerCase()) ||
                         u.email.toLowerCase().includes(userSearch.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const pendingCount = users.filter(u => u.status === 'pending').length;
  const approvedCount = users.filter(u => u.status === 'approved').length;
  const rejectedCount = users.filter(u => u.status === 'rejected').length;

  const formatDate = (date: Date) => date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

  const tabs = [
    { key: 'sources', label: 'Sources de données', icon: '🔗', count: sources.length },
    { key: 'categories', label: 'Catégories de risques', icon: '📊', count: categories.length },
    { key: 'scheduler', label: 'Planification', icon: '⏰' },
    { key: 'stats', label: 'Statistiques', icon: '📈' },
    { key: 'users', label: 'Utilisateurs', icon: '👥', count: pendingCount > 0 ? pendingCount : undefined },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
              >
                <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-black text-slate-900">Administration</h1>
                <p className="text-slate-500 text-sm">Gérez les sources, catégories, planification et utilisateurs</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-bold">
                Admin
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-bold text-sm whitespace-nowrap transition-colors ${
                  activeTab === tab.key
                    ? 'border-lime-500 text-lime-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                {tab.count !== undefined && (
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    activeTab === tab.key ? 'bg-lime-100 text-lime-700' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        
        {/* ========== SOURCES DE DONNÉES ========== */}
        {activeTab === 'sources' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-900">Sources de données</h2>
              <button
                onClick={() => {
                  setSourceForm({ name: '', description: '', source_type: 'api', risk_type: 'regulatory', base_url: '', api_key_env_var: '', is_active: true, priority: 5 });
                  setShowSourceModal('create');
                }}
                className="px-4 py-2 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                </svg>
                Ajouter une source
              </button>
            </div>

            {loadingSources ? (
              <div className="text-center py-12 text-slate-500">Chargement...</div>
            ) : sources.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <div className="text-6xl mb-4">🔗</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Aucune source configurée</h3>
                <p className="text-slate-500 mb-6">Ajoutez des sources de données pour alimenter la veille</p>
                <button
                  onClick={() => setShowSourceModal('create')}
                  className="px-6 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
                >
                  Ajouter la première source
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {sources.map(source => (
                  <div key={source.id} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-slate-900">{source.name}</h3>
                          <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                            source.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {source.is_active ? '● Actif' : '○ Inactif'}
                          </span>
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-bold">
                            {source.source_type}
                          </span>
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-bold">
                            {source.risk_type}
                          </span>
                        </div>
                        <p className="text-slate-500 text-sm mb-2">{source.description || 'Pas de description'}</p>
                        {source.base_url && (
                          <p className="text-slate-400 text-xs font-mono truncate">{source.base_url}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleSource(source.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            source.is_active ? 'hover:bg-amber-100 text-amber-600' : 'hover:bg-emerald-100 text-emerald-600'
                          }`}
                          title={source.is_active ? 'Désactiver' : 'Activer'}
                        >
                          {source.is_active ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setEditingSource(source);
                            setSourceForm({
                              name: source.name,
                              description: source.description || '',
                              source_type: source.source_type,
                              risk_type: source.risk_type || 'regulatory',
                              base_url: source.base_url || '',
                              api_key_env_var: source.api_key_env_var || '',
                              is_active: source.is_active,
                              priority: source.priority
                            });
                            setShowSourceModal('edit');
                          }}
                          className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors"
                          title="Modifier"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteSource(source.id)}
                          className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
                          title="Supprimer"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========== CATÉGORIES DE RISQUES ========== */}
        {activeTab === 'categories' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-900">Catégories de risques</h2>
              <button
                onClick={() => setShowCategoryModal(true)}
                className="px-4 py-2 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                </svg>
                Ajouter une catégorie
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map(cat => (
                <div 
                  key={cat.code} 
                  className={`bg-white rounded-2xl border-2 p-6 transition-all ${
                    cat.is_active ? 'border-slate-200 hover:shadow-lg' : 'border-dashed border-slate-300 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                        style={{ backgroundColor: cat.color + '20' }}
                      >
                        {cat.icon}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900">{cat.name}</h3>
                        <p className="text-xs text-slate-400 font-mono">{cat.code}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleToggleCategory(cat.code)}
                      className={`p-2 rounded-lg transition-colors ${
                        cat.is_active ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'
                      }`}
                    >
                      {cat.is_active ? '✓' : '○'}
                    </button>
                  </div>
                  {cat.description && (
                    <p className="text-sm text-slate-500">{cat.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========== SCHEDULER ========== */}
        {activeTab === 'scheduler' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-900">Configuration de la planification</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Config Form */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6">
                <h3 className="font-bold text-slate-900 mb-4">Paramètres du scheduler</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Fréquence</label>
                    <select
                      value={schedulerForm.frequency}
                      onChange={(e) => setSchedulerForm(prev => ({ ...prev, frequency: e.target.value }))}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400"
                    >
                      <option value="hourly">Toutes les heures</option>
                      <option value="daily">Quotidien</option>
                      <option value="weekly">Hebdomadaire</option>
                      <option value="manual">Manuel uniquement</option>
                    </select>
                  </div>

                  {schedulerForm.frequency !== 'manual' && (
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-2">Heure d'exécution</label>
                      <input
                        type="time"
                        value={schedulerForm.time}
                        onChange={(e) => setSchedulerForm(prev => ({ ...prev, time: e.target.value }))}
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400"
                      />
                    </div>
                  )}

                  {schedulerForm.frequency === 'weekly' && (
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-2">Jour de la semaine</label>
                      <select
                        value={schedulerForm.day_of_week}
                        onChange={(e) => setSchedulerForm(prev => ({ ...prev, day_of_week: e.target.value }))}
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400"
                      >
                        <option value="monday">Lundi</option>
                        <option value="tuesday">Mardi</option>
                        <option value="wednesday">Mercredi</option>
                        <option value="thursday">Jeudi</option>
                        <option value="friday">Vendredi</option>
                        <option value="saturday">Samedi</option>
                        <option value="sunday">Dimanche</option>
                      </select>
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="enabled"
                      checked={schedulerForm.enabled}
                      onChange={(e) => setSchedulerForm(prev => ({ ...prev, enabled: e.target.checked }))}
                      className="w-5 h-5 rounded border-slate-300 text-lime-500 focus:ring-lime-400"
                    />
                    <label htmlFor="enabled" className="text-sm font-bold text-slate-700">
                      Scheduler activé
                    </label>
                  </div>

                  <button
                    onClick={handleUpdateScheduler}
                    className="w-full px-4 py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition-colors"
                  >
                    Sauvegarder la configuration
                  </button>
                </div>
              </div>

              {/* Actions */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6">
                <h3 className="font-bold text-slate-900 mb-4">Exécution manuelle</h3>
                
                <div className="bg-gradient-to-br from-lime-50 to-emerald-50 rounded-xl p-6 mb-4">
                  <div className="text-4xl mb-2">🚀</div>
                  <h4 className="font-bold text-slate-900 mb-2">Lancer une analyse maintenant</h4>
                  <p className="text-sm text-slate-600 mb-4">
                    Déclenche immédiatement le pipeline complet : collecte, analyse, scoring et notifications.
                  </p>
                  <button
                    onClick={handleRunNow}
                    disabled={runningAnalysis}
                    className={`w-full px-4 py-3 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 ${
                      runningAnalysis 
                        ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                        : 'bg-lime-500 text-white hover:bg-lime-600'
                    }`}
                  >
                    {runningAnalysis ? (
                      <>
                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                        </svg>
                        Analyse en cours...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                        Lancer l'analyse
                      </>
                    )}
                  </button>
                </div>

                {schedulerConfig && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Dernière exécution</span>
                      <span className="font-medium text-slate-900">
                        {schedulerConfig.last_run || 'Jamais'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Prochaine exécution</span>
                      <span className="font-medium text-slate-900">
                        {schedulerConfig.next_run || 'Non planifiée'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========== STATISTIQUES ========== */}
        {activeTab === 'stats' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-900">Statistiques système</h2>

            {stats ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="text-3xl mb-2">📄</div>
                  <p className="text-slate-500 text-sm">Documents collectés</p>
                  <p className="text-3xl font-black text-slate-900">{stats.documents.total}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="text-3xl mb-2">🔍</div>
                  <p className="text-slate-500 text-sm">Analyses effectuées</p>
                  <p className="text-3xl font-black text-slate-900">{stats.analyses.total}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="text-3xl mb-2">🏭</div>
                  <p className="text-slate-500 text-sm">Sites industriels</p>
                  <p className="text-3xl font-black text-slate-900">{stats.entities.sites}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="text-3xl mb-2">🚚</div>
                  <p className="text-slate-500 text-sm">Fournisseurs</p>
                  <p className="text-3xl font-black text-slate-900">{stats.entities.suppliers}</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">Chargement des statistiques...</div>
            )}

            {stats && (
              <div className="bg-white rounded-2xl border border-slate-200 p-6">
                <h3 className="font-bold text-slate-900 mb-4">Sources de données</h3>
                <div className="flex gap-4">
                  <div className="flex-1 bg-emerald-50 rounded-xl p-4 text-center">
                    <p className="text-2xl font-black text-emerald-600">{stats.sources.active}</p>
                    <p className="text-sm text-emerald-700">Actives</p>
                  </div>
                  <div className="flex-1 bg-slate-50 rounded-xl p-4 text-center">
                    <p className="text-2xl font-black text-slate-600">{stats.sources.inactive}</p>
                    <p className="text-sm text-slate-500">Inactives</p>
                  </div>
                  <div className="flex-1 bg-blue-50 rounded-xl p-4 text-center">
                    <p className="text-2xl font-black text-blue-600">{stats.sources.total}</p>
                    <p className="text-sm text-blue-700">Total</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========== UTILISATEURS ========== */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div>
                  <p className="text-3xl font-black text-slate-900">{pendingCount}</p>
                  <p className="text-slate-500 text-sm">En attente</p>
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <div>
                  <p className="text-3xl font-black text-slate-900">{approvedCount}</p>
                  <p className="text-slate-500 text-sm">Approuvés</p>
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
                <div>
                  <p className="text-3xl font-black text-slate-900">{rejectedCount}</p>
                  <p className="text-slate-500 text-sm">Rejetés</p>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="flex gap-2">
                  {[
                    { key: 'pending', label: 'En attente', count: pendingCount },
                    { key: 'approved', label: 'Approuvés', count: approvedCount },
                    { key: 'rejected', label: 'Rejetés', count: rejectedCount },
                    { key: 'all', label: 'Tous', count: users.length },
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setUserFilter(tab.key as any)}
                      className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                        userFilter === tab.key
                          ? 'bg-slate-900 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {tab.label} ({tab.count})
                    </button>
                  ))}
                </div>
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Rechercher..."
                  className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-lime-400 w-64"
                />
              </div>
            </div>

            {/* Users List */}
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
              {filteredUsers.length === 0 ? (
                <div className="p-12 text-center text-slate-400">Aucun utilisateur trouvé</div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredUsers.map(user => (
                    <div key={user.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-12 h-12 bg-gradient-to-br from-slate-700 to-slate-900 rounded-xl flex items-center justify-center text-white font-bold">
                            {user.fullName.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-900">{user.fullName}</h3>
                            <p className="text-sm text-slate-500">{user.email}</p>
                          </div>
                        </div>
                        <div className="hidden md:flex items-center gap-6 text-sm">
                          <div className="text-center">
                            <p className="text-slate-400 text-xs font-bold">RÔLE</p>
                            <p className="text-slate-700">{user.role}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-slate-400 text-xs font-bold">DÉPARTEMENT</p>
                            <p className="text-slate-700">{user.department || '-'}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-slate-400 text-xs font-bold">DATE</p>
                            <p className="text-slate-700">{formatDate(user.requestDate)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {user.status === 'pending' ? (
                            <>
                              <button
                                onClick={() => setShowUserConfirmModal({ action: 'approve', user })}
                                className="px-4 py-2 bg-emerald-500 text-white rounded-xl font-bold text-sm hover:bg-emerald-600"
                              >
                                ✓ Approuver
                              </button>
                              <button
                                onClick={() => setShowUserConfirmModal({ action: 'reject', user })}
                                className="px-4 py-2 bg-red-100 text-red-600 rounded-xl font-bold text-sm hover:bg-red-200"
                              >
                                ✗ Rejeter
                              </button>
                            </>
                          ) : (
                            <span className={`px-4 py-2 rounded-xl font-bold text-sm ${
                              user.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {user.status === 'approved' ? '✓ Approuvé' : '✗ Rejeté'}
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

      {/* ========== MODALS ========== */}
      
      {/* Modal Source */}
      {showSourceModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => { setShowSourceModal(null); setEditingSource(null); }}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-black text-slate-900">
                {showSourceModal === 'create' ? 'Nouvelle source' : 'Modifier la source'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Nom *</label>
                <input
                  type="text"
                  value={sourceForm.name}
                  onChange={(e) => setSourceForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900 placeholder:text-slate-400"
                  placeholder="EUR-Lex, OpenWeatherMap..."
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Description</label>
                <textarea
                  value={sourceForm.description}
                  onChange={(e) => setSourceForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900 placeholder:text-slate-400"
                  rows={2}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Type *</label>
                  <select
                    value={sourceForm.source_type}
                    onChange={(e) => setSourceForm(prev => ({ ...prev, source_type: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  >
                    <option value="api">API</option>
                    <option value="scraper">Scraper</option>
                    <option value="file">Fichier</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Catégorie risque *</label>
                  <select
                    value={sourceForm.risk_type}
                    onChange={(e) => setSourceForm(prev => ({ ...prev, risk_type: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  >
                    <option value="regulatory">Réglementaire</option>
                    <option value="climate">Climatique</option>
                    <option value="geopolitical">Géopolitique</option>
                    <option value="sanitary">Sanitaire</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">URL de base</label>
                <input
                  type="text"
                  value={sourceForm.base_url}
                  onChange={(e) => setSourceForm(prev => ({ ...prev, base_url: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900 placeholder:text-slate-400"
                  placeholder="https://api.example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Variable env. API Key</label>
                <input
                  type="text"
                  value={sourceForm.api_key_env_var}
                  onChange={(e) => setSourceForm(prev => ({ ...prev, api_key_env_var: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900 placeholder:text-slate-400"
                  placeholder="EURLEX_API_KEY"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Priorité (0-10)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={sourceForm.priority}
                    onChange={(e) => setSourceForm(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sourceForm.is_active}
                      onChange={(e) => setSourceForm(prev => ({ ...prev, is_active: e.target.checked }))}
                      className="w-5 h-5 rounded border-slate-300 text-lime-500"
                    />
                    <span className="font-bold text-slate-700">Source active</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex gap-3">
              <button
                onClick={() => { setShowSourceModal(null); setEditingSource(null); }}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200"
              >
                Annuler
              </button>
              <button
                onClick={showSourceModal === 'create' ? handleCreateSource : handleUpdateSource}
                className="flex-1 px-4 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
              >
                {showSourceModal === 'create' ? 'Créer' : 'Sauvegarder'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Catégorie */}
      {showCategoryModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowCategoryModal(false)}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-black text-slate-900">Nouvelle catégorie de risque</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Nom *</label>
                <input
                  type="text"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder:text-slate-400"
                  placeholder="Sanitaire, Cyber..."
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Code *</label>
                <input
                  type="text"
                  value={categoryForm.code}
                  onChange={(e) => setCategoryForm(prev => ({ ...prev, code: e.target.value.toLowerCase() }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-mono text-slate-900 placeholder:text-slate-400"
                  placeholder="sanitary, cyber..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Couleur</label>
                  <input
                    type="color"
                    value={categoryForm.color}
                    onChange={(e) => setCategoryForm(prev => ({ ...prev, color: e.target.value }))}
                    className="w-full h-12 rounded-xl cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Icône</label>
                  <input
                    type="text"
                    value={categoryForm.icon}
                    onChange={(e) => setCategoryForm(prev => ({ ...prev, icon: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-center text-2xl text-slate-900"
                  />
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex gap-3">
              <button
                onClick={() => setShowCategoryModal(false)}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold"
              >
                Annuler
              </button>
              <button
                onClick={handleCreateCategory}
                className="flex-1 px-4 py-3 bg-lime-500 text-white rounded-xl font-bold"
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Confirmation Utilisateur */}
      {showUserConfirmModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowUserConfirmModal(null)}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className={`p-6 ${showUserConfirmModal.action === 'approve' ? 'bg-emerald-500' : 'bg-red-500'}`}>
              <h2 className="text-xl font-black text-white">
                {showUserConfirmModal.action === 'approve' ? 'Approuver l\'accès' : 'Rejeter la demande'}
              </h2>
              <p className="text-white/80">{showUserConfirmModal.user.fullName}</p>
            </div>
            <div className="p-6">
              <p className="text-slate-600 mb-6">
                {showUserConfirmModal.action === 'approve' 
                  ? `Voulez-vous accorder l'accès à ${showUserConfirmModal.user.email} ?`
                  : `Voulez-vous rejeter la demande de ${showUserConfirmModal.user.email} ?`
                }
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowUserConfirmModal(null)}
                  className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold"
                >
                  Annuler
                </button>
                <button
                  onClick={() => showUserConfirmModal.action === 'approve' 
                    ? handleApproveUser(showUserConfirmModal.user.id)
                    : handleRejectUser(showUserConfirmModal.user.id)
                  }
                  className={`flex-1 px-4 py-3 rounded-xl font-bold text-white ${
                    showUserConfirmModal.action === 'approve' ? 'bg-emerald-500' : 'bg-red-500'
                  }`}
                >
                  Confirmer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
