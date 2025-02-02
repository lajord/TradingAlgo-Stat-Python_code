import numpy as np
import pandas as pd 
import vectorbt as vbt
import talib 
import matplotlib.pyplot as plt 
import plotly.graph_objects as go
import market_regime as mr
import s_score as sc
import MetaTrader5 as mt5
import sys
import os
chemin_parent = os.path.abspath(r'C:\Users\Jordi\Desktop\Environement de developement\Trading_Dev_Stratégie_Environement\FunctionEssential')
if chemin_parent not in sys.path:
    sys.path.append(chemin_parent)
import function_essential as fe


#################################################################################################################

"""
Création des fonctions python pour les indicateurs 
=> MA ,RSI, ATR etc etc calculer avec les outils a disposition ! vectorbt
"""



def s_score(close,period):
    return sc.mean_reversion(close,period)

def market_regime(close,period):
    return mr.market_regime(close,period)



###################################################################################################################


"""
Création des fonctions d'entrée et de sortie 
"""

def long(s_score, lower_band, market_regime,seuil):
    conditions = (s_score < lower_band) & (market_regime > seuil)
    return conditions

def short(s_score, upper_band, market_regime,seuil):
    conditions = (s_score > upper_band) & (market_regime > seuil)
    return conditions

def short_exit_trades(short,s_score):
    short_exit = np.zeros_like(short, dtype=bool)
    for i in range(0,len(short_exit)):
        if short[i] == True:
            for j in range(i+1,len(short_exit)):
                if s_score[j]<=0:
                    short_exit[j] =True

    return short_exit

def long_exit_trades(long,s_score):
    long_exit = np.zeros_like(long, dtype=bool)
    for i in range(0,len(long_exit)):
        if long[i] == True:
            for j in range(i+1,len(long_exit)):
                if s_score[j]>=0:
                    long_exit[j] =True
    return long_exit


####################################################################################################################
"""
Création des Indicator Factory
"""

Ind_s_score = vbt.IndicatorFactory(
    class_name="s_score",
    input_names=["close"],
    param_names=["period"],
    output_names=["value_s_score","ma30_s_score","Upper_band","Lower_band"]
).from_apply_func(s_score)

Ind_market_regime = vbt.IndicatorFactory(
    class_name="market_regime",
    input_names=["close"],
    param_names=["period"],
    output_names=["market_regime_value"]
).from_apply_func(market_regime)

Ind_long_entries = vbt.IndicatorFactory(
    class_name="long",
    input_names=["s_score","lower_band","market_regime"],
    param_names=["seuil"],
    output_names=["entries"]
).from_apply_func(long)

Ind_short_entries = vbt.IndicatorFactory(
    class_name="short",
    input_names=["s_score","upper_band","market_regime"],
    param_names=["seuil"],
    output_names=["entries"]
).from_apply_func(short)

Ind_long_exit_trades = vbt.IndicatorFactory(
    class_name="long_exit_trades",
    input_names=["long","s_score"],
    output_names=["exits"]
).from_apply_func(long_exit_trades)

Ind_short_exit_trades = vbt.IndicatorFactory(
    class_name="short_exit_trades",
    input_names=["short","s_score"],
    output_names=["exits"]
).from_apply_func(short_exit_trades)



