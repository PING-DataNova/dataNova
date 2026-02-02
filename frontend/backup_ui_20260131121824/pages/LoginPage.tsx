import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff } from 'lucide-react';
import { authService } from '../services/auth.service';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: (userType: 'juridique' | 'decisive', userData: any) => void;
  onShowRegister?: () => void;
  onShowHome?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onShowRegister, onShowHome }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Utilise authService qui appelle l'API backend
      const user = await authService.login({
        email,
        password,
      });

      // Connexion réussie
      onLogin(user.role, user);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Plateforme de veille réglementaire durable</h1>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <div className="input-wrapper">
              <User className="input-icon" />
              <input
                type="email"
                placeholder="juriste@hutchinson.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="login-input"
              />
            </div>
          </div>

          <div className="input-group">
            <div className="input-wrapper">
              <Lock className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="•••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="login-input"
              />
              <button
                type="button"
                className="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="login-button"
          >
            {loading ? 'Connexion...' : 'Connexion'}
          </button>

          <div className="login-footer">
            <a href="#" className="forgot-password">Mot de passe oublié ?</a>
            {onShowRegister && (
              <p className="register-link">
                Pas encore de compte ? <a href="#" onClick={(e) => { e.preventDefault(); onShowRegister(); }}>S'inscrire</a>
              </p>
            )}
            {onShowHome && (
              <p className="home-link">
                <a href="#" onClick={(e) => { e.preventDefault(); onShowHome(); }}>
                  Retour à l'accueil
                </a>
              </p>
            )}
          </div>
        </form>


      </div>

      <div className="login-background">
        <p>© Hutchinson 2026 - Tous droits réservés</p>
      </div>
    </div>
  );
};