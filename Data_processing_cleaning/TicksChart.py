import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

def is_weekday(date):
    return date.weekday() < 5



def aggregate_ticks_to_bars(file_paths, ticks_per_bar):
    df_final = pd.DataFrame()

    for file_path in file_paths:
        data = pd.read_csv(file_path)
        data['tick_index'] = data.index // ticks_per_bar
        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')
        data['is_weekday'] = data['Date'].apply(is_weekday)
        data_weekdays = data[data['is_weekday']].copy() 

        data_weekdays.loc[:, 'buy_volume'] = data_weekdays['size'].where(data_weekdays['side'] == 'B', 0)  # Achat market (side = A)
        data_weekdays.loc[:, 'sell_volume'] = data_weekdays['size'].where(data_weekdays['side'] == 'A', 0)  # Vente market (side = B)


        ohlc_dict = {
            'price': ['first', 'max', 'min', 'last'],
            'size': 'sum',
        }
        aggregated_data = data_weekdays.groupby('tick_index').agg(ohlc_dict)
        
        aggregated_data.columns = ['open', 'high', 'low', 'close', 'volume']

        aggregated_data['delta'] = data_weekdays.groupby('tick_index')['buy_volume'].sum() - data_weekdays.groupby('tick_index')['sell_volume'].sum()
        aggregated_data['CVD'] = aggregated_data['delta'].cumsum()

        aggregated_data['Date'] = data_weekdays.groupby('tick_index')['Date'].first().values
        aggregated_data['Time'] = data_weekdays.groupby('tick_index')['Time'].first().values

        df_final = pd.concat([df_final, aggregated_data])

    df_final.to_csv(f'aggregated_2024__{ticks_per_bar}_ticks.csv', index=False)





# file_paths=[r'C:\Users\Jordi\Desktop\ALGO\CSV2024_Global.csv']

# aggregate_ticks_to_bars(file_paths, ticks_per_bar=100)



df1 = pd.read_csv(r'C:\Users\Jordi\Desktop\ALGO\aggregated_2022__100_ticks.csv')
df2 = pd.read_csv(r'C:\Users\Jordi\Desktop\ALGO\aggregated_2023__100_ticks.csv')
df3 = pd.read_csv(r'C:\Users\Jordi\Desktop\ALGO\aggregated_2024__100_ticks.csv')

# Fusionner les colonnes Date et Time en une colonne Datetime
def merge_date_time(df):
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    return df

# Appliquer la fonction à chaque DataFrame
df1 = merge_date_time(df1)
df2 = merge_date_time(df2)
df3 = merge_date_time(df3)

# Fusionner les DataFrames
merged_df = pd.concat([df1, df2, df3])

# Trier par la colonne Datetime
merged_df = merged_df.sort_values(by='Datetime')

# Réinitialiser l'index (optionnel)
merged_df = merged_df.reset_index(drop=True)

# Afficher le résultat
print(merged_df)

# Sauvegarder le DataFrame fusionné dans un nouveau fichier CSV (optionnel)
merged_df.to_csv('ES_100T.csv', index=False)