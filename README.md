# Frontend PING - Équipe Juridique

## Connexion à l'Application

### Profils de Test

**Interface Juridique :**
- Email : `juriste@hutchinson.com` 
- Mot de passe : n'importe lequel (mode démo)

**Dashboard Décideur :**
- Email : `decideur@hutchinson.com`
- Mot de passe : n'importe lequel (mode démo)

### Démarrage

```bash
npm install
npm run dev
```

Accès : http://localhost:3005

## Connexion Frontend/Backend

### Configuration pour les développeurs Backend

Le frontend communique avec votre API via ces endpoints :

#### Endpoints Réglementations
```
GET    /api/regulations                    # Liste des réglementations
PUT    /api/regulations/:id/status         # Mettre à jour le statut
GET    /api/regulations/:id                # Détails d'une réglementation
GET    /api/regulations/stats              # Statistiques
```

#### Endpoints Authentification (optionnel)
```
POST   /api/auth/login                     # Connexion
POST   /api/auth/logout                    # Déconnexion
GET    /api/auth/me                        # Utilisateur actuel
```

### Structure des données attendues

#### Regulation Object
```typescript
interface Regulation {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'validated' | 'rejected' | 'to-review';
  type: string;
  dateCreated: Date;
  reference?: string;
}
```

#### API Response Format
```typescript
// GET /api/regulations
{
  "regulations": Regulation[],
  "total": number,
  "page": number,
  "limit": number
}

// PUT /api/regulations/:id/status
{
  "status": "validated" | "rejected" | "to-review",
  "comment": string (optionnel)
}
```

### Configuration du Frontend

1. **Copiez le fichier d'environnement :**
   ```bash
   cp .env.example .env.local
   ```

2. **Modifiez `.env.local` avec l'URL de votre backend :**
   ```
   VITE_API_BASE_URL=http://localhost:VOTRE_PORT/api
   ```

3. **Démarrez le frontend :**
   ```bash
   npm install
   npm run dev
   ```

### CORS Configuration

Pour éviter les erreurs CORS, configurez votre backend pour accepter les requêtes depuis :
- `http://localhost:3000` (dev frontend)
- `http://localhost:3005` (si port 3000 occupé)

#### Exemple Express.js :
```javascript
const cors = require('cors');
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3005'],
  credentials: true
}));
```

#### Exemple FastAPI (Python) :
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Tests et Debuggage

- **Activer les logs** : `VITE_DEBUG=true` dans `.env.local`
- **Tester les endpoints** : Utilisez Postman ou curl
- **Vérifier la console** : F12 → Console pour voir les requêtes API

### Contact

Frontend: [Votre nom]
Backend: [Noms de vos collègues]