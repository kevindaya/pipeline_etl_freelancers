import os
import numpy as np
import pandas as pd
import kagglehub as kh
import shutil

# Créer le dossier data s'il n'existe pas 
os.makedirs("data", exist_ok=True)

# Extraction du fichier CSV
cache_path = kh.dataset_download("urvishahir/global-freelancers-raw-dataset", force_download=True)

liste_fichiers = os.listdir(cache_path)

print("Contenu du dossier cache :", liste_fichiers)

# Chemin du fichier dans le cache Kaggle
fichier_source = os.path.join(cache_path, liste_fichiers[0])

# Chemin de destination dans le dossier /data
fichier_destination = os.path.join("data", "global_freelancers_raw.csv")

shutil.copy(fichier_source, fichier_destination)
print("Copié vers :", fichier_destination)

df = pd.read_csv(fichier_destination)

# Renommage des colonnes mal saisies
df = df.rename(columns = {'hourly_rate (USD)' : 'hourly_rate_usd', 'freelancer_ID' : 'freelancer_id'})

# Valeurs à remplacer dans les colonnes du dataframe
mapping_gender = {
    'F' : 'F',
    'FEMALE' : 'F',
    'M' : 'M',
    'MALE' : 'M',
}

mapping_is_active = {
    '0': False,
    '1' : True,
    'N' : False, 
    'False' : False,
    'True' : True,
    'yes' : True,
    'Y' : True,
    'no' : False
}

df['gender'] = df['gender'].str.upper().map(mapping_gender)
df['is_active'] = df['is_active'].map(mapping_is_active).astype('boolean')

# Combler les valeurs vides des colonnes non-numériques
exclus = [element for element in df.columns if pd.api.types.is_string_dtype(df[element])]

for element in exclus:
    df[element] = df[element].fillna("Unknown")

# Combler les valeurs vides des colonnes numériques
mediane_age = df['age'].median()
mediane_experience = df['years_of_experience'].median()

df['age'] = df['age'].fillna(mediane_age)
exp_manquants = df['years_of_experience'].isna() 
df['years_of_experience'] = df['years_of_experience'].fillna(mediane_experience)

# Limiter l'expérience à l'âge - 18 pour les valeurs non manquantes
df.loc[exp_manquants, 'years_of_experience'] = np.minimum(df.loc[exp_manquants, 'years_of_experience'], df.loc[exp_manquants, 'age'] - 18)

# Extraction des nombres dans la colonne hourly_rate_usd
df['hourly_rate_usd'] = df['hourly_rate_usd'].str.extract(r'(\d+)').astype(float)
df['client_satisfaction'] = df['client_satisfaction'].str.extract(r'(\d+)').astype(float)

# Estimer et combler les salaires vides selon l'expérience et le métier
df['exp_bin'] = pd.cut(df['years_of_experience'], bins=[0, 3, 5, 7, 10, np.inf], labels=['0-3', '3-5', '5-7', '7-10', '10+'], include_lowest=True)
df['hourly_rate_usd'] = df.groupby(['primary_skill', 'exp_bin'], observed=True)['hourly_rate_usd'].transform(lambda x: x.fillna(x.median()))

# Suppression de la colonne temporaire exp_bin
df = df.drop(columns=['exp_bin'])

# Sauvegarde du dataframe nettoyé dans un nouveau fichier CSV 

df.to_csv('data/global_freelancers_clean.csv',index=False)

print(df.describe())