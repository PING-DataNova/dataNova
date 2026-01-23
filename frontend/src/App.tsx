import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { LegalTeamPage } from './pages/LegalTeamPage';
import { DecisionDashboard } from './pages/DecisionDashboard';
import { User } from './types';
import './App.css';

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const handleLogin = (userType: 'juridique' | 'decisive', userData: any) => {
    const user: User = {
      id: userData.id,
      name: userData.name,
      role: userType,
      avatar: userData.avatar
    };
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  // Si pas connecté, afficher la page de connexion
  if (!currentUser) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Redirection selon le rôle
  return (
    <div className="app">
      {currentUser.role === 'juridique' ? (
        <LegalTeamPage />
      ) : (
        <DecisionDashboard />
      )}
    </div>
  );
}

export default App;