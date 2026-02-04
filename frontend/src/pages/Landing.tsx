
import React from 'react';

interface LandingProps {
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard') => void;
}

const Landing: React.FC<LandingProps> = ({ onNavigate }) => {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 flex flex-col selection:bg-lime-400 selection:text-slate-900">
      {/* Background Orbs for uniqueness */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-lime-500/10 blur-[120px] rounded-full animate-pulse"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Header */}
      <nav className="relative z-20 p-8 flex justify-between items-center max-w-7xl mx-auto w-full">
        <div className="flex items-center group cursor-pointer" onClick={() => onNavigate('landing')}>
          <img src="/hutchinson-logo-white.svg" alt="Hutchinson" className="h-8 object-contain" />
        </div>
        
        <div className="hidden lg:flex space-x-12 text-sm font-bold uppercase tracking-widest text-slate-400">
          <a href="#" className="hover:text-lime-400 transition-colors">Expertise</a>
          <a href="#" className="hover:text-lime-400 transition-colors">Ressources</a>
          <a href="#" className="hover:text-lime-400 transition-colors">Impact</a>
        </div>

        <div className="flex items-center space-x-6">
          <button 
            onClick={() => onNavigate('login')}
            className="text-sm font-bold uppercase tracking-widest hover:text-lime-400 transition-colors"
          >
            S'identifier
          </button>
          <button 
            onClick={() => onNavigate('register')}
            className="px-8 py-3 rounded-full bg-lime-400 text-slate-950 font-black text-sm uppercase tracking-widest hover:bg-white hover:scale-105 transition-all shadow-[0_0_20px_rgba(163,230,53,0.3)]"
          >
            Créer mon compte
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 flex-grow flex items-center px-8">
        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-20 items-center py-20">
          <div className="space-y-10">
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-full text-xs font-bold uppercase tracking-widest text-lime-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-lime-500"></span>
              </span>
              <span>Propulsé par IA Agentique</span>
            </div>
            
            <h1 className="text-6xl md:text-8xl font-black leading-none tracking-tight">
              MAÎTRISEZ LE <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-lime-400 via-emerald-400 to-blue-400">PRÉSENT</span>,<br />
              DÉFINISSEZ LE FUTUR.
            </h1>

            <p className="text-slate-400 text-xl max-w-xl leading-relaxed font-medium">
              Plateforme de vigilance pour anticiper les risques réglementaires, climatiques et géopolitiques. Prenez des décisions éclairées grâce à nos insights prédictifs.
            </p>

            <div className="flex flex-wrap gap-6">
              <button 
                onClick={() => onNavigate('register')}
                className="group relative px-10 py-5 rounded-2xl bg-white text-slate-950 font-black text-lg transition-all hover:pr-14 overflow-hidden"
              >
                <span className="relative z-10">Démarrer l'audit</span>
                <span className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                </span>
              </button>
            </div>
          </div>

          <div className="hidden lg:block relative">
            <div className="absolute -inset-10 bg-gradient-to-tr from-lime-400/20 to-blue-400/20 blur-[100px] rounded-full"></div>
            <div className="relative bg-slate-900/40 border border-slate-800 rounded-[3rem] p-4 backdrop-blur-xl shadow-2xl">
              <div className="bg-[#020617] rounded-[2.5rem] overflow-hidden aspect-[4/5] p-8 flex flex-col">
                <div className="flex justify-between items-center mb-10">
                  <div className="space-y-1">
                    <div className="w-24 h-2 bg-slate-800 rounded"></div>
                    <div className="w-16 h-2 bg-slate-900 rounded"></div>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-lime-400/10 flex items-center justify-center">
                    <div className="w-4 h-4 bg-lime-400 rounded-sm"></div>
                  </div>
                </div>
                
                <div className="space-y-6">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800/50 flex items-center justify-between transform transition-all hover:scale-105 hover:bg-slate-800/50">
                      <div className="flex items-center space-x-4">
                        <div className={`w-3 h-3 rounded-full ${i === 1 ? 'bg-red-400' : i === 2 ? 'bg-amber-400' : 'bg-lime-400'}`}></div>
                        <div className="space-y-2">
                          <div className="w-32 h-2 bg-slate-700 rounded"></div>
                          <div className="w-20 h-1 bg-slate-800 rounded"></div>
                        </div>
                      </div>
                      <div className="w-8 h-4 bg-slate-800 rounded"></div>
                    </div>
                  ))}
                </div>

                <div className="mt-auto bg-lime-400 p-6 rounded-3xl">
                   <div className="flex justify-between items-end">
                      <div className="space-y-1">
                        <p className="text-slate-900 text-xs font-bold uppercase tracking-tighter">Indice de Risque Global</p>
                        <p className="text-slate-950 text-4xl font-black">74.2</p>
                      </div>
                      <div className="h-10 w-24 flex items-end space-x-1">
                        {[4,7,5,8,9].map((h, i) => (
                          <div key={i} className="bg-slate-950/20 w-full rounded-t-sm" style={{ height: `${h}0%` }}></div>
                        ))}
                      </div>
                   </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="p-10 border-t border-slate-900/50 flex flex-col md:flex-row justify-between items-center text-slate-500 text-xs font-bold uppercase tracking-widest gap-4">
        <div className="flex space-x-8">
          <a href="#" className="hover:text-white">Confidentialité</a>
          <a href="#" className="hover:text-white">Sécurité</a>
          <a href="#" className="hover:text-white">Conformité</a>
        </div>
        <p>© 2026 HUTCHINSON STRATEGIC INTEL</p>
      </footer>
    </div>
  );
};

export default Landing;
