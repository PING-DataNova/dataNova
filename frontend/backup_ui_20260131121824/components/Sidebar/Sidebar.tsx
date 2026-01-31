import React from 'react';
import { FileText, User, LogOut, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  userName: string;
  activeFilter: string;
  onFilterChange: (filter: string) => void;
  onLogout?: () => void;
  regulationCounts: {
    pending: number;
    validated: number;
    rejected: number;
    toReview: number;
  };
}

export const Sidebar: React.FC<SidebarProps> = ({ userName, activeFilter, onFilterChange, onLogout, regulationCounts }) => {
  
  const handleLogout = () => {
    if (onLogout) {
      if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        onLogout();
      }
    } else {
      if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        window.location.reload();
      }
    }
  };
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon">G</div>
        </div>
        <h2 className="user-name">Juriste {userName}</h2>
      </div>

      <nav className="sidebar-nav">
        <div 
          className={`nav-item ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => onFilterChange('all')}
        >
          <FileText className="nav-icon" />
          <span>Réglementations</span>
          <span className="notification-badge">{regulationCounts.pending}</span>
        </div>
        
        <div 
          className={`nav-item ${activeFilter === 'to-review' ? 'active' : ''}`}
          onClick={() => onFilterChange('to-review')}
        >
          <AlertCircle className="nav-icon" />
          <span>À revoir</span>
          {regulationCounts.toReview > 0 && (
            <span className="notification-badge orange">{regulationCounts.toReview}</span>
          )}
        </div>
        
        <div 
          className={`nav-item ${activeFilter === 'validated' ? 'active' : ''}`}
          onClick={() => onFilterChange('validated')}
        >
          <CheckCircle className="nav-icon" />
          <span>Validées</span>
          {regulationCounts.validated > 0 && (
            <span className="notification-badge green">{regulationCounts.validated}</span>
          )}
        </div>
        
        <div 
          className={`nav-item ${activeFilter === 'rejected' ? 'active' : ''}`}
          onClick={() => onFilterChange('rejected')}
        >
          <XCircle className="nav-icon" />
          <span>Rejetées</span>
          {regulationCounts.rejected > 0 && (
            <span className="notification-badge red">{regulationCounts.rejected}</span>
          )}
        </div>
        
        <div className="nav-item">
          <User className="nav-icon" />
          <span>Profil</span>
        </div>
        
        <div 
          className="nav-item disconnect"
          onClick={handleLogout}
        >
          <LogOut className="nav-icon" />
          <span>Déconnexion</span>
        </div>
      </nav>
    </div>
  );
};