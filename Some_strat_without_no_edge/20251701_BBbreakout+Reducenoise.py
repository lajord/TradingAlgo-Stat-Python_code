import vectorbt as vbt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd

import sys
import pywt
import os
chemin_parent = os.path.abspath(r'C:\Users\Jordi\Desktop\Environement de developement\Trading_Dev_Stratégie_Environement\FunctionEssential')
if chemin_parent not in sys.path:
    sys.path.append(chemin_parent)

import function_essential as fe
###################################
#Fonction indicateur
###################################


def bb(close,period_n):
    midle = vbt.MA.run(close,window=period_n).ma
    close = pd.DataFrame(close)
    std = close.rolling(window=period_n).std()
    upper = midle + 2 * std.values 
    lower = midle - 2 * std.values
    print(upper.shape)
    print(lower.shape)
    print(midle.shape)
    return lower , midle , upper


def reduce_noise(close):
    wavelet = 'sym4'  
    level = 3  
    min_val = close.min()
    max_val = close.max()
    normalized_prices = (close - min_val) / (max_val - min_val)
    coeffs = pywt.wavedec(normalized_prices, wavelet, level=level)
    threshold = np.sqrt(2 * np.log(len(normalized_prices)))  
    coeffs_thresholded = [pywt.threshold(c, threshold, mode='soft') if i > 0 else c for i, c in enumerate(coeffs)]
    denoised_prices = pywt.waverec(coeffs_thresholded, wavelet)
    denoised_prices = denoised_prices[:len(close)]  # Ajuster la taille si nécessaire
    denoised_prices = denoised_prices * (max_val - min_val) + min_val
    
    # Retourner la série complète débruitée
    return pd.Series(denoised_prices)



###################################
#Fonction entrée et sortie
###################################

def entries(close,price_denoised_series, upper_bb, lower_bb):                #Entrée super basique on peut rajouter des regles de momentum pour une strat de momentum 
    entries_long = []
    entries_short = []
    last_true_index_long = -15  
    last_true_index_short = -15  
    for i in range(len(close)):
        condition_long = price_denoised_series[i] > upper_bb[i]
        condition_short = price_denoised_series[i] < lower_bb[i]
        if condition_long:
            if i - last_true_index_long >= 15: 
                entries_long.append(True)
                last_true_index_long = i  
            else:
                entries_long.append(False)
        else:
            entries_long.append(False)
        
        if condition_short:
            if i - last_true_index_short >= 15: 
                entries_short.append(True)
                last_true_index_short = i  
            else:
                entries_short.append(False)
        else:
            entries_short.append(False)
    entries_long = np.array(entries_long)
    entries_short = np.array(entries_short)

    return entries_long, entries_short


def exits(close, entries_long, entries_short, k_ratio):
    save_indice_long = -1
    save_indice_short = -1
    exits_long = []
    exits_short = []
    max_price = 1
    min_price = 100000000

    for i in range(len(close)):
        # Gestion des entrées longues
        if entries_long[i] == True:
            save_indice_long = i
            max_price = close[i]  
            exits_long.append(False)  
        elif save_indice_long != -1:  
            if close[i] > max_price:
                max_price = close[i]
            if close[i] < max_price - (max_price * k_ratio):
                exits_long.append(True)
                save_indice_long = -1  
                max_price = 1  
            else:
                exits_long.append(False)
        else:
            exits_long.append(False)

        if entries_short[i] == True:
            save_indice_short = i
            min_price = close[i]  
            exits_short.append(False) 
        elif save_indice_short != -1:  
            if close[i] < min_price:
                min_price = close[i]
            if close[i] > min_price + (min_price * k_ratio):
                exits_short.append(True)
                save_indice_short = -1  
                min_price = 100000000 
            else:
                exits_short.append(False)
        else:
            exits_short.append(False)


    exits_long = np.array(exits_long)
    exits_short = np.array(exits_short)
    print(exits_long.shape)
    print(exits_short.shape)
    return exits_long, exits_short



###################################
#Indicator Factory
###################################

Ind_bb = vbt.IndicatorFactory(
    class_name= 'BB',
    input_names=['close'],
    param_names=['period_n'],
    output_names=['lower','midle','upper'],

).from_apply_func(bb)

Ind_entries = vbt.IndicatorFactory(
    class_name= 'entries',
    input_names=['close','price_denoised_series','upper_bb','lower_bb'],
    output_names=['entries_long','entries_short'],
).from_apply_func(entries)

Ind_exits = vbt.IndicatorFactory(
    class_name= 'exits',
    input_names=['close','entries_long','entries_short'],
    param_names=['k_ratio'],
    output_names=['exits_long','exits_short'],
).from_apply_func(exits)



###################################
#Strategie class
###################################


class Strategie():



    def __init__(self,data,frequence,list_tickers):
        self.data = data
        self.frequence = frequence
        self.list_tickers = list_tickers



    def backtest(self,period_n,k_ratio,windows_wavelet):
        entries_df_long = pd.DataFrame()
        entries_df_short = pd.DataFrame()
        exits_df_long = pd.DataFrame()
        exits_df_short = pd.DataFrame()
        close_df = pd.DataFrame()

        for ticker in self.list_tickers:
            close = self.data[ticker]['close']
            price_denoised = np.full(len(close), np.nan)
            for i in range(windows_wavelet, len(close)):
                windows_data = close.iloc[i - windows_wavelet:i]
                price_denoised_value = reduce_noise(windows_data)  
                price_denoised[i] = price_denoised_value.iloc[-1]
            price_denoised_series = pd.Series(price_denoised)
            print(price_denoised_series.shape)
            print(close.shape)

            liste_value = self.make_values(price_denoised_series,period_n)
            long,short = self.make_entries(close,price_denoised_series,liste_value[2],liste_value[0])
            long_exit,short_exit = self.make_exits(close,long,short,k_ratio)


            #Reset les index pour tout normaliser
            long = long.reset_index(drop=True)
            short = short.reset_index(drop=True)
            long_exit = long_exit.reset_index(drop=True)
            short_exit = short_exit.reset_index(drop=True)
            close = close.reset_index(drop=True)
            #enregistrer dans des dataframes 
            entries_df_long[ticker] = long
            entries_df_short[ticker] = short
            exits_df_long[ticker] = long_exit
            exits_df_short[ticker] = short_exit
            close_df[ticker] = close

        #remplacer les 0 qui ont état mis durant import data
        close_df = close_df.replace(0, None).fillna(method='ffill')
        portfolio = vbt.Portfolio.from_signals(
            close_df,
            entries_df_long,
            exits_df_long,
            short,
            short_exit,
            init_cash=100000,
            freq=self.frequence
        )

        return portfolio



    def make_values(self,price_denoised_series,period_n):
        Bolinger_band = Ind_bb.run(price_denoised_series,period_n)
        value = [Bolinger_band.lower,Bolinger_band.midle,Bolinger_band.upper]
        return value
        

    def make_entries(self,close,price_denoised_series,upper,lower):
        entries = Ind_entries.run(close,price_denoised_series,upper,lower)
        return entries.entries_long,entries.entries_short

    def make_exits(self,close, entries_long, entries_short, k_ratio):
        exits = Ind_exits.run(close,entries_long,entries_short,k_ratio)
        return exits.exits_long,exits.exits_short




tickers = ['FDAX_TOTAL_4H']
data = fe.get_data(tickers,"2015-01-01","2025-01-01")
strat = Strategie(data,"240",tickers)

portfolio = strat.backtest(20,0.01,50)

fe.get_pnl(portfolio)
