
import React, { useState } from 'react';

interface RegisterProps {
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard') => void;
}

const Register: React.FC<RegisterProps> = ({ onNavigate }) => {
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

          <form className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Nom Complet</label>
                <input
                  type="text"
                  placeholder="Jean Dupont"
                  className="w-full px-5 py-3 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Spécialité</label>
                <select className="w-full px-5 py-3 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium appearance-none cursor-pointer">
                  <option>Juridique</option>
                  <option>Environnement</option>
                  <option>Géopolitique</option>
                  <option>Supply Chain</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Email Corporatif</label>
              <input
                type="email"
                placeholder="nom@hutchinson.com"
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Mot de Passe</label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-lime-400/20 focus:bg-white transition-all text-slate-900 font-medium"
              />
            </div>

            <div className="flex items-center space-x-3 ml-1 py-2">
               <input type="checkbox" id="terms" className="w-4 h-4 rounded text-lime-500 focus:ring-lime-500 border-slate-200" />
               <label htmlFor="terms" className="text-xs text-slate-500 font-medium cursor-pointer">J'accepte les conditions d'utilisation et la politique de confidentialité.</label>
            </div>

            <button
              type="button"
              className="w-full py-5 bg-lime-400 text-slate-950 font-black rounded-2xl hover:bg-slate-900 hover:text-white transition-all shadow-xl shadow-lime-100 uppercase tracking-[0.2em] text-sm"
            >
              Créer mon compte
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
