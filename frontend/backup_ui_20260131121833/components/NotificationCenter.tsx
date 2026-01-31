
import React, { useState } from 'react';
import { Notification } from '../types';

interface NotificationCenterProps {
  notifications: Notification[];
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ notifications }) => {
  const [isOpen, setIsOpen] = useState(false);
  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`relative p-3 rounded-2xl transition-all duration-300 group ${isOpen ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}
      >
        <svg className="w-6 h-6 transition-transform group-hover:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-2 right-2 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500 text-[8px] font-black text-white items-center justify-center border-2 border-white">
              {unreadCount}
            </span>
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)}></div>
          <div className="absolute right-0 mt-4 w-[22rem] bg-white rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-slate-100 z-50 overflow-hidden transform animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="px-6 py-5 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
              <h3 className="font-black text-slate-900 uppercase tracking-widest text-xs">Vigilance en temps réel</h3>
              <span className="text-[10px] font-black bg-slate-900 text-white px-2 py-0.5 rounded-full">{notifications.length}</span>
            </div>
            
            <div className="max-h-[450px] overflow-y-auto custom-scrollbar">
              {notifications.length === 0 ? (
                <div className="p-12 text-center">
                   <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                   </div>
                   <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">Aucune alerte</p>
                </div>
              ) : (
                notifications.map(notif => (
                  <div key={notif.id} className="p-5 border-b border-slate-50 hover:bg-slate-50/80 cursor-pointer transition-all flex space-x-4 items-start group">
                    <div className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${
                      notif.category === 'Climat' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 
                      notif.category === 'Géopolitique' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 
                      'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]'
                    }`}></div>
                    <div className="space-y-1">
                      <div className="flex justify-between items-start">
                        <h4 className="text-sm font-black text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">{notif.title}</h4>
                      </div>
                      <p className="text-xs text-slate-500 font-medium leading-relaxed">{notif.description}</p>
                      <div className="flex items-center space-x-2 pt-1">
                         <span className="text-[8px] font-black uppercase tracking-widest text-slate-300">{notif.category}</span>
                         <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
                         <span className="text-[8px] font-black text-slate-300 uppercase tracking-widest">Il y a 2m</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <button className="w-full py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-slate-900 hover:bg-slate-50 transition-all border-t border-slate-50">
              Tout marquer comme lu
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationCenter;
