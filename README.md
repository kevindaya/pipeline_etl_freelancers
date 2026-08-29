# Pipeline ETL — Global Freelancers Dataset

Pipeline ETL complet (Extract → Transform → Load) en Python, appliqué à un dataset de 1000 profils de freelances fictifs volontairement "sale" (formats mélangés, valeurs manquantes, incohérences de casse). Les données sont nettoyées avec Pandas puis chargées dans **Google BigQuery**.

Projet réalisé dans le cadre de mon apprentissage de la Data Engineering, avec un focus sur la compréhension du "pourquoi" derrière chaque décision de nettoyage.

## Objectif

Transformer un CSV brut et incohérent en un dataset propre, exploitable, avec des décisions de nettoyage documentées et justifiées.

## Dataset

- **Source** : [Global Freelancers (Raw) Dataset](https://www.kaggle.com/datasets/urvishahir/global-freelancers-raw-dataset) — Urvish Ahir, licence CC0 (domaine public)
- **Contenu** : 1000 profils fictifs générés avec la librairie `Faker` (nom, genre, âge, pays, langue, compétence principale, années d'expérience, taux horaire, note, statut actif, satisfaction client)
- **Extraction** : Téléchargement automatisé via l'API Kaggle.
- `data/global_freelancers_raw.csv` : fichier source, jamais modifié
- `data/global_freelancers_clean.csv` : fichier généré par `pipeline.py`, prêt à l'emploi

## Problèmes identifiés dans les données brutes

| Colonne | Problème |
|---|---|
| `gender` | 10 variantes différentes pour 2 catégories réelles (`f`, `FEMALE`, `male`, `F`...) |
| `hourly_rate (USD)` | Formats mélangés : `'100'`, `'USD 100'`, `'$40'` |
| `is_active` | 8 façons différentes d'écrire vrai/faux (`'0'`, `'Y'`, `'yes'`, `'False'`...) |
| `client_satisfaction` | Stocké en texte avec `%` (ex: `'84%'`) |
| `age`, `years_of_experience`, `rating`, `hourly_rate_usd`, `client_satisfaction` | Valeurs manquantes, de 3% à 17.6% selon la colonne |

## Décisions de nettoyage et justification

Chaque valeur manquante n'a pas été traitée de la même façon — la stratégie dépend de ce que le manque signifie réellement pour la colonne concernée :

| Colonne | % manquant | Stratégie | Justification |
|---|---|---|---|
| `age` | 3% | Médiane globale | Peu de manquants, caractéristique stable, la médiane résiste aux valeurs extrêmes |
| `years_of_experience` | 5% | Médiane globale, plafonnée à `age - 18` | Empêche les incohérences logiques (ex: 9 ans d'expérience à 20 ans) — voir section Limites connues |
| `hourly_rate_usd` | 9.4% | Médiane groupée par `primary_skill` × tranche d'expérience | Le taux horaire dépend fortement du métier et de l'ancienneté ; une médiane globale écraserait des écarts réels |
| `rating` | 10.1% | **Non imputé**, laissé tel quel | Une note manquante signifie probablement "pas encore noté", pas "note moyenne" — inventer une valeur fausserait le sens de la donnée |
| `client_satisfaction` | 17.6% | **Non imputé**, laissé tel quel | Même logique que `rating`, avec un taux de manquants trop élevé (17.6%) pour une imputation fiable |
| `is_active` | 8.9% | Type `boolean` nullable (`pd.NA`) | Possibilité de confidentialité du statut du freelancer (ni `True` ni `False`) |
| `toutes_les_colonnes_non_numériques`| Varie selon la colonnes | Les valeurs manquantes ont été remplacées par `Unknown` | Il s'agit particulièrement des colonnes de type `string`, leurs valeurs manquantes ne réprésentaient pas d'informations exploitables|

**Principe général appliqué** : on impute uniquement quand le taux de manquants est faible et l'absence de valeur n'a pas de sens métier fort en elle-même. Sinon, on documente et on laisse le manque visible.

## Limites connues

- L'imputation de `years_of_experience` par une médiane globale (9 ans) créait des incohérences pour les profils jeunes (ex: 20 ans avec 9 ans d'expérience). Correction appliquée : plafonnement à `age - 18`, sous l'hypothèse qu'une carrière ne commence pas avant 18 ans.
- Les valeurs manquantes de `hourly_rate_usd` sont supposées liées à des profils incomplets. En contexte réel, cette hypothèse serait à valider avec le propriétaire des données (confidentialité possible) : les valeurs manquantes ont été comblées par médiane groupée selon `primary_skill` et `hourly_rate_usd` à partir des données possédées.

## Chargement (Load)

Les données nettoyées sont chargées dans **Google BigQuery** via `google-cloud-bigquery`, en Python.

- **Destination** : dataset `pipeline_etl_freelancers`, table `global_freelancers_clean` (projet `pipeline-etl-freelancers`, zone `US`)
- **Schéma explicite** : les 12 colonnes et leurs types sont déclarés à la main plutôt que laissés à l'autodétection de BigQuery, pour éviter tout mauvais typage silencieux sur un lot de données futur
- **`write_disposition=WRITE_TRUNCATE`** : chaque exécution du pipeline remplace entièrement le contenu de la table, pour que le script reste rejouable sans créer de doublons
- **Création du dataset idempotente** (`exists_ok=True`) : le script peut être relancé sur un projet vierge sans étape manuelle préalable dans la console

**Prérequis pour exécuter le Load** :
- Un compte de service GCP avec le rôle BigQuery Data Editor (ou supérieur), sa clé exportée en JSON (`cle_gcp.json`, non versionné)
- Un fichier `.env` (non versionné) avec :
  ```
  GOOGLE_APPLICATION_CREDENTIALS=cle_gcp.json
  PROJECT_ID=<ton-project-id>
  DATASET_ID=<nom-du-dataset>
  ```
  
## Bugs pandas rencontrés (et compris)

Quelques pièges qui valent la peine d'être documentés pour de futurs projets :

- **`NaN != NaN`** : impossible de faire correspondre un `NaN` dans un dictionnaire via `.map()` — nécessite `.fillna()` séparément.
- **`.astype(bool)` force les `NaN` à `True`** : tout ce qui n'est ni `0` ni vide devient `True`. Solution : `.astype('boolean')` (type nullable).
- **`.str` accessor uniquement sur du texte** : toute opération `.str.xxx()` doit précéder une conversion `.astype(float)`, jamais l'inverse.
- **`pd.cut()` exclut la borne basse par défaut** : nécessite `include_lowest=True` pour inclure la valeur minimale exacte dans la première tranche.
- **`.groupby(...).transform()` vs `.agg()`** : `transform` conserve la taille originale du dataframe (une valeur par ligne), utile pour combler des `NaN` sans perdre de lignes.

## Stack technique

- Python 3
- pandas, numpy
- google-cloud-bigquery (chargement vers BigQuery)
- python-dotenv (gestion des identifiants via `.env`)
- kagglehub (extraction automatisée du dataset source)

## Utilisation

```bash
python pipeline.py
```

Télécharge le dataset source, génère `data/global_freelancers_clean.csv`, puis charge son contenu dans la table BigQuery `pipeline_etl_freelancers.global_freelancers_clean`.

