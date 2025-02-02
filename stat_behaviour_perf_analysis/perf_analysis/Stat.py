import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

#Algo pour calculer les différentes stats et faire des graphes en fonction
#Pnl , WR , graphique bar avec les rendements de chaque trade pour voir la répartition
# Moyenne du P/L : Calculez le profit ou la perte moyen par trade pour identifier la rentabilité moyenne.
# Variance et écart-type du P/L : Mesurez la volatilité des profits et pertes pour comprendre le risque.
# Max Drawdown : La plus grande perte de valeur de votre portefeuille à partir d'un sommet, pour comprendre le risque maximal supporté
# séparer les trades de facons a avoir le ratio des trades ou je joue de la continuation sur des accumu, ou je joue des rebonds ou des deeps etc


# df = pd.read_csv(r'C:\Users\Jordi\Desktop\ALGO\TradeActivityLogExport_2024-11-04.csv', sep='\t')

# colonnes_utiles = [
#     'DateTime', 'Symbol', 'OrderType', 'Quantity', 'BuySell', 'Price', 
#     'OrderStatus', 'FillPrice','OpenClose']


# df_filtre = df[[col for col in colonnes_utiles if col in df.columns]]


# colonnes_prix = ['Price', 'FillPrice']  

# for colonne in colonnes_prix:
#     if colonne in df_filtre.columns:
#         df_filtre.loc[:, colonne] = df_filtre[colonne] / 100


# #df_filtre et le csv avec toute la data 

# df_filtre.to_csv('trades_historical_Octobre.csv', index=False)
df_filtre = pd.read_csv('trades_historical_Octobre.csv')

point_per_trade = 5

df_stat = pd.DataFrame()


returns = []
dates = []
for i in range(0, len(df_filtre) - 1, 2):
    open_order = df_filtre.iloc[i]
    close_order = df_filtre.iloc[i + 1]
    if open_order['OpenClose'] == 'Open' and close_order['OpenClose'] == 'Close':
        if open_order['BuySell'] == 'Buy':
            lot = close_order['Quantity']
            trade_return = (close_order['FillPrice'] - open_order['FillPrice']) * point_per_trade * lot - (1.02 * lot)
            returns.append(trade_return)
        else:
            lot = close_order['Quantity']
            trade_return = (open_order['FillPrice'] - close_order['FillPrice']) * point_per_trade * lot - (1.02 * lot)
            returns.append(trade_return)
        dates.append(close_order['DateTime'])




df_stat['return $'] = returns
df_stat['Date'] = dates
df_stat['PnL'] = df_stat['return $'].cumsum()
df_stat['Win'] = df_stat['return $'] > 0
df_stat['Loose'] = df_stat['return $'] <= 0
capital = 25000
df_stat['return_on_capital_%'] = df_stat['return $'] * 100 / capital
df_stat['Trade Number'] = range(1, len(df_stat) + 1)



print(df_stat)

def stat(df):

    rendement_moyen = df['return $'].mean()
    std_dev_pnl = df['return $'].std()
    median_pnl = df['return $'].median()
    min_pnl = df['return $'].min()
    max_pnl = df['return $'].max()

    print(f"Rendement Moyen: {rendement_moyen}")
    print(f"Ecart-type: {std_dev_pnl}")
    print(f"Mediane: {median_pnl}")
    print(f"Min: {min_pnl}")
    print(f"Max: {max_pnl}")









def PnL(df_stat):
    df_stat['Date'] = pd.to_datetime(df_stat['Date'])
    df_stat = df_stat.sort_values(by='Date')
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))  
    plt.plot(df_stat['Date'], df_stat['PnL'], color='#2A9D8F', linewidth=2)
    plt.axhline(0, color='black', linewidth=1.5, linestyle='--')
    plt.fill_between(df_stat['Date'], df_stat['PnL'], 0, where=(df_stat['PnL'] > 0), 
                    color='green', alpha=0.3)
    plt.fill_between(df_stat['Date'], df_stat['PnL'], 0, where=(df_stat['PnL'] <= 0), 
                    color='red', alpha=0.3)
    plt.title('Évolution du PnL au fil du temps', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('PnL cumulé ($)', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(color='gray', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.show()
    plt.show()



def repartition(df_stat):
    labels = ['Gagnant', 'Perdant']
    nombre_win = df_stat['Win'].sum()
    nombre_loose = df_stat['Loose'].sum()
    sizes = [nombre_win, nombre_loose]
    colors = ['#2A9D8F', '#E76F51']  
    explode = (0.1, 0) 
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=140)
    plt.title('Répartition des Trades Gagnants et Perdants', fontsize=16, fontweight='bold')
    plt.show()


def repartition_purcentage(df_stat):
    colors = df_stat['return_on_capital_%'].apply(lambda x: 'green' if x > 0 else 'red')
    plt.figure(figsize=(10, 6))
    plt.bar(df_stat['Trade Number'], df_stat['return_on_capital_%'], color=colors)
    plt.axhline(0, color='black', linewidth=1.5, linestyle='--')
    plt.title('Évolution du Rendement en % sur le Capital par Trade', fontsize=16, fontweight='bold')
    plt.xlabel('Nombre de Trades', fontsize=14)
    plt.ylabel('Rendement en % sur le Capital', fontsize=14)
    plt.grid(False)
    plt.tight_layout()
    plt.show()



stat(df_stat)
repartition_purcentage(df_stat)
PnL(df_stat)
repartition(df_stat)