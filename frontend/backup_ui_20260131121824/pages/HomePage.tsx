import React from 'react';
import './HomePage.css';

interface HomePageProps {
  onShowLogin: () => void;
  onShowRegister: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onShowLogin, onShowRegister }) => {
  return (
    <div className="home-page">
      <header className="home-header">
        <div className="home-logo-slot" aria-label="Emplacement logo">
          <div className="home-logo-placeholder" />
        </div>
        <nav className="home-nav">
          <a href="#comment" className="home-nav-link">comment</a>
          <a href="#blog" className="home-nav-link">Blog</a>
          <a href="#pricing" className="home-nav-link">Pricing</a>
          <button className="home-nav-button ghost" onClick={onShowLogin}>s'identifier</button>
          <button className="home-nav-button primary" onClick={onShowRegister}>s'inscrire</button>
        </nav>
      </header>

      <main className="home-hero">
        <div className="home-hero-left">
          <h1>
            Anticiper les risques.
            <br />
            Sécuriser ses
            <br />
            décisions.
          </h1>
          <p>
            Surveillez les évolutions réglementaires en temps réel et
            identifiez les risques liés à vos fournisseurs avant qu'ils
            n'impactent vos activités.
          </p>
          <div className="home-cta">
            <button className="home-cta-button primary" onClick={onShowRegister}>s'inscrire</button>
            <button className="home-cta-button ghost" onClick={onShowLogin}>s'identifier</button>
          </div>
        </div>

        <div className="home-hero-right">
          <div className="home-image-placeholder" aria-label="Emplacement image" />
        </div>
      </main>
    </div>
  );
};
