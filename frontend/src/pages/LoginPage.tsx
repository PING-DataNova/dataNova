import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff } from 'lucide-react';
import { authService } from '../services/auth.service';
import { config } from '../config/app.config';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: (userType: 'juridique' | 'decisive', userData: any) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
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
      // Utilise authService qui gère mock ou API selon la config
      const response = await authService.login({
        email,
        password,
      });

      // Connexion réussie
      onLogin(response.user.role, response.user);
      
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
          <div className="logo-container">
            <div className="logo">G</div>
          </div>
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
          </div>
        </form>

        <div className="demo-info">
          <p><strong>Mode: {config.mode.toUpperCase()}</strong></p>
          {config.isMockMode() && (
            <>
              <p>• juriste@hutchinson.com → Interface Juridique</p>
              <p>• decideur@hutchinson.com → Dashboard Décideur</p>
            </>
          )}
          {config.isApiMode() && (
            <p>• Connecté au backend: {config.apiUrl}</p>
          )}
        </div>
      </div>

      <div className="login-background">
        <p>© Hutchinson 2026 - Tous droits réservés</p>
      </div>
    </div>
  );
};