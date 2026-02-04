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
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header avec flèche retour */}
      <header className="bg-white border-b border-slate-100 px-8 py-4 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <button 
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-xl transition-colors group"
            title="Retour au dashboard"
          >
            <svg className="w-6 h-6 text-slate-400 group-hover:text-slate-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-900 tracking-tight">Analyse Fournisseur</h1>
            <p className="text-xs text-slate-400">Évaluez les risques réglementaires et climatiques</p>
          </div>
        </div>
      </header>

      {/* Contenu principal */}
      <div className="max-w-4xl mx-auto px-8 py-10">
        <form onSubmit={handleSubmit} className="space-y-8">
          
          {/* Informations de base */}
          <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">Informations du fournisseur</h2>
            </div>
            
            <div className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Nom du fournisseur *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Ex: Thai Rubber Co."
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent transition-all"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Pays *
                  </label>
                  <select
                    name="country"
                    value={formData.country}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent transition-all"
                    required
                  >
                    <option value="">Sélectionner un pays</option>
                    {COUNTRIES.map(country => (
                      <option key={country} value={country}>{country}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Ville
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city || ''}
                    onChange={handleInputChange}
                    placeholder="Ex: Bangkok"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Latitude (optionnel)
                  </label>
                  <input
                    type="number"
                    name="latitude"
                    value={formData.latitude || ''}
                    onChange={handleInputChange}
                    placeholder="Ex: 13.7563"
                    step="0.0001"
                    min="-90"
                    max="90"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Longitude (optionnel)
                  </label>
                  <input
                    type="number"
                    name="longitude"
                    value={formData.longitude || ''}
                    onChange={handleInputChange}
                    placeholder="Ex: 100.5018"
                    step="0.0001"
                    min="-180"
                    max="180"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent transition-all"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Matières fournies */}
          <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">Matières fournies *</h2>
            </div>

            {/* Tags des matières */}
            <div className="flex flex-wrap gap-2 mb-4">
              {formData.materials.map(material => (
                <span key={material} className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                  {material}
                  <button 
                    type="button" 
                    onClick={() => handleRemoveMaterial(material)}
                    className="ml-1 hover:text-emerald-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            
            <div className="flex gap-3">
              <input
                type="text"
                value={newMaterial}
                onChange={(e) => setNewMaterial(e.target.value)}
                placeholder="Ajouter une matière"
                list="materials-list"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddMaterial();
                  }
                }}
                className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
              />
              <datalist id="materials-list">
                {COMMON_MATERIALS.map(m => (
                  <option key={m} value={m} />
                ))}
              </datalist>
              <button 
                type="button" 
                onClick={handleAddMaterial}
                className="px-5 py-3 bg-emerald-500 text-white font-bold rounded-xl hover:bg-emerald-600 transition-colors"
              >
                + Ajouter
              </button>
            </div>
          </div>

          {/* Codes NC */}
          <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">Codes NC (douaniers)</h2>
            </div>

            {/* Tags des codes */}
            <div className="flex flex-wrap gap-2 mb-4">
              {(formData.nc_codes || []).map(code => (
                <span key={code} className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium font-mono">
                  {code}
                  <button 
                    type="button" 
                    onClick={() => handleRemoveNcCode(code)}
                    className="ml-1 hover:text-blue-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            
            <div className="flex gap-3">
              <select
                value={newNcCode}
                onChange={(e) => setNewNcCode(e.target.value)}
                className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all"
              >
                <option value="">Sélectionner un code NC</option>
                {COMMON_NC_CODES.map(nc => (
                  <option key={nc.code} value={nc.code}>
                    {nc.code} - {nc.label}
                  </option>
                ))}
              </select>
              <button 
                type="button" 
                onClick={handleAddNcCode}
                className="px-5 py-3 bg-blue-500 text-white font-bold rounded-xl hover:bg-blue-600 transition-colors"
              >
                + Ajouter
              </button>
            </div>
          </div>

          {/* Criticité et volume */}
          <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-orange-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">Importance</h2>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                  Criticité du fournisseur
                </label>
                <div className="flex gap-3">
                  {['Standard', 'Important', 'Critique'].map(level => (
                    <label 
                      key={level} 
                      className={`flex-1 py-3 px-4 rounded-xl border-2 text-center cursor-pointer transition-all font-medium ${
                        formData.criticality === level 
                          ? level === 'Critique' 
                            ? 'border-red-500 bg-red-50 text-red-700' 
                            : level === 'Important'
                              ? 'border-orange-500 bg-orange-50 text-orange-700'
                              : 'border-slate-900 bg-slate-900 text-white'
                          : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="criticality"
                        value={level}
                        checked={formData.criticality === level}
                        onChange={handleInputChange}
                        className="sr-only"
                      />
                      {level}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Volume annuel (€)
                </label>
                <input
                  type="number"
                  name="annual_volume"
                  value={formData.annual_volume || ''}
                  onChange={handleInputChange}
                  placeholder="Ex: 2500000"
                  min="0"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition-all"
                />
              </div>
            </div>
          </div>

          {/* Erreur */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 font-medium">
              {error}
            </div>
          )}

          {/* Message de validation */}
          {!isFormValid && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-amber-700">
              <p className="font-medium mb-2">Pour lancer l'analyse, veuillez remplir :</p>
              <ul className="list-disc list-inside text-sm space-y-1">
                {formData.name.trim() === '' && <li>Le nom du fournisseur</li>}
                {formData.country === '' && <li>Le pays</li>}
                {formData.materials.length === 0 && <li>Au moins une matière fournie</li>}
              </ul>
            </div>
          )}

          {/* Bouton submit */}
          <button 
            type="submit" 
            disabled={!isFormValid || isLoading}
            className={`w-full py-5 rounded-2xl font-black text-lg uppercase tracking-wider transition-all flex items-center justify-center gap-3 ${
              !isFormValid || isLoading
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-lime-400 to-emerald-500 text-slate-900 hover:from-lime-300 hover:to-emerald-400 hover:scale-[1.02] shadow-lg shadow-lime-500/30'
            }`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyse en cours...
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                </svg>
                Analyser les risques
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SupplierAnalysis;