class Strategie():


    def __init__(self,data,frequence,list_tickers):
        self.data = data
        self.frequence = frequence
        self.list_tickers = list_tickers


    def backtest(self,period_end,period_start,period_s_score,period_market_regime, period_X_candle,seuil):
        if (period_end == 0) and (period_start == 0):

            long_entries_df = pd.DataFrame()
            short_entries_df = pd.DataFrame()
            long_exits_df = pd.DataFrame()
            short_exits_df = pd.DataFrame()
            close_df = pd.DataFrame()

            for ticker in self.list_tickers:
                """
                A modifier pour rajouter calcul d'indicateur un peu spécial ou autre 
                """
                data = self.data[ticker]
                close = data['close']
                liste_value = self.make_value_no_combi(close,period_s_score,period_market_regime)
                entries = self.make_entries(liste_value[0],liste_value[2],liste_value[3],liste_value[4],seuil)

                long = entries[0]
                short = entries[1]
                
                exits = self.make_exits(long,short,liste_value[0])
                long_exits = exits[0]
                short_exits = exits[1]
                # return long,long_exits,short,short_exits
                #Reset les index pour tout normaliser
                long = long.reset_index(drop=True)
                short = short.reset_index(drop=True)
                long_exits = long_exits.reset_index(drop=True)
                short_exits = short_exits.reset_index(drop=True)
                close = close.reset_index(drop=True)
                #enregistrer dans des dataframes 
                long_entries_df[ticker] = long
                short_entries_df[ticker] = short
                long_exits_df[ticker] = long_exits
                short_exits_df[ticker] = short_exits
                close_df[ticker] = close

            #remplacer les 0 qui ont état mis durant import data
            close_df = close_df.replace(0, None).fillna(method='ffill')
            portfolio = vbt.Portfolio.from_signals(
                close_df,
                long_entries_df,
                long_exits_df,
                short_entries_df,
                short_exits,
                freq=self.frequence
            )

            return portfolio
        
        else :
            pass


    def optimize(self,metrics,choice,period1,period2,params1):
        dataframe_save = {}   # Dans le cadre d'un multi Asset ca va venir enregistrer le df de l'optimisation -> Puis faire un mean -> Voir le parametre qui fonctionne le mieux sur tous
        if choice == 1:
            entries_df = pd.DataFrame()
            exits_df = pd.DataFrame()
            for ticker in self.list_tickers:

                entries_df = entries_df[0:0]
                exits_df = exits_df[0:0]
                data = self.data[ticker]
                liste_value = self.make_value_no_combi()

                for i in range(params1.shape[1]):  ## Ici tu boucles sur le paramètre que tu veux opti / Il peut y avoir deux boucles si tu opti deux params !
                    params1_1D = params1.iloc[:, i]
                    liste_value[0] =  params1_1D
                    entries = self.make_entries()
                    exits = self.make_exits()

                    #Important a pas toucher
                    entries_df[i] = entries 
                    exits_df[i] = exits
                    #-----------------------#

                # Important a note !! Pour pas avoir d'erreur ensuite les noms des colonnes de entries et exits doivent avoir des index de 0 a n (0,1,2,3 etc)
                # Si tu as un soucis avec la suite apres le backtest regarde les indices de entries et exits

                close = data['close']
                close_df = close.replace(0, None).fillna(method='ffill')
                portfolio = vbt.Portfolio.from_signals(
                     close_df,
                     entries_df,
                     exits_df,
                     freq= self.frequence,
                     slippage=0.0005
                )
                combinaison = fe.get_combinaison(period1,period2)
                df = fe.get_df_optimisation_parameter(combinaison,portfolio,metrics)
                dataframe_save[ticker] = df



        if choice == 2:

            pass

        """
        on peut rajouter d'autre choice biensur
        """
    
    def make_entries(self,s_score,upper_band,lower_band,market_regime,seuil):
        long = Ind_long_entries.run(s_score,lower_band,market_regime,seuil)
        short = Ind_short_entries.run(s_score,upper_band,market_regime,seuil)

        long_entries = long.entries
        short_entires = short.entries

        for i in range(0,len(long_entries)):
            if long_entries[i] == True:
                for j in range(1,30):
                    long_entries[i+j] = False
            if short_entires[i] == True:
                for j in range(1,30):
                    short_entires[i+j] = False

        out = [long_entries,short_entires]
        return out 

    def make_exits(self,long,short,s_score):
        long_exits = Ind_long_exit_trades.run(long,s_score)
        short_exits = Ind_short_exit_trades.run(short,s_score)
        out = [long_exits.exits,short_exits.exits]
        return out

    
    def make_value_no_combi(self,close,period_s_score,period_mr):
        Value_s_score = Ind_s_score.run(close,period_s_score,param_product = True)
        Value_market_regime = Ind_market_regime.run(close,period_mr,param_product = True)

        valeurs = [Value_s_score.value_s_score, Value_s_score.ma30_s_score, Value_s_score.Upper_band, Value_s_score.Lower_band,Value_market_regime.market_regime_value]
        return valeurs


tickers = ['EURUSD']
data = fe.get_data_forex(tickers,timeframe=mt5.TIMEFRAME_H4)

strat_mean_reversion = Strategie(data,"240m",tickers)

# long_entires,long_exits,short_entires,short_exits = strat_mean_reversion.backtest(0,0,150,30,50,75)
portfolio= strat_mean_reversion.backtest(0,0,200,30,80,75)

fe.get_pnl(portfolio)


# num_true = long_entires.sum()
# print(f"Nombre de long : {num_true}")
# num_true = short_entires.sum()
# print(f"Nombre de short : {num_true}")

# # Créer un DataFrame pour les données de close et portfolio
# df = pd.DataFrame({'close': data["EURUSD"]['close'], 'long': long_entires, 'short': short_entires, 'exits_long' : long_exits,'exits_short' : short_exits})

# # Créer la figure avec les prix de clôture
# fig = go.Figure()

# # Tracer les prix de clôture
# fig.add_trace(go.Scatter(
#     x=df.index, 
#     y=df['close'], 
#     mode='lines', 
#     name='Close',
#     line=dict(color='white')
# ))

# # Ajouter des croix bleues pour les `True` dans portfolio
# fig.add_trace(go.Scatter(
#     x=df[df['long']].index, 
#     y=df[df['long']]['close'], 
#     mode='markers', 
#     name='Entries', 
#     marker=dict(symbol='x', color='blue', size=10)
# ))

# fig.add_trace(go.Scatter(
#     x=df[df['short']].index, 
#     y=df[df['short']]['close'], 
#     mode='markers', 
#     name='Entries', 
#     marker=dict(symbol='x', color='red', size=10)
# ))


# fig.add_trace(go.Scatter(
#     x=df[df['exits_long']].index, 
#     y=df[df['exits_long']]['close'], 
#     mode='markers', 
#     name='long exits', 
#     marker=dict(symbol='arrow-bar-up', color='blue', size=10)
# ))

# fig.add_trace(go.Scatter(
#     x=df[df['exits_short']].index, 
#     y=df[df['exits_short']]['close'], 
#     mode='markers', 
#     name='short exits', 
#     marker=dict(symbol='arrow-bar-up', color='red', size=10)
# ))

# # Personnaliser le graphique
# fig.update_layout(
#     title="Close Prices with Portfolio Signals",
#     xaxis_title="Index",
#     yaxis_title="Close Price",
#     template="plotly_dark"  # Choix du thème, vous pouvez aussi choisir 'plotly' ou 'ggplot2'
# )

# # Afficher le graphique interactif
# fig.show()