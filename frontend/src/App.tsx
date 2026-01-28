import { useState } from 'react';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { LegalTeamPage } from './pages/LegalTeamPage';
import { DecisionDashboard } from './pages/DecisionDashboard';
import { User } from './types';
import { authService } from './services/auth.service';
import './App.css';

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    // Restaurer l'utilisateur depuis localStorage au démarrage
    const savedUser = authService.getUser();
    if (savedUser && authService.isAuthenticated()) {
      return {
        id: savedUser.id,
        name: savedUser.name,
        role: savedUser.role as 'juridique' | 'decisive',
        avatar: undefined
      };
    }
    return null;
  });
  const [showRegister, setShowRegister] = useState(false);

  const handleLogin = (userType: 'juridique' | 'decisive', userData: any) => {
    const user: User = {
      id: userData.id,
      name: userData.name,
      role: userType,
      avatar: userData.avatar
    };
    setCurrentUser(user);
  };

  // Si pas connecté, afficher la page de connexion ou inscription
  if (!currentUser) {
    if (showRegister) {
      return <RegisterPage onRegisterSuccess={() => setShowRegister(false)} />;
    }
    return <LoginPage onLogin={handleLogin} onShowRegister={() => setShowRegister(true)} />;
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