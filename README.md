# Fiche d'inspection Trackdéchets

**version 0.2.0**

> Application basée sur Plotly Dash consacrée à la production de fiche permettant aux inspecteurs et inspectrices de
> l'environnement de préparer l'inspection d'un établissement avec des données issues de Trackdéchets.

### Pré-requis

- python 3.10
- pip
- [pipenv](https://pipenv.pypa.io/en/latest/)

### Déploiement

1. Faites une copie du fichier de déclaration des variables d'environnement :

```
cp sample.env .env
```

2. Configurez les variables d'environnement dans `.env` (vous pouvez aussi les déclarer directement dans votre système)  
3. Créez l'environnement

```bash
pipenv install
```

4. Démarrez l'application

```bash
pipenv run gunicorn --bind 0.0.0.0:8700 app:server
```

### Notes de versions

**0.2.0 04/05/2022**

- information supplémentaires dans l'en-tête
- support des établissements non-incrits dans Trackdéchets
  - sans bordereaux
  - avec bordereaux
- instructions pour l'édition d'une version PDF
- champ de sélection du SIRET
- configuration du déploiement sur Scalingo

**0.1.0 07/04/2022**

- coordonnées de l'établissement
- bordereaux de suivi de déchets dangereux (BSDD) émis et reçus
- département d'origine des déchets, par ordre de poids
