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
    'nan' : False,
    'no' : False
}

df['gender'] = df['gender'].str.upper().map(mapping_gender)
df['is_active'] = df['is_active'].map(mapping_is_active)

