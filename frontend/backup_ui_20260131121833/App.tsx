
import React, { useState, useEffect } from 'react';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import { User } from './types';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'landing' | 'login' | 'register' | 'dashboard'>('landing');
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

  const navigateTo = (page: 'landing' | 'login' | 'register' | 'dashboard') => {
    setCurrentPage(page);
  };

  return (
    <div className="min-h-screen">
      {currentPage === 'landing' && <Landing onNavigate={navigateTo} />}
      {currentPage === 'login' && <Login onNavigate={navigateTo} onLogin={handleLogin} />}
      {currentPage === 'register' && <Register onNavigate={navigateTo} />}
      {currentPage === 'dashboard' && user && (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </div>
  );
};

export default App;
