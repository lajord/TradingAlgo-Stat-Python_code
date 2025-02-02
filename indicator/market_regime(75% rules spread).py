import pandas as pd
import numpy as np
import plotly.graph_objects as go

"""
LAW OF REVERSION
Source : Statistical Arbitrage Andrew Pole 

L'objectif de cette indicateur c'est d'essayer d'isoler les périodes de range / chop / mean reversion des périodes de tendances 
L'indicateur ce base sur la règle des 75% expliquer dans le livre

l'indicateur aura une seuil au 75 et une valeur entière possitive comprise entre 0 et 100 inclus 

Fenetre loockback = 150

"""


def market_regime(close, windows):
    # S'assurer que close est un Series
    if isinstance(close, np.ndarray):
        close = close.squeeze()
        close = pd.Series(close)

    # Calcul de la moyenne mobile
    spreads = close.diff().dropna()  # Différences entre fermetures
    moving_average = spreads.rolling(window=windows).mean()

    market_regime_value = []

    # Boucle principale
    for i in range(windows * 2, len(close)):  # Démarrer après 2*windows
        # Fenêtre locale
        window_data = close[i - windows:i]
        spreads = window_data.diff().dropna()
        current_moving_average = moving_average[i - windows:i].dropna()

        # Vérification
        verification = 0
        for j in range(len(spreads)):  # Index local
            spread_t_minus_1 = spreads.iloc[j - 1] if j > 0 else np.nan
            spread_t = spreads.iloc[j]
            if spread_t_minus_1 > spread_t:
                verification += 1 if spread_t_minus_1 > current_moving_average.iloc[j] else 0
            else:
                verification += 1 if spread_t_minus_1 < current_moving_average.iloc[j] else 0

        # Calcul de la probabilité
        proba = (verification / windows) * 100
        market_regime_value.append(proba)

    # Ajouter des NaN initiaux
    market_regime_value = [np.nan] * (windows * 2) + market_regime_value
    market_regime_value = np.array(market_regime_value)
    market_regime_smoothed = pd.Series(market_regime_value).rolling(window=1, min_periods=1).mean()  #Lisser le prix du market regime -> J'ai mis le params a 1 la 


    return market_regime_smoothed


