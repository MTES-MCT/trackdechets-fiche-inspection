# Fiche d'inspection Trackdéchets

**version 1.3.1**


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
pipenv run run.py
```

### Notes de versions

**1.3.1 09/02/2023**
- L'alerte "déchets dangereux non autorisés" est maintenant déclenchée uniquement lorsque le déchet dangereux est reçu
- Ajout du profil établissement "WORKER"

**1.3 10/01/2023**
- Ajout des alertes sur les données ICPE
- Le tableau des déchets entrants et sortants est maintenant triable
- Le nombre de bordereaux reçu est affiché à côté du nombre de bordereaux créés
- Réduction du nombre de page à l'impression

**1.2 22/12/2022**
- Ajout des données ICPE et de nouveaux composants associés
- Utilisation de dahs_extensions pour ne plus faire transiter les données côté client 
entre les différents callbacks.
- Amélioration du CSS pour l'impression

**1.1.1 22/11/2022**

- Ajustement de la configuration serveur pour éviter les timeout
- Utilisation d'un *background callback* pour le chargement des données
- Ajout d'une animation de chargement
- Ajout d'un favicon

**1.1 21/11/2022**

- Ajout d'une option pour pouvoir imprimer la fiche inspection sans problèmes de mise en page
- Amélioration du design du tableau présentant le détail des déchets entrants/sortants

**1.0 10/09/2022**

- Réorganisation complète de l'application
- Ajout des données pour tous les types de bordereaux
- Présentation revue pour l'impression
- Ajout des statistiques par code déchets
- Les données aberrantes sont maintenant signalées avec possibilités de télécharger un extrait des données correspondantes


**0.3.0 9/06/2022**

- 🐛 correction du bug de la date de génération de la fiche
- suppression de la correction du poids
- affichage des profils déclarés
- encadrement des informations déclarées
- reformatage des informations sur les BSDD
- ajout des BSDD émis et du nombre de révisions

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
