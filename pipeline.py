import pandas as pd
import numpy as np

df = pd.read_csv("data/global_freelancers_raw.csv")

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


# Extraction des nombres dans la colonne hourly_rate_usd
df['hourly_rate (USD)'] = df['hourly_rate (USD)'].str.extract(r'(\d+)').astype(float)

# Renommage des colonnes
df = df.rename(columns = {'hourly_rate (USD)' : 'hourly_rate_usd', 'freelancer_ID' : 'freelancer_id'})
