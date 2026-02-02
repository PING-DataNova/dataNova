
import React, { useState } from 'react';
import { User } from '../types';
import { login as loginApi, saveToken } from '../services/authService';

interface LoginProps {
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard') => void;
  onLogin: (user: User) => void;
}

const Login: React.FC<LoginProps> = ({ onNavigate, onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!email || !password) {
      setError('Veuillez remplir tous les champs');
      return;
    }

    setIsLoading(true);
    try {
      const response = await loginApi({ email, password });
      
      // Sauvegarder le token
      saveToken(response.token);
      
      // Convertir vers le type User du frontend
      const user: User = {
        email: response.user.email,
        fullName: response.user.name,
        role: response.user.role === 'juridique' ? 'Analyste Juridique' : 'Décisionnaire'
      };
      
      onLogin(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 selection:bg-lime-200">
      {/* Abstract background subtle pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="w-full max-w-lg relative">
        {/* Branding decoration */}
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 flex items-center space-x-2">
           <div className="w-6 h-6 bg-slate-900 rounded-lg"></div>
           <span className="font-black tracking-[0.3em] text-slate-900">HUTCHINSON</span>
        </div>

        <div className="bg-white p-12 rounded-[3rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] border border-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-lime-300 via-emerald-400 to-blue-400"></div>
          
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-slate-900 mb-3 tracking-tight">Ravi de vous revoir.</h2>
            <p className="text-slate-500 font-medium">Accédez à votre centre de veille stratégique.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium flex items-center space-x-2">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-slate-400 ml-1">Email Professionnel</label>
              <input
                type="email"
                placeholder="analyste@hutchinson.com"
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-xs font-black uppercase tracking-widest text-slate-400">Mot de passe</label>
                <button type="button" className="text-[10px] font-black uppercase tracking-widest text-blue-600 hover:text-blue-800">Oublié ?</button>
              </div>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-5 bg-slate-900 text-white font-black rounded-2xl hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 uppercase tracking-[0.2em] text-sm flex items-center justify-center space-x-2 group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  <span>Connexion en cours...</span>
                </>
              ) : (
                <>
                  <span>Authentification</span>
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                </>
              )}
            </button>
          </form>

          <div className="mt-12 pt-8 border-t border-slate-50 text-center">
            <p className="text-slate-500 font-bold">
              Nouveau sur la plateforme ?{' '}
              <button 
                onClick={() => onNavigate('register')} 
                className="text-slate-900 hover:text-lime-500 underline underline-offset-4 decoration-lime-300 decoration-2 transition-all"
              >
                Créer son compte
              </button>
            </p>
          </div>
        </div>

        <button 
          onClick={() => onNavigate('landing')}
          className="mt-8 flex items-center space-x-2 text-slate-400 hover:text-slate-900 transition-colors mx-auto font-black text-xs uppercase tracking-widest"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          <span>Retour à l'accueil</span>
        </button>
      </div>
    </div>
  );
};

export default Login;
