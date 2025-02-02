import pandas as pd
from datetime import datetime

# Paramètres
input_file_path = r'C:\Users\Utilisateur\Coding\python\DataStatSPX.csv'
output_file_path = r'C:\Users\Utilisateur\Coding\python\Datastat-remaniée.xlsx'
date_debut = '2023-01-01'  # Format : 'YYYY-MM-DD'

# Lecture du fichier CSV avec le bon délimiteur et en utilisant la première ligne comme en-tête
df = pd.read_csv(input_file_path, sep=',')

# Renommer la colonne 'time' en 'Date' pour plus de clarté
df.rename(columns={'time': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

# Conversion du format de date
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d').dt.strftime('%d/%m/%Y')

# Filtrage des données à partir de la date de début
date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
df = df[df['Date'] >= date_debut]

# Réorganisation des colonnes : Close, Open, High, Low
df = df[['Date', 'Close', 'Open', 'High', 'Low']]

# Remplacement des points par des virgules dans les valeurs numériques
# Ensuite, on convertit ces valeurs en nombres pour éviter l'erreur de texte
df[['Close', 'Open', 'High', 'Low']] = df[['Close', 'Open', 'High', 'Low']].replace(',', '.', regex=True).astype(float)

# Exportation vers un fichier Excel avec un format approprié
with pd.ExcelWriter(output_file_path, date_format='DD/MM/YYYY', datetime_format='DD/MM/YYYY') as writer:
    df.to_excel(writer, index=False)

print(f"Fichier réorganisé et sauvegardé sous : {output_file_path}")
