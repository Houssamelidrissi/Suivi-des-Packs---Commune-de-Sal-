# CommuneSale - Plateforme de Gestion de Projets

## Description / Description
CommuneSale est une plateforme de gestion de projets conçue pour faciliter la collaboration et le suivi des projets en équipe. / CommuneSale is a project management platform designed to facilitate team collaboration and project tracking.

## Technologies Utilisées / Technologies Used
- **Backend**: Django 4.2+
- **Frontend**: HTML5, CSS3, JavaScript
- **Base de données**: SQLite (développement) / PostgreSQL (production)
- **Autres**: 
  - Bootstrap 5 pour le design responsive
  - jQuery pour les interactions côté client
  - Django REST framework pour les API

## Prérequis / Prerequisites
- Python 3.8+
- pip (gestionnaire de paquets Python)
- Virtualenv (recommandé)

## Installation / Installation

### 1. Cloner le dépôt
```bash
git clone [URL_DU_DEPOT]
cd communesale
```

### 2. Créer et activer un environnement virtuel
```bash
# Sur macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Sur Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```
SECRET_KEY=votre_clé_secrète
DEBUG=True
```

### 5. Appliquer les migrations
```bash
python manage.py migrate
```

### 6. Créer un superutilisateur (optionnel)
```bash
python manage.py createsuperuser
```

### 7. Lancer le serveur de développement
```bash
python manage.py runserver
```

## Structure du Projet / Project Structure
```
communesale/
├── media/                 # Fichiers uploadés par les utilisateurs
├── project_management/    # Configuration du projet Django
├── projects/             # Application principale
│   ├── migrations/       # Fichiers de migration
│   ├── static/           # Fichiers statiques (CSS, JS, images)
│   └── templates/        # Templates HTML
├── static/               # Fichiers statiques globaux
└── staticfiles/          # Fichiers statiques collectés
```

## Contribution / Contributing
Les contributions sont les bienvenues ! Pour contribuer :
1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créez une Pull Request

## Licence / License
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact / Contact
Pour toute question ou suggestion, veuillez ouvrir une issue sur le dépôt.
