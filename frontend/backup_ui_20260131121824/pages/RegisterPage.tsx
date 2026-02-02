import React, { useState } from 'react';
import { authService } from '../services/auth.service';
import './RegisterPage.css';

interface RegisterPageProps {
  onRegisterSuccess: () => void;
  onShowHome?: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onRegisterSuccess, onShowHome }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    role: 'juridique' as 'juridique' | 'decisive'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validation email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Veuillez entrer une adresse email valide');
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      setLoading(false);
      return;
    }

    try {
      await authService.register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        role: formData.role
      });

      setSuccess(true);
      setTimeout(() => {
        onRegisterSuccess();
      }, 2000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="register-container">
        <div className="register-card">
          <h1 className="register-title">Inscription réussie !</h1>
          <p className="register-success">Redirection vers la page de connexion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="register-container">
      <div className="register-card">
        <h1 className="register-title">Créer un compte</h1>

        <form onSubmit={handleSubmit} className="register-form">
          {error && <div className="register-error">{error}</div>}

          <div className="register-field">
            <label className="register-label">Email professionnel</label>
            <input
              type="email"
              className="register-input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={loading}
              placeholder="nom@entreprise.com"
            />
          </div>

          <div className="register-field">
            <label className="register-label">Nom complet</label>
            <input
              type="text"
              className="register-input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              disabled={loading}
              placeholder="Prénom Nom"
            />
          </div>

          <div className="register-field">
            <label className="register-label">Rôle</label>
            <select
              className="register-select"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as 'juridique' | 'decisive' })}
              required
              disabled={loading}
            >
              <option value="juridique">Admin</option>
              <option value="decisive">Consultant</option>
            </select>
          </div>

          <div className="register-field">
            <label className="register-label">Mot de passe</label>
            <input
              type="password"
              className="register-input"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={loading}
              placeholder="Minimum 6 caractères"
              minLength={6}
            />
          </div>

          <div className="register-field">
            <label className="register-label">Confirmer le mot de passe</label>
            <input
              type="password"
              className="register-input"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              required
              disabled={loading}
              placeholder="Confirmez votre mot de passe"
              minLength={6}
            />
          </div>

          <button type="submit" className="register-button" disabled={loading}>
            {loading ? 'Création en cours...' : 'Créer mon compte'}
          </button>
        </form>

        <div className="register-footer">
          Déjà un compte ? <a href="#" onClick={(e) => { e.preventDefault(); onRegisterSuccess(); }}>Se connecter</a>
          {onShowHome && (
            <div className="register-home-link">
              <a href="#" onClick={(e) => { e.preventDefault(); onShowHome(); }}>Retour à l'accueil</a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
