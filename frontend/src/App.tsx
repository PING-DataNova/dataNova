
import React, { useState, useEffect } from 'react';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import AgentDashboard from './pages/AgentDashboard';
import SupplierAnalysis from './pages/SupplierAnalysis';
import AdminPanel from './pages/AdminPanel';
import { User } from './types';

type PageType = 'landing' | 'login' | 'register' | 'dashboard' | 'agent' | 'supplier-analysis' | 'admin';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('landing');
  const [user, setUser] = useState<User | null>(null);

  // Persistence logic (simulated)
  useEffect(() => {
    const savedUser = localStorage.getItem('hutchinson_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setCurrentPage('dashboard');
    }
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
    localStorage.setItem('hutchinson_user', JSON.stringify(userData));
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('hutchinson_user');
    setCurrentPage('landing');
  };

  const navigateTo = (page: PageType) => {
    setCurrentPage(page);
  };

  return (
    <div className="min-h-screen">
      {currentPage === 'landing' && <Landing onNavigate={navigateTo} />}
      {currentPage === 'login' && <Login onNavigate={navigateTo} onLogin={handleLogin} />}
      {currentPage === 'register' && <Register onNavigate={navigateTo} />}
      {currentPage === 'dashboard' && user && (
        <Dashboard user={user} onLogout={handleLogout} onNavigate={navigateTo} />
      )}
      {currentPage === 'agent' && user && (
        <AgentDashboard user={user} onNavigate={navigateTo} />
      )}
      {currentPage === 'supplier-analysis' && user && (
        <SupplierAnalysis onBack={() => setCurrentPage('dashboard')} />
      )}
      {currentPage === 'admin' && user && (
        <AdminPanel onBack={() => setCurrentPage('dashboard')} />
      )}
    </div>
  );
};

export default App;
