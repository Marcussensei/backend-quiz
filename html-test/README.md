# 🧪 Application Web de Test - API Quiz Backend

Une interface web simple pour tester tous les endpoints de l'API Quiz Backend.

## 🚀 Démarrage rapide

1. **Démarrer le serveur backend :**
   ```bash
   cd /d/quiz-backend
   uvicorn app.main:app --reload
   ```

2. **Ouvrir l'application de test :**
   - Ouvrir `index.html` dans votre navigateur web
   - Ou utiliser un serveur local : `python -m http.server 8080` puis aller sur `http://localhost:8080`
## � Configuration d'Authentification

### Cookies HTTP-Only
L'application utilise des cookies HTTP-only pour l'authentification JWT. La configuration actuelle est optimisée pour le développement :

- **SameSite**: `None` (permet cross-origin en développement)
- **Secure**: `False` (HTTP en développement)
- **HttpOnly**: `True` (sécurisé contre XSS)

### ⚠️ Configuration Production
En production avec HTTPS, modifiez dans `app/api/router.py` :

```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    max_age=1800,
    expires=1800,
    secure=True,  # 🔒 True en production
    samesite="strict"  # 🔒 Strict en production
)
```

### 🧪 Tests Automatisés
- `test_auth_flow.py` : Test du flux d'authentification
- `test_html_auth.py` : Test depuis l'app HTML
- `test_cors.py` : Validation CORS

## �🔧 Configuration CORS

**Important :** Le serveur FastAPI est maintenant configuré avec CORS pour permettre les requêtes depuis les applications frontend de développement.

### Origines autorisées :
- `http://localhost:3000` (React)
- `http://localhost:5500` (Live Server VS Code)
- `http://localhost:8080` (Autres serveurs)
- `http://localhost:5173` (Vite)
- Et leurs équivalents `127.0.0.1`

### Test CORS :
Ouvrez `test-cors.html` dans votre navigateur pour vérifier que CORS fonctionne.

### Problèmes courants :
- **Erreur "CORS blocked"** : Redémarrez le serveur FastAPI
- **Cookies non envoyés** : Assurez-vous d'utiliser `http://` (pas `file://`)
- **Port différent** : Ajoutez votre port dans `app/main.py` si nécessaire
## 📋 Fonctionnalités

### 🔐 Authentification
- **Inscription** : Créer un nouveau compte utilisateur
- **Connexion** : Se connecter avec email/mot de passe
- **Déconnexion** : Se déconnecter

**Compte admin de test :**
- Email: `admin@test.com`
- Mot de passe: `admin123`

### 📚 Catégories
- **Lister les catégories** : Voir toutes les catégories disponibles
- **Voir les quiz par catégorie** : Accéder aux quiz disponibles avec logique d'accès
- **Sélectionner un quiz** : Démarrer un quiz accessible

### 🎯 Quiz
- **Démarrer un quiz** : Lancer une nouvelle tentative
- **Répondre aux questions** : Interface pour répondre (cases à cocher)
- **Soumettre le quiz** : Envoyer les réponses et voir les résultats

### 📊 Tentatives
- **Voir mes tentatives** : Historique des quiz passés
- **Détail d'une tentative** : Voir les questions, réponses et corrections

### 👑 Administration (Admin seulement)
- **Statistiques générales** : Dashboard admin
- **Gestion utilisateurs** : Liste des utilisateurs

## 🎨 Interface Utilisateur

### Navigation
- Onglets en haut pour naviguer entre les sections
- Indicateur de connexion en haut à droite
- Bouton admin visible seulement pour les administrateurs

### Logs en temps réel
- Section en bas pour voir toutes les requêtes API
- Codes couleur : vert=succès, rouge=erreur, bleu=info
- Bouton pour effacer les logs

### Design responsive
- Adapté mobile et desktop
- Animations et transitions fluides

## 🔧 Architecture technique

### Technologies
- **HTML5** : Structure de l'interface
- **CSS3** : Styles et animations
- **JavaScript (ES6+)** : Logique et appels API

### Gestion d'état
- `currentUser` : Informations utilisateur connecté
- `currentAttempt` : Tentative de quiz en cours
- `currentQuiz` : Quiz en cours

### Appels API
- Utilise `fetch()` avec credentials pour les cookies HTTP-only
- Gestion d'erreurs complète
- Logs détaillés de toutes les requêtes

## 📊 Endpoints testés

| Section | Endpoint | Méthode | Description |
|---------|----------|---------|-------------|
| Auth | `/auth/register` | POST | Inscription |
| Auth | `/auth/login` | POST | Connexion |
| Auth | `/auth/me` | GET | Infos utilisateur |
| Auth | `/auth/logout` | POST | Déconnexion |
| Catégories | `/categories` | GET | Liste catégories |
| Catégories | `/categories/{id}/quizzes/available` | GET | Quiz accessibles |
| Quiz | `/attempts/start/{quizId}` | POST | Démarrer quiz |
| Quiz | `/attempts/submit/{attemptId}` | POST | Soumettre réponses |
| Tentatives | `/users/me/attempts` | GET | Mes tentatives |
| Tentatives | `/attempts/{id}` | GET | Détail tentative |
| Admin | `/admin/stats` | GET | Stats générales |
| Admin | `/admin/users` | GET | Liste utilisateurs |

## 🐛 Dépannage

### Erreur CORS
Si vous avez des erreurs CORS, assurez-vous que :
- Le serveur backend tourne sur `http://127.0.0.1:8000`
- L'application HTML est servie depuis un serveur (pas ouvert directement)

### Cookies non envoyés
- Ouvrez la console développeur (F12)
- Vérifiez que les cookies sont envoyés avec les requêtes
- Assurez-vous que l'URL commence par `http://` (pas `file://`)

### Erreurs 401/403
- Vérifiez que vous êtes connecté
- Pour les endpoints admin, connectez-vous avec un compte admin

## 🎯 Utilisation typique

1. **Se connecter** avec `admin@test.com` / `admin123`
2. **Explorer les catégories** et voir les quiz disponibles
3. **Sélectionner un quiz accessible** (avec ✅)
4. **Répondre aux questions** en cochant les bonnes réponses
5. **Soumettre le quiz** et voir le score
6. **Consulter les résultats détaillés** dans "Mes tentatives"
7. **Accéder à l'admin** pour voir les statistiques

Cette interface permet de tester rapidement tous les aspects de l'API sans utiliser Postman ou curl ! 🚀




uvicorn app.main:app --reload