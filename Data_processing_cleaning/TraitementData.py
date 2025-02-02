import numpy as np
import pandas as pd
from numba import njit
import databento as db
import os
from datetime import datetime, timedelta







def ConvertirDBNV1(dbn_file_path, seuil_ecart=2):   
    count = 1
    df_consolide = pd.DataFrame()

    for file_path in dbn_file_path:
        try:
            print(f"Traitement de {file_path}")
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            dbn_store = db.DBNStore.from_file(file_path)
            df = dbn_store.to_df()
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier {file_path} : {e}")
            continue  # Passe au fichier suivant

        df['ts_event'] = pd.to_datetime(df['ts_event'])
        df['Date'] = df['ts_event'].dt.date
        df['Time'] = df['ts_event'].dt.strftime('%H:%M:%S')
        df = df.sort_values(by='ts_event').reset_index(drop=True)
        df['rolling_mean'] = df['price'].rolling(window=50).mean()
        df_filtre = df[abs(df['price'] - df['rolling_mean']) <= seuil_ecart]
        df_filtre = df_filtre.drop(columns=['rolling_mean'])

        print("Traitement du CSV")
        colonnes_a_supprimer = [
            'symbol', 'ts_event', 'sequence', 'ts_in_delta', 'depth', 'instrument_id', 'publisher_id', 'rtype'
        ]
        df = df.drop(columns=colonnes_a_supprimer)

        # Nettoyage du CSV
        df_filtre_sans_anomalies = detect_anomalies(df)
        df_consolide = pd.concat([df_consolide, df_filtre_sans_anomalies], ignore_index=True)

    # Enregistrement du fichier CSV consolidé
    df_consolide.to_csv("CSV2024_Global.csv", index=False)
    print(f"Le fichier consolidé a été enregistré sous le nom CSV2024_Global.csv.")


@njit
def detect_anomalies_numba(prices, threshold):
    n = len(prices)
    anomalies = np.zeros(n, dtype=np.bool_)
    last_valid_price = prices[0]
    for i in range(1, n):
        if abs(prices[i] - last_valid_price) > threshold:
            anomalies[i] = True
        else:
            last_valid_price = prices[i]
    return anomalies

def detect_anomalies(df, threshold=5):
    prices = df['price'].values
    anomalies = detect_anomalies_numba(prices, threshold)
    df['Anomalie'] = anomalies
    df_sans_anomalies = df[df['Anomalie'] == False].reset_index(drop=True)
    print(f"Le DataFrame sans anomalies a été traiter.")
    return df_sans_anomalies
    

def generate_dbn_file_paths(start_date, end_date, base_path):
    # Conversion des dates de départ et de fin en objets datetime
    current_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')
    
    dbn_file_paths = []

    # Tant que la date actuelle est avant ou égale à la date de fin
    while current_date <= end_date:
        # Formatage de la date sous forme "YYYYMMDD"
        date_str = current_date.strftime('%Y%m%d')
        
        # Construction du chemin complet du fichier .dbn
        dbn_file = fr"{base_path}\glbx-mdp3-{date_str}.trades.dbn\glbx-mdp3-{date_str}.trades.dbn"
        dbn_file_paths.append(dbn_file)
        
        # Incrémentation du jour (1 jour à la fois)
        current_date += timedelta(days=1)

    return dbn_file_paths

# Exemple d'utilisation du script
# start_date = "20221001"  # Date de début : 1er février 2022
# end_date = "20221123"    # Date de fin : 31 juillet 2024
# base_path = r"C:\Users\Jordi\Desktop\ALGO\dbn"  # Chemin de base
# dbn_file_paths = generate_dbn_file_paths(start_date, end_date, base_path)

# # Afficher ou utiliser la liste des chemins
# print(dbn_file_paths)



dbn_file_paths=[r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240101-20240131.trades.dbn',r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240201-20240229.trades.dbn',r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240301-20240331.trades.dbn'
                ,r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240401-20240430.trades.dbn',r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240501-20240531.trades.dbn'
                ,r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240601-20240630.trades.dbn',r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240701-20240731.trades.dbn',r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240801-20240805.trades.dbn'
                ,r'C:\Users\Jordi\Desktop\ALGO\dbn\glbx-mdp3-20240919.trades.dbn\glbx-mdp3-20240919.trades.dbn']
ConvertirDBNV1(dbn_file_paths)
