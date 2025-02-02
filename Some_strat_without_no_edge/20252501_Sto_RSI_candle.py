import numpy as np
import pandas as pd 
import vectorbt as vbt
import talib 
import matplotlib.pyplot as plt 
import sys
import os
function_essential_path = r"H:\Desktop\Environement_Trading_Developement\FunctionEssential"
sys.path.append(function_essential_path)
# Importer utils.py
import utils as us
import talib 

#################################################################################################################

"""
Création des fonctions python pour les indicateurs 
=> MA ,RSI, ATR etc etc calculer avec les outils a disposition ! vectorbt
"""


def is_hammer(close, high, low, open):
    # Calcul des composantes de la bougie
    body_size = abs(close - open)
    upper_shadow = high - max(open, close)
    lower_shadow = min(open, close) - low
    is_red = open > close  # True = bougie rouge (Open > Close)

    if (not is_red) and (lower_shadow >= 2 * body_size) and (upper_shadow <= 0.1 * body_size):
        return 1  # Hammer détecté
    
    # Vérification Inverted Hammer (bougie verte ou doji)
    elif (not is_red) and (upper_shadow >= 2 * body_size) and (lower_shadow <= 0.1 * body_size):
        return 2  # Inverted Hammer détecté
    # Aucun pattern détecté
    else:
        return 3



def is_shootingstar_hangingman(close, high, low, open):
    body_size = abs(close - open)
    upper_shadow = high - max(open, close)
    lower_shadow = min(open, close) - low
    is_red = open > close  
    # Conditions pour Hanging Man (bougie rouge, tendance haussière)
    hanging_man = (
        is_red
        and (lower_shadow >= 2 * body_size)  # Longue mèche inférieure
        and (upper_shadow <= 0.1 * body_size)  # Mèche supérieure quasi nulle
    )
    shooting_star = (
        is_red  # Bougie verte ou doji (Close >= Open)
        and (upper_shadow >= 2 * body_size)  # Longue mèche supérieure
        and (lower_shadow <= 0.1 * body_size)  # Mèche inférieure quasi nulle
    )

    if hanging_man:
        return 4  # Hanging Man détecté
    elif shooting_star:
        return 5  # Shooting Star détecté
    else:
        return 3  # Rien
    


def trend_cross(close, MA200, lookback):
    cross = [0] * len(close)  
    for i in range(len(close)):
        if i >= lookback - 1:  
            window_start = i - lookback + 1
            window_end = i + 1  
            all_above = all(close.iloc[window_start:window_end] > MA200.iloc[window_start:window_end])
            all_below = all(close.iloc[window_start:window_end] < MA200.iloc[window_start:window_end])
            
            if all_above:
                cross[i] = 1  # Bull
            elif all_below:
                cross[i] = 2  # Bear
            else:
                cross[i] = 3  # Range
        else:
            cross[i] = 0  # Non défini pour les premières valeurs
    return np.array(cross)


def point_pivot(close, high, low, nbr_pivot):
    pivot_collection = []
    pivot_support_0 = (close + high + low) / 3
    pivot_collection.append(pivot_support_0)
    pivot_resistance_0 = (close + high + low) / 3
    pivot_collection.append(pivot_resistance_0)
    pivot_support_1 = 2 * pivot_support_0 - high
    pivot_resistance_1 = 2 * pivot_support_0 - low
    pivot_collection.append(pivot_support_1)
    pivot_collection.append(pivot_resistance_1)
    for i in range(2, nbr_pivot):
        pivot_support_i = pivot_support_0 - (high - low) * (i - 1)
        pivot_resistance_i = pivot_support_0 + (high - low) * (i - 1)
        pivot_collection.append(pivot_support_i)
        pivot_collection.append(pivot_resistance_i)
    point_pivot_array = np.array(pivot_collection).T
    point_pivot_array = np.squeeze(point_pivot_array)
    return point_pivot_array





###################################################################################################################


"""
Création des fonctions d'entrée et de sortie 
"""

def entries(is_hammer,is_shootingstar_hangingman,trend,rsi,stock_k,stock_d):

    long_entries = (
        ((is_hammer == 1) | (is_hammer == 2)) &   # 1=Hammer, 2=Inverted Hammer          # 1=Tendance Bull 
        (stock_k < 20) & 
        (stock_d < 20) & 
        (rsi < 30)
    )

    short_entries = (
        ((is_shootingstar_hangingman == 4) | (is_shootingstar_hangingman == 5)) &   # 1=Hammer, 2=Inverted Hammer                           # 2=Tendance Bear 
        (stock_k > 80) & 
        (stock_d > 80) & 
        (rsi > 70)
    )

    return long_entries,short_entries


