import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

tickers = ['^GSPC', '^VIX']

start_date = '2010-01-01'
end_date = '2024-01-01'
data_SP = yf.download('^GSPC', start=start_date, end=end_date, interval='1d')
data_VIX= yf.download('^VIX', start=start_date, end=end_date, interval='1d')
print(data_SP.head())
elasticité= pd.DataFrame()
elasticité['SP500_Daily_Return'] = (data_SP['Adj Close'] - data_SP['Open']) / data_SP['Open'] * 100


vix_open = data_VIX['Open']
vix_open_rounded = np.ceil(vix_open * 2) / 2
elasticité['VIX_Open_Rounded'] = vix_open_rounded

print(elasticité.head())
elasticité['SP500_Daily_Return'] = elasticité['SP500_Daily_Return'].abs()
grouped_elasticité_abs = elasticité.groupby('VIX_Open_Rounded')['SP500_Daily_Return'].mean()

# Afficher les résultats
print("Moyennes des rendements du S&P 500 pour chaque niveau du VIX arrondi :")
print(grouped_elasticité_abs)# Tracer le graphique
plt.figure(figsize=(10, 6))
plt.plot(grouped_elasticité_abs.index, grouped_elasticité_abs.values, marker='o', linestyle='-')
plt.title('Moyenne des rendements absolus du S&P 500 en fonction des niveaux arrondis du VIX')
plt.xlabel('Niveaux du VIX arrondis')
plt.ylabel('Moyenne des rendements absolus du S&P 500 (%)')
plt.grid(True)

# Afficher le graphique
plt.show()