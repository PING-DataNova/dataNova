
import React, { useState } from 'react';
import { Search, Bell, AlertCircle, Loader2 } from 'lucide-react';
import { Regulation } from '../types';
import { RegulationCard } from '../components/RegulationCard/RegulationCard';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { useRegulations, useRegulationActions } from '../hooks/useRegulations';
import './LegalTeamPage.css';

export const LegalTeamPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  
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

  const getFilteredRegulations = () => {
    // Plus besoin de filtrage côté frontend car c'est fait par l'API
    return regulations;
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
            
            <button className="notification-btn">
              <Bell className="bell-icon" />
            </button>
            
            <button 
              className="disconnect-btn"
              onClick={() => {
                if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
                  alert('Déconnexion réussie');
                }
              }}
            >
              Déconnexion
            </button>
          </div>
        </header>

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