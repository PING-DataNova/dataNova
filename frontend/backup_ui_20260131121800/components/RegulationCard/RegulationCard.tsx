import React from 'react';
import { Regulation } from '../../types';
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react';
import './RegulationCard.css';

interface RegulationCardProps {
  regulation: Regulation;
  onValidate: (id: string) => void;
  onReject: (id: string) => void;
  onReview: (id: string) => void;
  disabled?: boolean;
}

export const RegulationCard: React.FC<RegulationCardProps> = ({
  regulation,
  onValidate,
  onReject,
  onReview,
  // disabled prop available but not used yet
}) => {
  const getStatusIcon = () => {
    switch (regulation.status) {
      case 'validated':
        return <CheckCircle className="status-icon validated" />;
      case 'rejected':
        return <XCircle className="status-icon rejected" />;
      case 'to-review':
        return <AlertCircle className="status-icon to-review" />;
      default:
        return <Clock className="status-icon pending" />;
    }
  };

  const getStatusText = () => {
    switch (regulation.status) {
      case 'validated':
        return 'Validée';
      case 'rejected':
        return 'Rejetée';
      case 'to-review':
        return 'À revoir';
      default:
        return 'En attente';
    }
  };

  const getStatusClass = () => {
    switch (regulation.status) {
      case 'validated':
        return 'status-badge validated';
      case 'rejected':
        return 'status-badge rejected';
      case 'to-review':
        return 'status-badge to-review';
      default:
        return 'status-badge pending';
    }
  };

  return (
    <div className="regulation-card">
      <div className="regulation-header">
        <div className="regulation-info">
          <h3 className="regulation-title">{regulation.title}</h3>
          <span className="regulation-reference">{regulation.reference}</span>
        </div>
        <div className="regulation-status">
          {getStatusIcon()}
          <span className={getStatusClass()}>{getStatusText()}</span>
        </div>
      </div>
      
      <p className="regulation-description">{regulation.description}</p>
      
      <div className="regulation-actions">
        {regulation.status === 'pending' && (
          <>
            <button 
              className="action-btn validate-btn"
              onClick={() => onValidate(regulation.id)}
            >
              Valider
            </button>
            <button 
              className="action-btn reject-btn"
              onClick={() => onReject(regulation.id)}
            >
              Rejeter
            </button>
            <button 
              className="action-btn review-btn"
              onClick={() => onReview(regulation.id)}
            >
              À revoir
            </button>
          </>
        )}
      </div>
    </div>
  );
};