import numpy as np
import pandas as pd 
import vectorbt as vbt
import talib 
import matplotlib.pyplot as plt 
import plotly.graph_objects as go
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





###################################################################################################################


"""
Création des fonctions d'entrée et de sortie 
"""

#Ca va renvoyer une liste d'index qui représente les position qui n'ont pas de reverse

def long(close, s_score, lower_band, ma_s_score):

    conditions_first = (s_score < lower_band)
    conditions = np.zeros_like(conditions_first, dtype=bool)
    last_true = 30
    for i in range(0, len(conditions_first)):
        if conditions_first[i]== True  and (s_score[i] < ma_s_score[i]) and last_true>=30:
            last_true = 0
            conditions[i]= True
                
        last_true += 1
    return conditions

def short(close,s_score,upper_band,ma_s_score):

    conditions_first = (s_score > upper_band)
    conditions = np.zeros_like(conditions_first, dtype=bool)
    last_true = 30
    for i in range(0, len(conditions_first)):
        if conditions_first[i] == True and (s_score[i] > ma_s_score[i]) and last_true>=30:
            last_true = 0
            conditions[i]= True
        last_true += 1
    return conditions


def short_exit_trades(short,index,ma_s_score,s_score,period_out,period_out_reverse):
    short_exit = np.zeros_like(short, dtype=bool)

    for i in range(0,len(short)):
        if short[i] == True:
            short_exit[i+period_out_reverse]= True
    
    return short_exit

def long_exit_trades(long,index,ma_s_score,s_score,period_out,period_out_reverse):
    long_exit = np.zeros_like(long, dtype=bool)

    for i in range(0,len(long)):
        if long[i] == True:
            long_exit[i+period_out_reverse]= True

    
    return long_exit



####################################################################################################################
"""
Création des Indicator Factory
"""
#close,s_score,lower_band,ma_s_score
Ind_long_entries = vbt.IndicatorFactory(
    class_name="long",
    input_names=["close","s_score","lower_band","ma_s_score"],
    output_names=["entries"]
).from_apply_func(long)

Ind_short_entries = vbt.IndicatorFactory(
    class_name="short",
    input_names=["close","s_score","upper_band","ma_s_score"],
    output_names=["entries"]
).from_apply_func(short)

Ind_long_exit_trades = vbt.IndicatorFactory(
    class_name="long_exit_trades",
    input_names=["long","index","ma_s_score","s_score"],
    param_names=["period_out","period_out_reverse"],
    output_names=["exits"]
).from_apply_func(long_exit_trades)

Ind_short_exit_trades = vbt.IndicatorFactory(
    class_name="short_exit_trades",
    input_names=["short","index","ma_s_score","s_score"],
    param_names=["period_out","period_out_reverse"],
    output_names=["exits"]
).from_apply_func(short_exit_trades)

Ind_s_score = vbt.IndicatorFactory(
    class_name="s_score",
    input_names=["close"],
    param_names=["period"],
    output_names=["value_s_score","ma30_s_score","Upper_band","Lower_band"]
).from_apply_func(s_score)




