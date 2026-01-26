import React, { useState } from 'react';
import { BarChart, FileText, TrendingUp, AlertTriangle, Calendar, Download, Bell, CheckCircle, User, Mail, Building, Shield } from 'lucide-react';
import './DecisionDashboard.css';

interface DashboardStats {
  totalRegulations: number;
  progressPercentage: number;
  validatedPercentage: number;
  highRisks: number;
  criticalDeadlines: number;
}

export const DecisionDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState<'dashboard' | 'profile'>('dashboard');
  
  const stats: DashboardStats = {
    totalRegulations: 123,
    progressPercentage: 78,
    validatedPercentage: 22,
    highRisks: 15,
    criticalDeadlines: 7
  };

  const handleExportPDF = () => {
    // Logique d'export PDF
    alert('Export PDF en cours...');
  };

  const handleLogout = () => {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
      window.location.reload();
    }
  };

  return (
    <div className="decision-layout">
      {/* Sidebar */}
      <div className="decision-sidebar">
        <div className="decision-sidebar-header">
          <div className="decision-logo">
            <div className="decision-logo-icon">G</div>
          </div>
          <h2 className="decision-user-name">Décideur Hutchinson</h2>
        </div>

        <nav className="decision-sidebar-nav">
          <div 
            className={`decision-nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            <BarChart className="decision-nav-icon" />
            <span>Dashboard</span>
          </div>
          
          <div 
            className={`decision-nav-item ${activeView === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveView('profile')}
          >
            <FileText className="decision-nav-icon" />
            <span>Profil</span>
          </div>
          
          <div className="decision-nav-item disconnect" onClick={handleLogout}>
            <span>Déconnexion</span>
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="decision-main-content">
        <header className="decision-main-header">
          <div className="decision-header-left">
            <div className="decision-notification-icon">
              <Bell size={24} color="#f59e0b" />
            </div>
            <h1>{activeView === 'dashboard' ? 'Dashboard Décideurs' : 'Profil Utilisateur'}</h1>
          </div>
          
          {activeView === 'dashboard' && (
            <div className="decision-header-right">
              <button 
                className="decision-export-btn"
                onClick={handleExportPDF}
              >
                <Download className="btn-icon" />
                Exporter Dashboard PDF
              </button>
            </div>
          )}
        </header>

        {/* Conditional Content */}
        {activeView === 'dashboard' ? (
          // Dashboard Content
          <div className="decision-content">
          <section className="decision-indicators-section">
            <h2>Indicateurs clés</h2>
            
            <div className="decision-indicators-grid">
              <div className="decision-indicator-card">
                <div className="decision-indicator-icon">
                  <FileText size={32} color="#6b7280" />
                </div>
                <div className="decision-indicator-value">{stats.totalRegulations}</div>
                <div className="decision-indicator-label">Réglementations suivies</div>
              </div>

              <div className="decision-indicator-card">
                <div className="decision-indicator-icon">
                  <div className="decision-check-icon">
                    <CheckCircle size={24} color="white" />
                  </div>
                </div>
                <div className="decision-indicator-value">
                  {stats.progressPercentage}% / {stats.validatedPercentage}%
                </div>
                <div className="decision-indicator-label">En cours vs Validées</div>
              </div>

              <div className="decision-indicator-card warning">
                <div className="decision-indicator-icon">
                  <AlertTriangle size={32} color="#f59f0bfb" />
                </div>
                <div className="decision-indicator-value">{stats.highRisks}</div>
                <div className="decision-indicator-label">Risques élevés détectés</div>
              </div>

              <div className="decision-indicator-card">
                <div className="decision-indicator-icon">
                  <Calendar size={32} color="#6b7280" />
                </div>
                <div className="decision-indicator-value">{stats.criticalDeadlines}</div>
                <div className="decision-indicator-label">Deadlines critiques (6 mois)</div>
              </div>
            </div>
          </section>

          {/* Visualizations */}
          <section className="decision-visualizations-section">
            <h2>Visualisations</h2>
            
            <div className="decision-charts-grid">
              <div className="decision-chart-card">
                <h3>Répartition par date d'application</h3>
                <div className="decision-chart-placeholder">
                  <BarChart size={48} color="#9caeafff" />
                  <p>Graphique de répartition temporelle</p>
                </div>
              </div>

              <div className="decision-chart-card">
                <h3>Répartition par process</h3>
                <div className="decision-chart-placeholder">
                  <TrendingUp size={48} color="#9ca3af" />
                  <p>Graphique de répartition par processus</p>
                </div>
              </div>
            </div>
          </section>
        </div>
        ) : (
          // Profile Content
          <div className="decision-content">
            <section className="profile-section">
              <div className="profile-card">
                <div className="profile-header">
                  <div className="profile-avatar-large">
                    <User size={48} color="#fff" />
                  </div>
                  <h2>Décideur Hutchinson</h2>
                  <p className="profile-role">Profil Décisionnel</p>
                </div>

                <div className="profile-info-grid">
                  <div className="profile-info-item">
                    <div className="profile-info-icon">
                      <Mail size={20} color="#dc2626" />
                    </div>
                    <div className="profile-info-content">
                      <div className="profile-info-label">Email</div>
                      <div className="profile-info-value">decideur@hutchinson.com</div>
                    </div>
                  </div>

                  <div className="profile-info-item">
                    <div className="profile-info-icon">
                      <Building size={20} color="#dc2626" />
                    </div>
                    <div className="profile-info-content">
                      <div className="profile-info-label">Département</div>
                      <div className="profile-info-value">Direction Générale</div>
                    </div>
                  </div>

                  <div className="profile-info-item">
                    <div className="profile-info-icon">
                      <Shield size={20} color="#dc2626" />
                    </div>
                    <div className="profile-info-content">
                      <div className="profile-info-label">Permissions</div>
                      <div className="profile-info-value">Lecture Dashboard, Export PDF</div>
                    </div>
                  </div>

                  <div className="profile-info-item">
                    <div className="profile-info-icon">
                      <Calendar size={20} color="#dc2626" />
                    </div>
                    <div className="profile-info-content">
                      <div className="profile-info-label">Dernière connexion</div>
                      <div className="profile-info-value">15/01/2026 - 14:30</div>
                    </div>
                  </div>
                </div>

                <div className="profile-stats">
                  <h3>Statistiques d'utilisation</h3>
                  <div className="profile-stats-grid">
                    <div className="profile-stat-item">
                      <div className="profile-stat-value">47</div>
                      <div className="profile-stat-label">Connexions ce mois</div>
                    </div>
                    <div className="profile-stat-item">
                      <div className="profile-stat-value">23</div>
                      <div className="profile-stat-label">Exports PDF</div>
                    </div>
                    <div className="profile-stat-item">
                      <div className="profile-stat-value">156</div>
                      <div className="profile-stat-label">Réglementations consultées</div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
};