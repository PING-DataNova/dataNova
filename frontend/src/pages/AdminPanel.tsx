/**
 * Panel d'Administration Complet
 * 
 * Fonctionnalités:
 * - Gestion des sources de données (CRUD)
 * - Gestion des fournisseurs (CRUD)
 * - Gestion des sites Hutchinson (CRUD)
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

interface Supplier {
  id: string;
  name: string;
  code: string;
  country: string;
  region: string | null;
  city: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  sector: string;
  products_supplied: string[];
  company_size: string | null;
  certifications: string[] | null;
  financial_health: string | null;
  criticality_score: number | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

interface HutchinsonSite {
  id: string;
  name: string;
  code: string;
  country: string;
  region: string | null;
  city: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  sectors: string[] | null;
  products: string[] | null;
  raw_materials: string[] | null;
  certifications: string[] | null;
  employee_count: number | null;
  annual_production_value: number | null;
  strategic_importance: string | null;
  daily_revenue: number | null;
  active: boolean;
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
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  department?: string;
  active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
  // Computed status based on active and last_login
  status?: 'pending' | 'approved' | 'rejected';
}

interface AdminPanelProps {
  onBack: () => void;
}



const API_BASE = 'http://localhost:8000/api/admin';

const AdminPanel: React.FC<AdminPanelProps> = ({ onBack }) => {
  // Onglet actif
  const [activeTab, setActiveTab] = useState<'sources' | 'suppliers' | 'sites' | 'categories' | 'scheduler' | 'stats' | 'users'>('sources');
  
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

  // États Fournisseurs
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loadingSuppliers, setLoadingSuppliers] = useState(false);
  const [showSupplierModal, setShowSupplierModal] = useState<'create' | 'edit' | null>(null);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [supplierForm, setSupplierForm] = useState({
    name: '',
    code: '',
    country: '',
    region: '',
    city: '',
    address: '',
    latitude: '',
    longitude: '',
    sector: '',
    products_supplied: '',
    company_size: 'PME',
    certifications: '',
    financial_health: 'bon',
    criticality_score: 5,
    active: true
  });

  // États Sites Hutchinson
  const [sites, setSites] = useState<HutchinsonSite[]>([]);
  const [loadingSites, setLoadingSites] = useState(false);
  const [showSiteModal, setShowSiteModal] = useState<'create' | 'edit' | null>(null);
  const [editingSite, setEditingSite] = useState<HutchinsonSite | null>(null);
  const [siteForm, setSiteForm] = useState({
    name: '',
    code: '',
    country: '',
    region: '',
    city: '',
    address: '',
    latitude: '',
    longitude: '',
    sectors: '',
    products: '',
    raw_materials: '',
    certifications: '',
    employee_count: '',
    annual_production_value: '',
    strategic_importance: 'moyen',
    daily_revenue: '',
    active: true
  });

  // États Catégories
  const [categories, setCategories] = useState<RiskCategory[]>([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    code: '',
    description: '',
    color: '#3B82F6',
    icon: '',
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
  const [users, setUsers] = useState<PendingUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userFilter, setUserFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
  const [userSearch, setUserSearch] = useState('');
  const [showUserConfirmModal, setShowUserConfirmModal] = useState<{ action: 'approve' | 'reject'; user: PendingUser } | null>(null);

  // Chargement des données
  useEffect(() => {
    if (activeTab === 'sources') loadSources();
    if (activeTab === 'suppliers') loadSuppliers();
    if (activeTab === 'sites') loadSites();
    if (activeTab === 'categories') loadCategories();
    if (activeTab === 'scheduler') loadScheduler();
    if (activeTab === 'stats') loadStats();
    if (activeTab === 'users') loadUsers();
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

  const loadSuppliers = async () => {
    setLoadingSuppliers(true);
    try {
      const res = await fetch(`${API_BASE}/suppliers`);
      if (res.ok) {
        const data = await res.json();
        setSuppliers(data);
      }
    } catch (err) {
      console.error('Erreur chargement fournisseurs:', err);
    } finally {
      setLoadingSuppliers(false);
    }
  };

  const loadSites = async () => {
    setLoadingSites(true);
    try {
      const res = await fetch(`${API_BASE}/sites`);
      if (res.ok) {
        const data = await res.json();
        setSites(data);
      }
    } catch (err) {
      console.error('Erreur chargement sites:', err);
    } finally {
      setLoadingSites(false);
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

  const loadUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await fetch(`${API_BASE}/users`);
      if (res.ok) {
        const data = await res.json();
        // Compute status from active and last_login
        const usersWithStatus = data.map((user: PendingUser) => ({
          ...user,
          status: !user.active ? 'rejected' : (user.last_login ? 'approved' : 'pending')
        }));
        setUsers(usersWithStatus);
      }
    } catch (err) {
      console.error('Erreur chargement utilisateurs:', err);
    } finally {
      setLoadingUsers(false);
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
        alert('Source créée avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de créer la source'}`);
      }
    } catch (err) {
      console.error('Erreur création source:', err);
      alert('Erreur réseau lors de la création de la source');
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
        alert('Source supprimée avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de supprimer la source'}`);
      }
    } catch (err) {
      console.error('Erreur suppression source:', err);
      alert('Erreur réseau lors de la suppression');
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

  // Fournisseurs CRUD
  const resetSupplierForm = () => {
    setSupplierForm({
      name: '', code: '', country: '', region: '', city: '', address: '',
      latitude: '', longitude: '', sector: '', products_supplied: '',
      company_size: 'PME', certifications: '', financial_health: 'bon',
      criticality_score: 5, active: true
    });
  };

  const handleCreateSupplier = async () => {
    try {
      const payload = {
        ...supplierForm,
        latitude: supplierForm.latitude ? parseFloat(supplierForm.latitude) : null,
        longitude: supplierForm.longitude ? parseFloat(supplierForm.longitude) : null,
        products_supplied: supplierForm.products_supplied.split(',').map(p => p.trim()).filter(p => p),
        certifications: supplierForm.certifications ? supplierForm.certifications.split(',').map(c => c.trim()).filter(c => c) : null,
      };
      const res = await fetch(`${API_BASE}/suppliers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowSupplierModal(null);
        resetSupplierForm();
        loadSuppliers();
        alert('Fournisseur créé avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de créer le fournisseur'}`);
      }
    } catch (err) {
      console.error('Erreur création fournisseur:', err);
      alert('Erreur réseau lors de la création du fournisseur');
    }
  };

  const handleUpdateSupplier = async () => {
    if (!editingSupplier) return;
    try {
      const payload = {
        ...supplierForm,
        latitude: supplierForm.latitude ? parseFloat(supplierForm.latitude) : null,
        longitude: supplierForm.longitude ? parseFloat(supplierForm.longitude) : null,
        products_supplied: supplierForm.products_supplied.split(',').map(p => p.trim()).filter(p => p),
        certifications: supplierForm.certifications ? supplierForm.certifications.split(',').map(c => c.trim()).filter(c => c) : null,
      };
      const res = await fetch(`${API_BASE}/suppliers/${editingSupplier.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowSupplierModal(null);
        setEditingSupplier(null);
        resetSupplierForm();
        loadSuppliers();
        alert('Fournisseur mis à jour !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de modifier le fournisseur'}`);
      }
    } catch (err) {
      console.error('Erreur mise à jour fournisseur:', err);
    }
  };

  const handleDeleteSupplier = async (id: string) => {
    if (!confirm('Supprimer ce fournisseur ?')) return;
    try {
      const res = await fetch(`${API_BASE}/suppliers/${id}`, { method: 'DELETE' });
      if (res.ok) {
        loadSuppliers();
        alert('Fournisseur supprimé !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de supprimer le fournisseur'}`);
      }
    } catch (err) {
      console.error('Erreur suppression fournisseur:', err);
    }
  };

  const handleToggleSupplier = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/suppliers/${id}/toggle`, { method: 'POST' });
      if (res.ok) loadSuppliers();
    } catch (err) {
      console.error('Erreur toggle fournisseur:', err);
    }
  };

  // Sites CRUD
  const resetSiteForm = () => {
    setSiteForm({
      name: '', code: '', country: '', region: '', city: '', address: '',
      latitude: '', longitude: '', sectors: '', products: '', raw_materials: '',
      certifications: '', employee_count: '', annual_production_value: '',
      strategic_importance: 'moyen', daily_revenue: '', active: true
    });
  };

  const handleCreateSite = async () => {
    try {
      const payload = {
        ...siteForm,
        latitude: siteForm.latitude ? parseFloat(siteForm.latitude) : null,
        longitude: siteForm.longitude ? parseFloat(siteForm.longitude) : null,
        employee_count: siteForm.employee_count ? parseInt(siteForm.employee_count) : null,
        annual_production_value: siteForm.annual_production_value ? parseFloat(siteForm.annual_production_value) : null,
        daily_revenue: siteForm.daily_revenue ? parseFloat(siteForm.daily_revenue) : null,
        sectors: siteForm.sectors ? siteForm.sectors.split(',').map(s => s.trim()).filter(s => s) : null,
        products: siteForm.products ? siteForm.products.split(',').map(p => p.trim()).filter(p => p) : null,
        raw_materials: siteForm.raw_materials ? siteForm.raw_materials.split(',').map(r => r.trim()).filter(r => r) : null,
        certifications: siteForm.certifications ? siteForm.certifications.split(',').map(c => c.trim()).filter(c => c) : null,
      };
      const res = await fetch(`${API_BASE}/sites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowSiteModal(null);
        resetSiteForm();
        loadSites();
        alert('Site créé avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de créer le site'}`);
      }
    } catch (err) {
      console.error('Erreur création site:', err);
      alert('Erreur réseau lors de la création du site');
    }
  };

  const handleUpdateSite = async () => {
    if (!editingSite) return;
    try {
      const payload = {
        ...siteForm,
        latitude: siteForm.latitude ? parseFloat(siteForm.latitude) : null,
        longitude: siteForm.longitude ? parseFloat(siteForm.longitude) : null,
        employee_count: siteForm.employee_count ? parseInt(siteForm.employee_count) : null,
        annual_production_value: siteForm.annual_production_value ? parseFloat(siteForm.annual_production_value) : null,
        daily_revenue: siteForm.daily_revenue ? parseFloat(siteForm.daily_revenue) : null,
        sectors: siteForm.sectors ? siteForm.sectors.split(',').map(s => s.trim()).filter(s => s) : null,
        products: siteForm.products ? siteForm.products.split(',').map(p => p.trim()).filter(p => p) : null,
        raw_materials: siteForm.raw_materials ? siteForm.raw_materials.split(',').map(r => r.trim()).filter(r => r) : null,
        certifications: siteForm.certifications ? siteForm.certifications.split(',').map(c => c.trim()).filter(c => c) : null,
      };
      const res = await fetch(`${API_BASE}/sites/${editingSite.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowSiteModal(null);
        setEditingSite(null);
        resetSiteForm();
        loadSites();
        alert('Site mis à jour !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de modifier le site'}`);
      }
    } catch (err) {
      console.error('Erreur mise à jour site:', err);
    }
  };

  const handleDeleteSite = async (id: string) => {
    if (!confirm('Supprimer ce site ?')) return;
    try {
      const res = await fetch(`${API_BASE}/sites/${id}`, { method: 'DELETE' });
      if (res.ok) {
        loadSites();
        alert('Site supprimé !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de supprimer le site'}`);
      }
    } catch (err) {
      console.error('Erreur suppression site:', err);
    }
  };

  const handleToggleSite = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/sites/${id}/toggle`, { method: 'POST' });
      if (res.ok) loadSites();
    } catch (err) {
      console.error('Erreur toggle site:', err);
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
        setCategoryForm({ name: '', code: '', description: '', color: '#3B82F6', icon: '', is_active: true });
        loadCategories();
        alert('Catégorie créée avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de créer la catégorie'}`);
      }
    } catch (err) {
      console.error('Erreur création catégorie:', err);
      alert('Erreur réseau lors de la création de la catégorie');
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
      const data = await res.json();
      if (res.ok) {
        alert(`Analyse terminee !\n\nDocuments collectes: ${data.result?.documents_collected || 0}\nAnalyses de risques: ${data.result?.risk_analyses || 0}\nNotifications: ${data.result?.notifications_sent || 0}`);
        loadScheduler();
      } else {
        alert(`Erreur: ${data.detail || 'Echec de l\'analyse'}`);
      }
    } catch (err) {
      console.error('Erreur lancement analyse:', err);
      alert('Erreur de connexion au serveur. Verifiez que le backend est en cours d\'execution.');
    } finally {
      setRunningAnalysis(false);
    }
  };

  // Utilisateurs
  const handleApproveUser = async (userId: string) => {
    try {
      const res = await fetch(`${API_BASE}/users/${userId}/approve`, { method: 'POST' });
      if (res.ok) {
        loadUsers();
        setShowUserConfirmModal(null);
        alert('Utilisateur approuvé avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible d\'approuver l\'utilisateur'}`);
      }
    } catch (err) {
      console.error('Erreur approbation utilisateur:', err);
      alert('Erreur lors de l\'approbation de l\'utilisateur');
    }
  };

  const handleRejectUser = async (userId: string) => {
    try {
      const res = await fetch(`${API_BASE}/users/${userId}/reject`, { method: 'POST' });
      if (res.ok) {
        loadUsers();
        setShowUserConfirmModal(null);
        alert('Utilisateur rejeté avec succès !');
      } else {
        const error = await res.json();
        alert(`Erreur: ${error.detail || 'Impossible de rejeter l\'utilisateur'}`);
      }
    } catch (err) {
      console.error('Erreur rejet utilisateur:', err);
      alert('Erreur lors du rejet de l\'utilisateur');
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesFilter = userFilter === 'all' || u.status === userFilter;
    const fullName = `${u.first_name} ${u.last_name}`.toLowerCase();
    const matchesSearch = fullName.includes(userSearch.toLowerCase()) ||
                         u.email.toLowerCase().includes(userSearch.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const pendingCount = users.filter(u => u.status === 'pending').length;
  const approvedCount = users.filter(u => u.status === 'approved').length;
  const rejectedCount = users.filter(u => u.status === 'rejected').length;

  const tabs = [
    { key: 'sources', label: 'Sources de données', icon: '', count: sources.length },
    { key: 'suppliers', label: 'Fournisseurs', icon: '', count: suppliers.length },
    { key: 'sites', label: 'Sites Hutchinson', icon: '', count: sites.length },
    { key: 'categories', label: 'Catégories de risques', icon: '', count: categories.length },
    { key: 'scheduler', label: 'Planification', icon: '' },
    { key: 'stats', label: 'Statistiques', icon: '' },
    { key: 'users', label: 'Utilisateurs', icon: '', count: pendingCount > 0 ? pendingCount : undefined },
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
                <svg className="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
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

        {/* ========== FOURNISSEURS ========== */}
        {activeTab === 'suppliers' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-900">Gestion des Fournisseurs</h2>
              <button
                onClick={() => {
                  resetSupplierForm();
                  setShowSupplierModal('create');
                }}
                className="px-4 py-2 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                </svg>
                Ajouter un fournisseur
              </button>
            </div>

            {loadingSuppliers ? (
              <div className="text-center py-12 text-slate-500">Chargement...</div>
            ) : suppliers.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Aucun fournisseur</h3>
                <p className="text-slate-500 mb-6">Ajoutez des fournisseurs pour gérer votre supply chain</p>
                <button
                  onClick={() => setShowSupplierModal('create')}
                  className="px-6 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
                >
                  Ajouter le premier fournisseur
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {suppliers.map(supplier => (
                  <div key={supplier.id} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-slate-900">{supplier.name}</h3>
                          <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                            supplier.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {supplier.active ? '● Actif' : '○ Inactif'}
                          </span>
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-bold">
                            {supplier.sector}
                          </span>
                          {supplier.criticality_score && (
                            <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                              supplier.criticality_score >= 8 ? 'bg-red-100 text-red-700' :
                              supplier.criticality_score >= 5 ? 'bg-amber-100 text-amber-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              Criticité: {supplier.criticality_score}/10
                            </span>
                          )}
                        </div>
                        <p className="text-slate-500 text-sm mb-1">
                          {supplier.city ? `${supplier.city}, ` : ''}{supplier.country} • Code: {supplier.code}
                        </p>
                        <p className="text-slate-400 text-xs">
                          Produits: {supplier.products_supplied?.join(', ') || 'Non spécifié'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleSupplier(supplier.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            supplier.active ? 'hover:bg-amber-100 text-amber-600' : 'hover:bg-emerald-100 text-emerald-600'
                          }`}
                          title={supplier.active ? 'Désactiver' : 'Activer'}
                        >
                          {supplier.active ? (
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
                            setEditingSupplier(supplier);
                            setSupplierForm({
                              name: supplier.name,
                              code: supplier.code,
                              country: supplier.country,
                              region: supplier.region || '',
                              city: supplier.city || '',
                              address: supplier.address || '',
                              latitude: supplier.latitude?.toString() || '',
                              longitude: supplier.longitude?.toString() || '',
                              sector: supplier.sector,
                              products_supplied: supplier.products_supplied?.join(', ') || '',
                              company_size: supplier.company_size || 'PME',
                              certifications: supplier.certifications?.join(', ') || '',
                              financial_health: supplier.financial_health || 'bon',
                              criticality_score: supplier.criticality_score || 5,
                              active: supplier.active
                            });
                            setShowSupplierModal('edit');
                          }}
                          className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors"
                          title="Modifier"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteSupplier(supplier.id)}
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

        {/* ========== SITES HUTCHINSON ========== */}
        {activeTab === 'sites' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-900">Sites Hutchinson</h2>
              <button
                onClick={() => {
                  resetSiteForm();
                  setShowSiteModal('create');
                }}
                className="px-4 py-2 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                </svg>
                Ajouter un site
              </button>
            </div>

            {loadingSites ? (
              <div className="text-center py-12 text-slate-500">Chargement...</div>
            ) : sites.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                </svg>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Aucun site Hutchinson</h3>
                <p className="text-slate-500 mb-6">Ajoutez les sites de production pour surveiller les risques</p>
                <button
                  onClick={() => setShowSiteModal('create')}
                  className="px-6 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
                >
                  Ajouter le premier site
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {sites.map(site => (
                  <div key={site.id} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-slate-900">{site.name}</h3>
                          <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                            site.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {site.active ? '● Actif' : '○ Inactif'}
                          </span>
                          {site.strategic_importance && (
                            <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                              site.strategic_importance === 'critique' ? 'bg-red-100 text-red-700' :
                              site.strategic_importance === 'fort' ? 'bg-amber-100 text-amber-700' :
                              site.strategic_importance === 'moyen' ? 'bg-blue-100 text-blue-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              {site.strategic_importance.charAt(0).toUpperCase() + site.strategic_importance.slice(1)}
                            </span>
                          )}
                          {site.employee_count && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-bold">
                              {site.employee_count} employés
                            </span>
                          )}
                        </div>
                        <p className="text-slate-500 text-sm mb-1">
                          {site.city ? `${site.city}, ` : ''}{site.country} • Code: {site.code}
                        </p>
                        <p className="text-slate-400 text-xs">
                          Secteurs: {site.sectors?.join(', ') || 'Non spécifié'} • Produits: {site.products?.join(', ') || 'Non spécifié'}
                        </p>
                        {site.daily_revenue && (
                          <p className="text-slate-400 text-xs mt-1">
                            CA journalier: {site.daily_revenue.toLocaleString('fr-FR')} €
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleSite(site.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            site.active ? 'hover:bg-amber-100 text-amber-600' : 'hover:bg-emerald-100 text-emerald-600'
                          }`}
                          title={site.active ? 'Désactiver' : 'Activer'}
                        >
                          {site.active ? (
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
                            setEditingSite(site);
                            setSiteForm({
                              name: site.name,
                              code: site.code,
                              country: site.country,
                              region: site.region || '',
                              city: site.city || '',
                              address: site.address || '',
                              latitude: site.latitude?.toString() || '',
                              longitude: site.longitude?.toString() || '',
                              sectors: site.sectors?.join(', ') || '',
                              products: site.products?.join(', ') || '',
                              raw_materials: site.raw_materials?.join(', ') || '',
                              certifications: site.certifications?.join(', ') || '',
                              employee_count: site.employee_count?.toString() || '',
                              annual_production_value: site.annual_production_value?.toString() || '',
                              strategic_importance: site.strategic_importance || 'moyen',
                              daily_revenue: site.daily_revenue?.toString() || '',
                              active: site.active
                            });
                            setShowSiteModal('edit');
                          }}
                          className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors"
                          title="Modifier"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteSite(site.id)}
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
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
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
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                      />
                    </div>
                  )}

                  {schedulerForm.frequency === 'weekly' && (
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-2">Jour de la semaine</label>
                      <select
                        value={schedulerForm.day_of_week}
                        onChange={(e) => setSchedulerForm(prev => ({ ...prev, day_of_week: e.target.value }))}
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
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
                  <svg className="w-10 h-10 text-lime-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
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
                  <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  <p className="text-slate-500 text-sm">Documents collectés</p>
                  <p className="text-3xl font-black text-slate-900">{stats.documents.total}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  <p className="text-slate-500 text-sm">Analyses effectuées</p>
                  <p className="text-3xl font-black text-slate-900">{stats.analyses.total}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                  <p className="text-slate-500 text-sm">Sites industriels</p>
                  <p className="text-3xl font-black text-slate-900">{stats.entities.sites}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
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
              {loadingUsers ? (
                <div className="p-12 text-center text-slate-400">Chargement des utilisateurs...</div>
              ) : filteredUsers.length === 0 ? (
                <div className="p-12 text-center text-slate-400">Aucun utilisateur trouvé</div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredUsers.map(user => (
                    <div key={user.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-12 h-12 bg-gradient-to-br from-slate-700 to-slate-900 rounded-xl flex items-center justify-center text-white font-bold">
                            {user.first_name?.[0] || ''}{user.last_name?.[0] || ''}
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-900">{user.first_name} {user.last_name}</h3>
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
                            <p className="text-slate-400 text-xs font-bold">CRÉÉ LE</p>
                            <p className="text-slate-700">{new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
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

      {/* Modal Fournisseur */}
      {showSupplierModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => { setShowSupplierModal(null); setEditingSupplier(null); }}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-black text-slate-900">
                {showSupplierModal === 'create' ? 'Nouveau fournisseur' : 'Modifier le fournisseur'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Nom *</label>
                  <input
                    type="text"
                    value={supplierForm.name}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900 placeholder:text-slate-400"
                    placeholder="Nom du fournisseur"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Code *</label>
                  <input
                    type="text"
                    value={supplierForm.code}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-slate-900 placeholder:text-slate-400"
                    placeholder="SUP001"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Pays *</label>
                  <input
                    type="text"
                    value={supplierForm.country}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, country: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="France"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Région</label>
                  <input
                    type="text"
                    value={supplierForm.region}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, region: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="Normandie"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Ville</label>
                  <input
                    type="text"
                    value={supplierForm.city}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, city: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="Rouen"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Secteur d'activité *</label>
                <input
                  type="text"
                  value={supplierForm.sector}
                  onChange={(e) => setSupplierForm(prev => ({ ...prev, sector: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="Chimie, Métallurgie, Électronique..."
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Produits fournis * (séparés par virgule)</label>
                <input
                  type="text"
                  value={supplierForm.products_supplied}
                  onChange={(e) => setSupplierForm(prev => ({ ...prev, products_supplied: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="Composants électroniques, Caoutchouc, Plastique"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Latitude</label>
                  <input
                    type="text"
                    value={supplierForm.latitude}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, latitude: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900"
                    placeholder="48.8566"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Longitude</label>
                  <input
                    type="text"
                    value={supplierForm.longitude}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, longitude: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900"
                    placeholder="2.3522"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Taille entreprise</label>
                  <select
                    value={supplierForm.company_size}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, company_size: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  >
                    <option value="PME">PME</option>
                    <option value="ETI">ETI</option>
                    <option value="Grand groupe">Grand groupe</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Santé financière</label>
                  <select
                    value={supplierForm.financial_health}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, financial_health: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  >
                    <option value="excellent">Excellent</option>
                    <option value="bon">Bon</option>
                    <option value="moyen">Moyen</option>
                    <option value="faible">Faible</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Criticité (1-10)</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={supplierForm.criticality_score}
                    onChange={(e) => setSupplierForm(prev => ({ ...prev, criticality_score: parseInt(e.target.value) || 5 }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Certifications (séparées par virgule)</label>
                <input
                  type="text"
                  value={supplierForm.certifications}
                  onChange={(e) => setSupplierForm(prev => ({ ...prev, certifications: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="ISO 9001, ISO 14001, IATF 16949"
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="supplier_active"
                  checked={supplierForm.active}
                  onChange={(e) => setSupplierForm(prev => ({ ...prev, active: e.target.checked }))}
                  className="w-5 h-5 rounded border-slate-300 text-lime-500"
                />
                <label htmlFor="supplier_active" className="font-bold text-slate-700">Fournisseur actif</label>
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex gap-3">
              <button
                onClick={() => { setShowSupplierModal(null); setEditingSupplier(null); resetSupplierForm(); }}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200"
              >
                Annuler
              </button>
              <button
                onClick={showSupplierModal === 'create' ? handleCreateSupplier : handleUpdateSupplier}
                className="flex-1 px-4 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
              >
                {showSupplierModal === 'create' ? 'Créer' : 'Sauvegarder'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Site Hutchinson */}
      {showSiteModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => { setShowSiteModal(null); setEditingSite(null); }}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-black text-slate-900">
                {showSiteModal === 'create' ? 'Nouveau site Hutchinson' : 'Modifier le site'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Nom du site *</label>
                  <input
                    type="text"
                    value={siteForm.name}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900 placeholder:text-slate-400"
                    placeholder="Hutchinson Châlette"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Code *</label>
                  <input
                    type="text"
                    value={siteForm.code}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-slate-900 placeholder:text-slate-400"
                    placeholder="SITE001"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Pays *</label>
                  <input
                    type="text"
                    value={siteForm.country}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, country: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="France"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Région</label>
                  <input
                    type="text"
                    value={siteForm.region}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, region: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="Centre-Val de Loire"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Ville</label>
                  <input
                    type="text"
                    value={siteForm.city}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, city: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="Châlette-sur-Loing"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Latitude</label>
                  <input
                    type="text"
                    value={siteForm.latitude}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, latitude: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900"
                    placeholder="47.9833"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Longitude</label>
                  <input
                    type="text"
                    value={siteForm.longitude}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, longitude: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 font-mono text-sm text-slate-900"
                    placeholder="2.7333"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Secteurs (séparés par virgule)</label>
                <input
                  type="text"
                  value={siteForm.sectors}
                  onChange={(e) => setSiteForm(prev => ({ ...prev, sectors: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="automotive, aerospace"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Produits fabriqués (séparés par virgule)</label>
                <input
                  type="text"
                  value={siteForm.products}
                  onChange={(e) => setSiteForm(prev => ({ ...prev, products: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="joints, tuyaux, pièces techniques"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Matières premières (séparées par virgule)</label>
                <input
                  type="text"
                  value={siteForm.raw_materials}
                  onChange={(e) => setSiteForm(prev => ({ ...prev, raw_materials: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="caoutchouc, plastique, métal"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Employés</label>
                  <input
                    type="number"
                    value={siteForm.employee_count}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, employee_count: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">CA journalier (€)</label>
                  <input
                    type="number"
                    value={siteForm.daily_revenue}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, daily_revenue: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                    placeholder="50000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Importance</label>
                  <select
                    value={siteForm.strategic_importance}
                    onChange={(e) => setSiteForm(prev => ({ ...prev, strategic_importance: e.target.value }))}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  >
                    <option value="faible">Faible</option>
                    <option value="moyen">Moyen</option>
                    <option value="fort">Fort</option>
                    <option value="critique">Critique</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Certifications (séparées par virgule)</label>
                <input
                  type="text"
                  value={siteForm.certifications}
                  onChange={(e) => setSiteForm(prev => ({ ...prev, certifications: e.target.value }))}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-400 text-slate-900"
                  placeholder="ISO 9001, ISO 14001, IATF 16949"
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="site_active"
                  checked={siteForm.active}
                  onChange={(e) => setSiteForm(prev => ({ ...prev, active: e.target.checked }))}
                  className="w-5 h-5 rounded border-slate-300 text-lime-500"
                />
                <label htmlFor="site_active" className="font-bold text-slate-700">Site actif</label>
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex gap-3">
              <button
                onClick={() => { setShowSiteModal(null); setEditingSite(null); resetSiteForm(); }}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200"
              >
                Annuler
              </button>
              <button
                onClick={showSiteModal === 'create' ? handleCreateSite : handleUpdateSite}
                className="flex-1 px-4 py-3 bg-lime-500 text-white rounded-xl font-bold hover:bg-lime-600"
              >
                {showSiteModal === 'create' ? 'Créer' : 'Sauvegarder'}
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
              <p className="text-white/80">{showUserConfirmModal.user.first_name} {showUserConfirmModal.user.last_name}</p>
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