class Strategie():


    def __init__(self,data,frequence,list_tickers):
        self.data = data
        self.frequence = frequence
        self.list_tickers = list_tickers


    def backtest(self,period_start,period_end, period_s_score,period_out,period_out_reverse):
        if (period_end == 0) and (period_start == 0):

            long_entries_df = pd.DataFrame()
            short_entries_df = pd.DataFrame()
            long_exits_df = pd.DataFrame()
            short_exits_df = pd.DataFrame()
            close_df = pd.DataFrame()
            for ticker in self.list_tickers:
                data = self.data[ticker]
                print(data['close'])
                liste_value = self.make_value_no_combi(data['close'],period_s_score)
                
                entries = self.make_entries(data['close'],liste_value,period_out)

                exits = self.make_exits(entries[0],entries[1],entries[2],liste_value[1],liste_value[0],period_out,period_out_reverse)

                long = entries[0]
                short = entries[1]
                long_exits = exits[0]
                short_exits = exits[1]
                #Reset les index pour tout normaliser
                long = long.reset_index(drop=True)
                short = short.reset_index(drop=True)
                long_exits = long_exits.reset_index(drop=True)
                short_exits = short_exits.reset_index(drop=True)
                #close = data['close'].reset_index(drop=True)
                #enregistrer dans des dataframes 
                long_entries_df[ticker] = long
                short_entries_df[ticker] = short
                long_exits_df[ticker] = long_exits
                short_exits_df[ticker] = short_exits
                close_df[ticker] = data['close']

            #remplacer les 0 qui ont état mis durant import data
            close_df = close_df.replace(0, None).fillna(method='ffill')

            print(close_df.shape)
            print(close_df.describe()) 
            portfolio = vbt.Portfolio.from_signals(
                close_df,
                long_entries_df,
                long_exits_df,
                short_entries_df,
                short_exits_df,
                freq=self.frequence
                # slippage=0.0005,
                # init_cash=10000,  # Capital initial
                # fees=0.001 
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
                print()
                portfolio = vbt.Portfolio.from_signals(
                     close_df,
                     entries_df,
                     exits_df,
                     freq= self.frequence,
                     slippage=0.0005,
                     init_cash=10000,  # Capital initial
                     fees=0.1     # Frais de transaction (par exemple 0.1%)
                )
                combinaison = fe.get_combinaison(period1,period2)
                df = fe.get_df_optimisation_parameter(combinaison,portfolio,metrics)
                dataframe_save[ticker] = df



        if choice == 2:

            pass

        """
        on peut rajouter d'autre choice biensur
        """
    
    def make_entries(self,close,list_value,period_firts):


        entries_long =Ind_long_entries.run(close,list_value[0],list_value[3],list_value[1])
        entries_short = Ind_short_entries.run(close,list_value[0],list_value[2],list_value[1])
        
        long = entries_long.entries
        short = entries_short.entries
        index= np.zeros_like(short, dtype=bool)

        long_reverse = np.zeros_like(long, dtype=bool)
        short_reverse = np.zeros_like(short, dtype=bool)

        for i in range(0,len(long)):
            if long[i]==True:
                if close[i+period_firts]<close[i]*0.995:
                    index[i] = True
                    short_reverse[i+period_firts] = True
        
        for i in range(0,len(short)):
            if short[i]==True:
                if close[i+period_firts]>close[i]*1.005:
                    index[i] = True
                    long_reverse[i+period_firts] = True

        # long = long | long_reverse
        # short = short | short_reverse
        out = [long,short,index]
        return out


    def make_exits(self,long,short,index,ma_s_score,s_score,period_out,period_out_reverse):

        long_exits = Ind_long_exit_trades.run(long,index,ma_s_score,s_score,period_out,period_out_reverse)
        short_exits = Ind_short_exit_trades.run(short,index,ma_s_score,s_score,period_out,period_out_reverse)
        out = [long_exits.exits,short_exits.exits]
        return out


    
    def make_value_no_combi(self,close,period):
        Value_spanA_1 = Ind_s_score.run(close,period=period,param_product = True)

        valeurs = [Value_spanA_1.value_s_score, Value_spanA_1.ma30_s_score, Value_spanA_1.Upper_band, Value_spanA_1.Lower_band]
        return valeurs




"""

Pour la structure du code ici ce que tu fais c'ets que tu fais t'es signaux entrées et sortie et ensuite tu gère le reverse :
-> Pour chaque true dans liste long_entries :
    si apres 5 bougie c'est pas le TP alors tu clotures dans long exits et tu mets true dans reverse short 
-> Pour chaque true dans short entries
    si apres 5 bougie c'est pas le tp alors tu clotures dans short exits et tu mets true dans reverse long 

    Pour chaque true dans reverse long tu calcul l'exit associer et tu met exits dans long exit et de meme pour short
    ensuite tu combines long entries et reverse long et tu combines short entries avec reverse short 

    tu peux meme en réalité tout mettre dans le meme et ca marchera 


"""



tickers = ['USDCHF']
data = fe.get_data_forex(tickers,timeframe=mt5.TIMEFRAME_H4)

strat_mean_reversion = Strategie(data,"240m",tickers)

portfolio = strat_mean_reversion.backtest(0,0,150,10,40)


fe.get_pnl(portfolio)

# num_true = entre[0].sum()
# print(f"Nombre de long : {num_true}")
# num_true = entre[1].sum()
# print(f"Nombre de short : {num_true}")

# # Créer un DataFrame pour les données de close et portfolio
# df = pd.DataFrame({'close': data["EURUSD"]['close'], 'long': entre[0], 'short': entre[1], 'exits_long' : exits[0],'exits_short' : exits[1]})

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