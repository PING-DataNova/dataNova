import React, { useState } from 'react';
import { 
  SupplierAnalysisRequest, 
  SupplierAnalysisResponse,
  COUNTRIES,
  COMMON_MATERIALS,
  COMMON_NC_CODES
} from '../types/supplier';
import { analyzeSupplier } from '../services/supplierService';
import SupplierAnalysisResults from './SupplierAnalysisResults';
import './SupplierAnalysis.css';

interface SupplierAnalysisProps {
  onBack: () => void;
}

const SupplierAnalysis: React.FC<SupplierAnalysisProps> = ({ onBack }) => {
  // État du formulaire
  const [formData, setFormData] = useState<SupplierAnalysisRequest>({
    name: '',
    country: '',
    city: '',
    latitude: undefined,
    longitude: undefined,
    materials: [],
    nc_codes: [],
    criticality: 'Standard',
    annual_volume: undefined,
  });

  // État de l'interface
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SupplierAnalysisResponse | null>(null);
  
  // Champs temporaires pour ajout
  const [newMaterial, setNewMaterial] = useState('');
  const [newNcCode, setNewNcCode] = useState('');

  // Validation du formulaire
  const isFormValid = formData.name.trim() !== '' && 
                      formData.country !== '' && 
                      formData.materials.length > 0;

  // Handlers
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }));
  };

  const handleAddMaterial = () => {
    const trimmed = newMaterial.trim();
    console.log('Adding material:', trimmed, 'Current materials:', formData.materials);
    if (trimmed && !formData.materials.includes(trimmed)) {
      setFormData(prev => ({
        ...prev,
        materials: [...prev.materials, trimmed]
      }));
      setNewMaterial('');
    }
  };

  const handleRemoveMaterial = (material: string) => {
    setFormData(prev => ({
      ...prev,
      materials: prev.materials.filter(m => m !== material)
    }));
  };

  const handleAddNcCode = () => {
    if (newNcCode.trim() && !formData.nc_codes?.includes(newNcCode.trim())) {
      setFormData(prev => ({
        ...prev,
        nc_codes: [...(prev.nc_codes || []), newNcCode.trim()]
      }));
      setNewNcCode('');
    }
  };

  const handleRemoveNcCode = (code: string) => {
    setFormData(prev => ({
      ...prev,
      nc_codes: (prev.nc_codes || []).filter(c => c !== code)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeSupplier(formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'analyse');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setResult(null);
    setFormData({
      name: '',
      country: '',
      city: '',
      latitude: undefined,
      longitude: undefined,
      materials: [],
      nc_codes: [],
      criticality: 'Standard',
      annual_volume: undefined,
    });
  };

  // Si on a un résultat, afficher la page des résultats
  if (result) {
    return (
      <SupplierAnalysisResults 
        result={result} 
        onNewAnalysis={handleNewAnalysis}
        onBack={onBack}
      />
    );
  }

  return (
    <div className="supplier-analysis-page">
      <div className="supplier-analysis-header">
        <button className="back-button" onClick={onBack}>
          ← Retour
        </button>
        <h1>🔍 Analyse de Risques Fournisseur</h1>
        <p className="subtitle">
          Évaluez les risques réglementaires et météorologiques pour un fournisseur
        </p>
      </div>

      <form className="supplier-form" onSubmit={handleSubmit}>
        {/* Informations de base */}
        <div className="form-section">
          <h2>📋 Informations du fournisseur</h2>
          
          <div className="form-group">
            <label htmlFor="name">Nom du fournisseur *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Ex: Thai Rubber Co."
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="country">Pays *</label>
              <select
                id="country"
                name="country"
                value={formData.country}
                onChange={handleInputChange}
                required
              >
                <option value="">Sélectionner un pays</option>
                {COUNTRIES.map(country => (
                  <option key={country} value={country}>{country}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="city">Ville</label>
              <input
                type="text"
                id="city"
                name="city"
                value={formData.city || ''}
                onChange={handleInputChange}
                placeholder="Ex: Bangkok"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="latitude">Latitude (optionnel)</label>
              <input
                type="number"
                id="latitude"
                name="latitude"
                value={formData.latitude || ''}
                onChange={handleInputChange}
                placeholder="Ex: 13.7563"
                step="0.0001"
                min="-90"
                max="90"
              />
            </div>

            <div className="form-group">
              <label htmlFor="longitude">Longitude (optionnel)</label>
              <input
                type="number"
                id="longitude"
                name="longitude"
                value={formData.longitude || ''}
                onChange={handleInputChange}
                placeholder="Ex: 100.5018"
                step="0.0001"
                min="-180"
                max="180"
              />
            </div>
          </div>
        </div>

        {/* Matières fournies */}
        <div className="form-section">
          <h2>🏭 Matières fournies *</h2>
          
          <div className="tags-input">
            <div className="tags-list">
              {formData.materials.map(material => (
                <span key={material} className="tag">
                  {material}
                  <button type="button" onClick={() => handleRemoveMaterial(material)}>×</button>
                </span>
              ))}
            </div>
            
            <div className="add-tag">
              <input
                type="text"
                value={newMaterial}
                onChange={(e) => {
                  console.log('Material input changed:', e.target.value);
                  setNewMaterial(e.target.value);
                }}
                placeholder="Ajouter une matière"
                list="materials-list"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddMaterial();
                  }
                }}
              />
              <datalist id="materials-list">
                {COMMON_MATERIALS.map(m => (
                  <option key={m} value={m} />
                ))}
              </datalist>
              <button type="button" onClick={() => {
                console.log('Button clicked, newMaterial:', newMaterial);
                handleAddMaterial();
              }}>+ Ajouter</button>
            </div>
          </div>
        </div>

        {/* Codes NC */}
        <div className="form-section">
          <h2>📦 Codes NC (douaniers)</h2>
          
          <div className="tags-input">
            <div className="tags-list">
              {(formData.nc_codes || []).map(code => (
                <span key={code} className="tag tag-code">
                  {code}
                  <button type="button" onClick={() => handleRemoveNcCode(code)}>×</button>
                </span>
              ))}
            </div>
            
            <div className="add-tag">
              <select
                value={newNcCode}
                onChange={(e) => setNewNcCode(e.target.value)}
              >
                <option value="">Sélectionner un code NC</option>
                {COMMON_NC_CODES.map(nc => (
                  <option key={nc.code} value={nc.code}>
                    {nc.code} - {nc.label}
                  </option>
                ))}
              </select>
              <button type="button" onClick={handleAddNcCode}>+ Ajouter</button>
            </div>
          </div>
        </div>

        {/* Criticité et volume */}
        <div className="form-section">
          <h2>⚡ Importance</h2>
          
          <div className="form-group">
            <label>Criticité du fournisseur</label>
            <div className="radio-group">
              {['Standard', 'Important', 'Critique'].map(level => (
                <label key={level} className={`radio-option ${formData.criticality === level ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="criticality"
                    value={level}
                    checked={formData.criticality === level}
                    onChange={handleInputChange}
                  />
                  {level === 'Critique' && '🔴 '}
                  {level === 'Important' && '🟠 '}
                  {level === 'Standard' && '🟢 '}
                  {level}
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="annual_volume">Volume annuel (€)</label>
            <input
              type="number"
              id="annual_volume"
              name="annual_volume"
              value={formData.annual_volume || ''}
              onChange={handleInputChange}
              placeholder="Ex: 2500000"
              min="0"
            />
          </div>
        </div>

        {/* Erreur */}
        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        {/* Message de validation */}
        {!isFormValid && (
          <div className="validation-message">
            ⚠️ Pour lancer l'analyse, veuillez remplir :
            <ul>
              {formData.name.trim() === '' && <li>Le nom du fournisseur</li>}
              {formData.country === '' && <li>Le pays</li>}
              {formData.materials.length === 0 && <li>Au moins une matière fournie</li>}
            </ul>
          </div>
        )}

        {/* Bouton submit */}
        <button 
          type="submit" 
          className={`submit-button ${isLoading ? 'loading' : ''} ${!isFormValid ? 'disabled' : ''}`}
          disabled={!isFormValid || isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Analyse en cours...
            </>
          ) : (
            '🔍 Analyser les risques'
          )}
        </button>
      </form>
    </div>
  );
};

export default SupplierAnalysis;