def exits(close,high,low, long, short, point_pivot_df):

    exits_long = [False] * len(long)
    exits_short = [False] * len(short)

    for i in range(len(close)):
        if long[i]:
            # Utilisation de .iloc pour l'accès positionnel
            SL = point_pivot_df['pivot_support_2'].iloc[i]
            TP = point_pivot_df['pivot_resistance_3'].iloc[i]
            
            # Vérification des valeurs NaN
            if pd.isna(SL) or pd.isna(TP):
                continue
                
            for j in range(i + 1, len(close)):
                if low[j] <= SL or high[j] >= TP:
                    exits_long[j] = True
                    break  # Sortie après la première occurrence

        if short[i]:
            SL = point_pivot_df['pivot_resistance_2'].iloc[i]
            TP = point_pivot_df['pivot_support_3'].iloc[i]
            
            if pd.isna(SL) or pd.isna(TP):
                continue
                
            for j in range(i + 1, len(close)):
                if high[j] >= SL or low[j] <= TP:
                    exits_short[j] = True
                    break

    return exits_long, exits_short


####################################################################################################################
"""
Création des Indicator Factory
"""



class Strategie():


    def __init__(self,data,frequence,list_tickers):
        self.data = data
        self.frequence = frequence
        self.list_tickers = list_tickers


    def backtest(self,period_start,period_end):
        if (period_end == 0) and (period_start == 0):

            long_df = pd.DataFrame()
            short_df = pd.DataFrame()
            long_exits_df = pd.DataFrame()
            short_exits_df = pd.DataFrame()
            close_df = pd.DataFrame()

            for ticker in self.list_tickers:
                data = self.data[ticker]
                liste_value = self.make_value_no_combi(data['high'],data['low'],data['close'],data.index)
                data["is_hammer"] = data.apply(
                    lambda row: is_hammer(row["close"], row["high"], row["low"], row["open"]), axis=1
                )
                data["is_shootingstar_hangingman"] = data.apply(
                    lambda row: is_shootingstar_hangingman(row["close"], row["high"], row["low"], row["open"]), axis=1
                )



                    
                long,short = self.make_entries(data["is_hammer"],data["is_shootingstar_hangingman"],liste_value[3],liste_value[0],liste_value[1],liste_value[2])
                exits_long,exits_short = self.make_exits(data['close'],data['high'],data['low'],long,short,liste_value[4])





                #Reset les index pour tout normaliser
                

                long = long.reset_index(drop=True)
                short = short.reset_index(drop=True)
                exits_long = pd.Series(exits_long).reset_index(drop=True)
                exits_short = pd.Series(exits_short).reset_index(drop=True)
                close = data['close'].reset_index(drop=True)
                #enregistrer dans des dataframes 
                long_df[ticker] = long
                short_df[ticker] = short
                long_exits_df[ticker] = exits_long
                short_exits_df[ticker] = exits_short
                close_df[ticker] = close

            #remplacer les 0 qui ont état mis durant import data
            close_df = close_df.replace(0, None).fillna(method='ffill')
            portfolio = vbt.Portfolio.from_signals(
                close_df,
                long_df,
                long_exits_df,
                short_df,
                short_exits_df,
                init_cash=10000,
                freq=self.frequence
            )
            us.get_pnl(portfolio)
            return portfolio
        



    
    def make_entries(self,is_hammer,is_shootingstar_hangingman,trend,rsi,stock_k,stock_d):
        long,short = entries(is_hammer,is_shootingstar_hangingman,trend,rsi,stock_k,stock_d)
        return long,short
    

    def make_exits(self,close,high,low,long,short,point_pivot_df):
        exits_long,exits_short = exits(close,high,low,long,short,point_pivot_df)
        return exits_long,exits_short

    
    def make_value_no_combi(self,high,low,close,datetime):

        RSI = vbt.RSI.run(close,window=14).rsi
        STOCH = vbt.STOCH.run(high,low,close,k_window=14,d_window=3)
        MA200 = vbt.MA.run(close,window=200).ma
        trend_state = trend_cross(close,MA200,20)

        data_weekly = us.get_data_forex(['USDJPY'],'W1','2005-01-01','2025-01-01')
        data_weekly = data_weekly['USDJPY']
        point_pivot_value = point_pivot(data_weekly['close'],data_weekly['high'],data_weekly['low'],4)
        columns = []
        count = 0
        for i in range(point_pivot_value.shape[1]):
            if i % 2 == 0:
                columns.append(f"pivot_support_{count}") 
            else:
                columns.append(f"pivot_resistance_{count}") 
                count += 1
        point_pivot_df = pd.DataFrame(point_pivot_value,columns=columns,index=data_weekly.index)
        point_pivot_df.index = pd.to_datetime(point_pivot_df.index)
        datetime = pd.to_datetime(datetime)
        point_pivot_df = point_pivot_df.reindex(datetime, method='ffill')

        return [RSI,STOCH.percent_k,STOCH.percent_d,trend_state,point_pivot_df]



        
    


tickers = ['USDJPY']
data = us.get_data_forex(tickers,'H1','2005-01-01','2025-01-01')
strat = Strategie(data,"60m",tickers)
strat.backtest(0,0)