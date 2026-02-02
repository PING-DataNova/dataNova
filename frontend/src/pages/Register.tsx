
import React, { useState } from 'react';
import { register as registerApi } from '../services/authService';

interface RegisterProps {
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard') => void;
}

const Register: React.FC<RegisterProps> = ({ onNavigate }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'juridique' | 'decisive'>('juridique');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name || !email || !password) {
      setError('Veuillez remplir tous les champs');
      return;
    }

    if (!acceptTerms) {
      setError('Veuillez accepter les conditions d\'utilisation');
      return;
    }

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    setIsLoading(true);
    try {
      await registerApi({ name, email, password, role });
      setSuccess(true);
      // Rediriger vers login après 2 secondes
      setTimeout(() => onNavigate('login'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'inscription');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6">
        <div className="bg-white p-12 rounded-[3rem] shadow-xl text-center max-w-md">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <h2 className="text-2xl font-black text-slate-900 mb-3">Compte créé !</h2>
          <p className="text-slate-500">Redirection vers la page de connexion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 selection:bg-lime-200">
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="w-full max-w-lg relative">
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 flex items-center space-x-2">
           <div className="w-6 h-6 bg-slate-900 rounded-lg"></div>
           <span className="font-black tracking-[0.3em] text-slate-900">HUTCHINSON</span>
        </div>

        <div className="bg-white p-12 rounded-[3rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] border border-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-lime-300 via-emerald-400 to-blue-400"></div>
          
          <div className="text-center mb-10">
            <h2 className="text-3xl font-black text-slate-900 mb-3 tracking-tight">Rejoignez l'élite.</h2>
            <p className="text-slate-500 font-medium">Anticipez les risques dès aujourd'hui.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium flex items-center space-x-2">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>{error}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Nom Complet</label>
                <input
                  type="text"
                  placeholder="Jean Dupont"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                  className="w-full px-5 py-3 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium disabled:opacity-50"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Rôle</label>
                <select 
                  value={role}
                  onChange={(e) => setRole(e.target.value as 'juridique' | 'decisive')}
                  disabled={isLoading}
                  className="w-full px-5 py-3 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium appearance-none cursor-pointer disabled:opacity-50"
                >
                  <option value="juridique">Analyste Juridique</option>
                  <option value="decisive">Décisionnaire</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Email Corporatif</label>
              <input
                type="email"
                placeholder="nom@hutchinson.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium disabled:opacity-50"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Mot de Passe</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium disabled:opacity-50"
                required
              />
            </div>

            <div className="flex items-center space-x-3 ml-1 py-2">
               <input 
                 type="checkbox" 
                 id="terms" 
                 checked={acceptTerms}
                 onChange={(e) => setAcceptTerms(e.target.checked)}
                 disabled={isLoading}
                 className="w-4 h-4 rounded text-lime-500 focus:ring-lime-500 border-slate-200" 
               />
               <label htmlFor="terms" className="text-xs text-slate-500 font-medium cursor-pointer">J'accepte les conditions d'utilisation et la politique de confidentialité.</label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-5 bg-lime-400 text-slate-950 font-black rounded-2xl hover:bg-slate-900 hover:text-white transition-all shadow-xl shadow-lime-100 uppercase tracking-[0.2em] text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  <span>Création en cours...</span>
                </>
              ) : (
                <span>Créer mon compte</span>
              )}
            </button>
          </form>

          <div className="mt-10 pt-8 border-t border-slate-50 text-center">
            <p className="text-slate-500 font-bold">
              Déjà un compte ?{' '}
              <button 
                onClick={() => onNavigate('login')} 
                className="text-slate-900 hover:text-blue-600 underline underline-offset-4 decoration-blue-300 decoration-2 transition-all"
              >
                Se connecter
              </button>
            </p>
          </div>
        </div>

        <button 
          onClick={() => onNavigate('landing')}
          className="mt-8 flex items-center space-x-2 text-slate-400 hover:text-slate-900 transition-colors mx-auto font-black text-xs uppercase tracking-widest"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          <span>Annuler et retourner</span>
        </button>
      </div>
    </div>
  );
};

export default Register;
