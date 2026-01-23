import React from 'react';
import { Calendar, Filter, Tag, BarChart3 } from 'lucide-react';
import './AdvancedFilters.css';

export interface FilterOptions {
  dateRange: 'all' | 'week' | 'month' | 'custom';
  customStartDate?: string;
  customEndDate?: string;
  regulationType: string[];
  ncCodes: string[];
  confidenceMin: number;
  confidenceMax: number;
}

interface AdvancedFiltersProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  onReset: () => void;
}

export const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onReset,
}) => {
  const handleDateRangeChange = (range: FilterOptions['dateRange']) => {
    onFiltersChange({ ...filters, dateRange: range });
  };

  const handleTypeToggle = (type: string) => {
    const types = filters.regulationType.includes(type)
      ? filters.regulationType.filter(t => t !== type)
      : [...filters.regulationType, type];
    onFiltersChange({ ...filters, regulationType: types });
  };

  const handleNCCodeChange = (code: string) => {
    const codes = filters.ncCodes.includes(code)
      ? filters.ncCodes.filter(c => c !== code)
      : [...filters.ncCodes, code];
    onFiltersChange({ ...filters, ncCodes: codes });
  };

  const handleConfidenceChange = (min: number, max: number) => {
    onFiltersChange({ ...filters, confidenceMin: min, confidenceMax: max });
  };

  const regulationTypes = ['EU', 'Directive', 'Règlement', 'Décision'];
  const commonNCCodes = ['2804', '2805', '2806', '2807', '2901', '2902'];

  return (
    <div className="advanced-filters">
      <div className="filters-header">
        <Filter size={20} />
        <h3>Filtres avancés</h3>
        <button onClick={onReset} className="reset-btn">
          Réinitialiser
        </button>
      </div>

      {/* Filtre par date */}
      <div className="filter-section">
        <div className="filter-label">
          <Calendar size={18} />
          <span>Période</span>
        </div>
        <div className="date-filter-options">
          <button
            className={`filter-chip ${filters.dateRange === 'all' ? 'active' : ''}`}
            onClick={() => handleDateRangeChange('all')}
          >
            Toutes
          </button>
          <button
            className={`filter-chip ${filters.dateRange === 'week' ? 'active' : ''}`}
            onClick={() => handleDateRangeChange('week')}
          >
            Cette semaine
          </button>
          <button
            className={`filter-chip ${filters.dateRange === 'month' ? 'active' : ''}`}
            onClick={() => handleDateRangeChange('month')}
          >
            Ce mois
          </button>
          <button
            className={`filter-chip ${filters.dateRange === 'custom' ? 'active' : ''}`}
            onClick={() => handleDateRangeChange('custom')}
          >
            Personnalisé
          </button>
        </div>

        {filters.dateRange === 'custom' && (
          <div className="custom-date-inputs">
            <input
              type="date"
              value={filters.customStartDate || ''}
              onChange={(e) =>
                onFiltersChange({ ...filters, customStartDate: e.target.value })
              }
              className="date-input"
            />
            <span>à</span>
            <input
              type="date"
              value={filters.customEndDate || ''}
              onChange={(e) =>
                onFiltersChange({ ...filters, customEndDate: e.target.value })
              }
              className="date-input"
            />
          </div>
        )}
      </div>

      {/* Filtre par type */}
      <div className="filter-section">
        <div className="filter-label">
          <Tag size={18} />
          <span>Type de réglementation</span>
        </div>
        <div className="type-filter-options">
          {regulationTypes.map((type) => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.regulationType.includes(type)}
                onChange={() => handleTypeToggle(type)}
              />
              <span>{type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Filtre par codes NC */}
      <div className="filter-section">
        <div className="filter-label">
          <Tag size={18} />
          <span>Codes NC</span>
        </div>
        <div className="nc-codes-filter">
          {commonNCCodes.map((code) => (
            <button
              key={code}
              className={`nc-code-chip ${
                filters.ncCodes.includes(code) ? 'active' : ''
              }`}
              onClick={() => handleNCCodeChange(code)}
            >
              {code}
            </button>
          ))}
        </div>
      </div>

      {/* Filtre par confiance IA */}
      <div className="filter-section">
        <div className="filter-label">
          <BarChart3 size={18} />
          <span>Niveau de confiance IA</span>
        </div>
        <div className="confidence-filter">
          <div className="confidence-labels">
            <span>{Math.round(filters.confidenceMin * 100)}%</span>
            <span>{Math.round(filters.confidenceMax * 100)}%</span>
          </div>
          <div className="range-inputs">
            <input
              type="range"
              min="0"
              max="100"
              value={filters.confidenceMin * 100}
              onChange={(e) =>
                handleConfidenceChange(
                  parseInt(e.target.value) / 100,
                  filters.confidenceMax
                )
              }
              className="confidence-slider"
            />
            <input
              type="range"
              min="0"
              max="100"
              value={filters.confidenceMax * 100}
              onChange={(e) =>
                handleConfidenceChange(
                  filters.confidenceMin,
                  parseInt(e.target.value) / 100
                )
              }
              className="confidence-slider"
            />
          </div>
          <div className="confidence-indicator">
            <div
              className="confidence-bar"
              style={{
                left: `${filters.confidenceMin * 100}%`,
                width: `${(filters.confidenceMax - filters.confidenceMin) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
