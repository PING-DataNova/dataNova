import { useState } from 'react';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { LegalTeamPage } from './pages/LegalTeamPage';
import { DecisionDashboard } from './pages/DecisionDashboard';
import { User } from './types';
import { authService } from './services/auth.service';
import { UnifiedDashboard } from './pages/UnifiedDashboard';
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
  const [authView, setAuthView] = useState<'home' | 'login' | 'register'>('home');

  const handleLogin = (userType: 'juridique' | 'decisive', userData: any) => {
    const user: User = {
      id: userData.id,
      name: userData.name,
      role: userType,
      avatar: userData.avatar
    };
    setCurrentUser(user);
  };

  // Si pas connecté, afficher la page d'accueil ou l'authentification
  if (!currentUser) {
    if (authView === 'register') {
      return (
        <RegisterPage
          onRegisterSuccess={() => setAuthView('login')}
          onShowHome={() => setAuthView('home')}
        />
      );
    }
    if (authView === 'login') {
      return (
        <LoginPage
          onLogin={handleLogin}
          onShowRegister={() => setAuthView('register')}
          onShowHome={() => setAuthView('home')}
        />
      );
    }
    return (
      <HomePage
        onShowLogin={() => setAuthView('login')}
        onShowRegister={() => setAuthView('register')}
      />
    );
  }

  // Interface unifiée pour le persona principal (visuel uniquement)
  return (
    <div className="app">
      <UnifiedDashboard />
    </div>
  );
}

export default App;