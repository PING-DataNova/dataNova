
import React, { useState } from 'react';
import { Search, Bell, AlertCircle, Loader2, Download, Copy, SlidersHorizontal } from 'lucide-react';
import { Regulation } from '../types';
import { RegulationCard } from '../components/RegulationCard/RegulationCard';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { AdvancedFilters, FilterOptions } from '../components/AdvancedFilters/AdvancedFilters';
import { useRegulations, useRegulationActions } from '../hooks/useRegulations';
import { downloadValidatedRegulationsJSON, copyValidatedRegulationsJSON } from '../utils/exportData';
import { authService } from '../services/auth.service';
import './LegalTeamPage.css';

export const LegalTeamPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [copySuccess, setCopySuccess] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  const [advancedFilters, setAdvancedFilters] = useState<FilterOptions>({
    dateRange: 'all',
    regulationType: [],
    ncCodes: [],
    confidenceMin: 0,
    confidenceMax: 1,
  });
  
  // Utilisation du hook pour récupérer les données du backend
  const { regulations, loading, error, total, refetch } = useRegulations({
    status: activeFilter,
    search: searchTerm,
  });

  // Hook pour les actions de mise à jour
  const { updating, error: updateError, updateStatus } = useRegulationActions(() => {
    refetch(); // Recharger les données après une mise à jour
  });

  const handleValidate = async (id: string) => {
    try {
      await updateStatus(id, 'validated');
    } catch (error) {
      console.error('Erreur validation:', error);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await updateStatus(id, 'rejected');
    } catch (error) {
      console.error('Erreur rejet:', error);
    }
  };

  const handleReview = async (id: string) => {
    try {
      await updateStatus(id, 'to-review');
    } catch (error) {
      console.error('Erreur mise en revue:', error);
    }
  };

  const handleExportJSON = () => {
    downloadValidatedRegulationsJSON();
  };

  const handleCopyJSON = async () => {
    const success = await copyValidatedRegulationsJSON();
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const handleResetFilters = () => {
    setAdvancedFilters({
      dateRange: 'all',
      regulationType: [],
      ncCodes: [],
      confidenceMin: 0,
      confidenceMax: 1,
    });
  };

  const applyAdvancedFilters = (regs: Regulation[]) => {
    let filtered = [...regs];

    // Filtre par date
    if (advancedFilters.dateRange !== 'all') {
      const now = new Date();
      filtered = filtered.filter((reg) => {
        const regDate = new Date(reg.dateCreated);
        if (advancedFilters.dateRange === 'week') {
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          return regDate >= weekAgo;
        }
        if (advancedFilters.dateRange === 'month') {
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          return regDate >= monthAgo;
        }
        if (advancedFilters.dateRange === 'custom' && advancedFilters.customStartDate && advancedFilters.customEndDate) {
          const start = new Date(advancedFilters.customStartDate);
          const end = new Date(advancedFilters.customEndDate);
          return regDate >= start && regDate <= end;
        }
        return true;
      });
    }

    // Filtre par type
    if (advancedFilters.regulationType.length > 0) {
      filtered = filtered.filter((reg) =>
        advancedFilters.regulationType.includes(reg.type)
      );
    }

    // Filtre par codes NC (simulé avec mock data)
    // Dans la vraie API, les réglementations auront un champ ncCodes
    if (advancedFilters.ncCodes.length > 0) {
      // Pour l'instant, on garde toutes les réglementations
      // Car les données mockées n'ont pas de codes NC
    }

    // Filtre par confiance IA (simulé - mock data n'a pas ce champ)
    // Dans la vraie API, filtrer par confidence between min and max

    return filtered;
  };

  const getFilteredRegulations = () => {
    return applyAdvancedFilters(regulations);
  };

  const filteredRegulations = getFilteredRegulations();

  const regulationCounts = {
    pending: regulations.filter(reg => reg.status === 'pending').length,
    validated: regulations.filter(reg => reg.status === 'validated').length,
    rejected: regulations.filter(reg => reg.status === 'rejected').length,
    toReview: regulations.filter(reg => reg.status === 'to-review').length,
  };

  const getPageTitle = () => {
    switch (activeFilter) {
      case 'pending':
        return 'Réglementations en attente';
      case 'validated':
        return 'Réglementations validées';
      case 'rejected':
        return 'Réglementations rejetées';
      case 'to-review':
        return 'Réglementations à revoir';
      default:
        return 'Toutes les réglementations';
    }
  };

  const getPageSubtitle = () => {
    switch (activeFilter) {
      case 'pending':
        return 'En attente de validation';
      case 'validated':
        return 'Validées par l\'équipe juridique';
      case 'rejected':
        return 'Rejetées par l\'équipe juridique';
      case 'to-review':
        return 'À revoir';
      default:
        return 'Vue d\'ensemble';
    }
  };

  return (
    <div className="legal-team-layout">
      <Sidebar 
        userName="Hutchinson" 
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        regulationCounts={regulationCounts}
      />
      
      <div className="main-content">
        <header className="main-header">
          <div className="header-left">
            <h1>{getPageTitle()}</h1>
            <p className="header-subtitle">{getPageSubtitle()}</p>
          </div>
          
          <div className="header-right">
            <div className="search-container">
              <Search className="search-icon" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>

            <button 
              className={`filters-toggle-btn ${showAdvancedFilters ? 'active' : ''}`}
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              title="Filtres avancés"
            >
              <SlidersHorizontal size={20} />
              Filtres
            </button>
            
            <button className="notification-btn">
              <Bell className="bell-icon" />
            </button>

            {activeFilter === 'validated' && (
              <>
                <button 
                  className="export-btn"
                  onClick={handleExportJSON}
                  title="Télécharger en JSON"
                >
                  <Download size={20} />
                  Export JSON
                </button>
                <button 
                  className="copy-btn"
                  onClick={handleCopyJSON}
                  title="Copier le JSON"
                >
                  <Copy size={20} />
                  {copySuccess ? '✓ Copié!' : 'Copier JSON'}
                </button>
              </>
            )}
            
            <button 
              className="disconnect-btn"
              onClick={() => {
                if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
                  authService.logout();
                  window.location.reload();
                }
              }}
            >
              Déconnexion
            </button>
          </div>
        </header>

        {showAdvancedFilters && (
          <div className="filters-container">
            <AdvancedFilters
              filters={advancedFilters}
              onFiltersChange={setAdvancedFilters}
              onReset={handleResetFilters}
            />
          </div>
        )}

        <div className="content-stats">
          <p className="regulations-count">
            {loading ? 'Chargement...' : `${total} réglementations au total`}
          </p>
          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>Erreur: {error}</span>
              <button onClick={refetch} className="retry-btn">Réessayer</button>
            </div>
          )}
          {updateError && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>Erreur de mise à jour: {updateError}</span>
            </div>
          )}
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader2 className="loading-spinner" />
            <p>Chargement des réglementations...</p>
          </div>
        ) : (
          <>
            <div className="regulations-list">
              {filteredRegulations.map((regulation) => (
                <RegulationCard
                  key={regulation.id}
                  regulation={regulation}
                  onValidate={handleValidate}
                  onReject={handleReject}
                  onReview={handleReview}
                  disabled={updating}
                />
              ))}
            </div>

            {!loading && filteredRegulations.length === 0 && !error && (
              <div className="empty-state">
                <p>Aucune réglementation trouvée.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};