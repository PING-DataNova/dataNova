
import React, { useState, useEffect } from 'react';
import { User, RiskData, Notification } from '../types';
import { MOCK_RISKS } from '../mockData';
import RiskTable from '../components/RiskTable';
import NotificationCenter from '../components/NotificationCenter';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, AreaChart, Area } from 'recharts';

interface DashboardProps {
  user: User;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState<'Réglementations' | 'Climat' | 'Géopolitique'>('Réglementations');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showRealTimeToast, setShowRealTimeToast] = useState<string | null>(null);
  
  // Real-time notification simulation
  useEffect(() => {
    const timers = [
      setTimeout(() => triggerNewRiskNotification('Climat', "Alerte Sécheresse: Impact Supply Chain Iberia"), 3000),
      setTimeout(() => triggerNewRiskNotification('Géopolitique', "Sanctions US: Nouvelle liste d'entités restreintes"), 8000),
      setTimeout(() => triggerNewRiskNotification('Réglementations', "Directive IA: Publication du journal officiel"), 15000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const triggerNewRiskNotification = (category: string, title: string) => {
    const newNotif: Notification = {
      id: Math.random().toString(36).substr(2, 9),
      title: title,
      description: `Un nouveau risque de type ${category} vient d'être enregistré dans la base.`,
      category: category,
      timestamp: new Date(),
      isRead: false
    };
    setNotifications(prev => [newNotif, ...prev]);
    setShowRealTimeToast(title);
    setTimeout(() => setShowRealTimeToast(null), 5000);
  };

  const filteredRisks = MOCK_RISKS.filter(r => r.category === activeTab);

  // Advanced Stats Data
  const impactStats = [
    { name: 'Faible', value: 12, color: '#10B981' },
    { name: 'Moyen', value: 24, color: '#F59E0B' },
    { name: 'Elevé', value: 8, color: '#F97316' },
    { name: 'Critique', value: 5, color: '#EF4444' },
  ];

  const trendData = [
    { name: 'Jan', val: 40 }, { name: 'Feb', val: 30 }, { name: 'Mar', val: 45 },
    { name: 'Apr', val: 60 }, { name: 'May', val: 55 }, { name: 'Jun', val: 80 }
  ];

  return (
    <div className="flex h-screen bg-[#F8FAFC] font-sans selection:bg-lime-200">
      
      {/* Toast Notification Pop-up */}
      {showRealTimeToast && (
        <div className="fixed top-8 right-8 z-[100] animate-bounce">
           <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-2xl flex items-center space-x-4 border border-lime-400/30 backdrop-blur-xl">
              <div className="w-10 h-10 bg-lime-400 rounded-xl flex items-center justify-center">
                 <svg className="w-6 h-6 text-slate-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-lime-400">Nouveau Risque</p>
                 <p className="text-sm font-bold">{showRealTimeToast}</p>
              </div>
              <button onClick={() => setShowRealTimeToast(null)} className="text-slate-500 hover:text-white transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
           </div>
        </div>
      )}

      {/* Modern Slim Sidebar */}
      <aside className="w-20 lg:w-72 bg-slate-950 text-slate-300 flex flex-col transition-all duration-300">
        <div className="p-6 flex justify-center lg:justify-start items-center space-x-3 mb-10">
          <div className="w-10 h-10 bg-lime-400 rounded-xl flex-shrink-0 flex items-center justify-center">
            <div className="w-4 h-4 bg-slate-950 rounded-sm"></div>
          </div>
          <span className="hidden lg:block font-black text-xl tracking-tighter text-white">VIGILANCE</span>
        </div>

        <nav className="flex-grow px-4 space-y-3">
          {(['Réglementations', 'Climat', 'Géopolitique'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full group relative flex items-center lg:space-x-4 p-3 lg:px-5 lg:py-4 rounded-2xl transition-all duration-300 ${
                activeTab === tab 
                  ? 'bg-white text-slate-900 shadow-xl shadow-lime-900/40' 
                  : 'hover:bg-slate-900 text-slate-500 hover:text-white'
              }`}
            >
              <div className="flex-shrink-0">
                {tab === 'Réglementations' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>}
                {tab === 'Climat' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"/></svg>}
                {tab === 'Géopolitique' && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9h18"/></svg>}
              </div>
              <span className="hidden lg:block font-bold text-sm tracking-tight">{tab}</span>
              {activeTab === tab && <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-lime-400 rounded-l-full hidden lg:block"></div>}
            </button>
          ))}
        </nav>

        <div className="p-6">
           <div className="hidden lg:block bg-slate-900 p-4 rounded-2xl mb-6">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Utilisateur</p>
              <div className="flex items-center space-x-3">
                 <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-black text-xs text-white">JD</div>
                 <div className="overflow-hidden">
                    <p className="text-sm font-bold text-white truncate">{user.fullName}</p>
                    <p className="text-[10px] text-lime-400 font-bold uppercase">{user.role}</p>
                 </div>
              </div>
           </div>
           <button 
             onClick={onLogout}
             className="w-full flex items-center lg:space-x-3 p-3 lg:px-4 text-slate-500 hover:text-red-400 transition-colors"
           >
             <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
             <span className="hidden lg:block text-xs font-black uppercase tracking-widest">Logout</span>
           </button>
        </div>
      </aside>

      {/* Dashboard Main View */}
      <main className="flex-grow flex flex-col overflow-hidden">
        {/* Header Navigation */}
        <header className="px-10 py-6 flex justify-between items-center bg-white border-b border-slate-100">
          <div>
             <div className="flex items-center space-x-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">
                <span>Database</span>
                <span>/</span>
                <span className="text-lime-500">{activeTab}</span>
             </div>
             <h1 className="text-3xl font-black text-slate-900 tracking-tighter">Insights Globaux</h1>
          </div>
          <div className="flex items-center space-x-8">
             <div className="hidden md:flex bg-slate-50 px-4 py-2 rounded-xl border border-slate-100 items-center">
                <svg className="w-4 h-4 text-slate-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <input type="text" placeholder="Rechercher un dossier..." className="bg-transparent text-sm font-medium outline-none w-48" />
             </div>
             <NotificationCenter notifications={notifications} />
          </div>
        </header>

        {/* Dynamic Content */}
        <div className="flex-grow overflow-y-auto p-10 space-y-10 custom-scrollbar">
          
          {/* Key Stats Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-4 bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
               <div className="flex justify-between items-start mb-6">
                  <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Gravité Moyenne</h3>
                  <span className="px-2 py-1 bg-red-100 text-red-600 rounded text-[10px] font-black uppercase">Attention</span>
               </div>
               <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={impactStats} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={8} dataKey="value">
                        {impactStats.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)' }} />
                    </PieChart>
                  </ResponsiveContainer>
               </div>
               <div className="flex flex-wrap gap-4 mt-6 justify-center">
                  {impactStats.map(s => (
                    <div key={s.name} className="flex items-center space-x-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }}></div>
                      <span className="text-[10px] font-black text-slate-500 uppercase">{s.name}</span>
                    </div>
                  ))}
               </div>
            </div>

            <div className="lg:col-span-8 bg-slate-900 p-8 rounded-[2.5rem] shadow-xl relative overflow-hidden">
               <div className="relative z-10 flex flex-col h-full">
                  <div className="flex justify-between items-start mb-8">
                    <div>
                      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Tendances d'Analyse</h3>
                      <p className="text-2xl font-black text-white">+28% de risques détectés <span className="text-lime-400">ce mois</span></p>
                    </div>
                    <div className="flex space-x-2">
                       {['7d', '30d', '90d'].map(d => (
                         <button key={d} className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${d === '30d' ? 'bg-lime-400 text-slate-950' : 'text-slate-500 hover:text-white'}`}>{d}</button>
                       ))}
                    </div>
                  </div>
                  <div className="flex-grow">
                    <ResponsiveContainer width="100%" height="100%">
                       <AreaChart data={trendData}>
                          <defs>
                            <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#A3E635" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#A3E635" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <Tooltip contentStyle={{ backgroundColor: '#0F172A', border: 'none', borderRadius: '12px', color: '#fff' }} />
                          <Area type="monotone" dataKey="val" stroke="#A3E635" strokeWidth={4} fillOpacity={1} fill="url(#colorVal)" />
                       </AreaChart>
                    </ResponsiveContainer>
                  </div>
               </div>
            </div>
          </div>

          {/* List Section */}
          <div className="space-y-6">
             <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 tracking-tighter">Inventaire des Menaces: {activeTab}</h2>
                  <p className="text-slate-400 text-sm font-medium">Données actualisées en temps réel par notre moteur de veille.</p>
                </div>
                <div className="flex items-center space-x-3">
                   <button className="px-6 py-3 bg-white border border-slate-200 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50 transition-colors">Filtrer</button>
                   <button className="px-6 py-3 bg-slate-900 text-white rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center space-x-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                      <span>Rapport PDF</span>
                   </button>
                </div>
             </div>

             <div className="group">
                <RiskTable risks={filteredRisks} />
             </div>
          </div>

          {/* Activity Feed / Last Photo Data Context */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
             {[
               { label: 'Risques Actifs', val: '42', color: 'text-blue-600', bg: 'bg-blue-50' },
               { label: 'Niveau d\'Urgence', val: 'Elevé', color: 'text-orange-600', bg: 'bg-orange-50' },
               { label: 'Recommandations', val: '12', color: 'text-emerald-600', bg: 'bg-emerald-50' },
               { label: 'Temps Réponse', val: '2.4s', color: 'text-purple-600', bg: 'bg-purple-50' }
             ].map((stat, i) => (
               <div key={i} className={`${stat.bg} p-6 rounded-[2rem] border border-white/50 shadow-sm flex flex-col justify-between h-32 transform transition-transform hover:-translate-y-1`}>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{stat.label}</p>
                  <p className={`text-3xl font-black ${stat.color}`}>{stat.val}</p>
               </div>
             ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
