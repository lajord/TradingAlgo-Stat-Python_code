# Indicateur de tendance #
# Indicateur propriétaire Jordi Oszust #
# 2024-11 #

import pandas as pd
import numpy as np



def ichimoku_leading_span_a(data,period_base_line,period_conversion_line,deplacement):

    conversion_line = (data['high'].rolling(window=period_conversion_line).max() +
                       data['low'].rolling(window=period_conversion_line).min()) / 2
    
    # Calcul de la Base Line (Kijun-sen)
    base_line = (data['high'].rolling(window=period_base_line).max() +
                 data['low'].rolling(window=period_base_line).min()) / 2
    
    # Calcul de Leading Span A
    leading_span_a = (conversion_line + base_line) / 2

    # Ajout des deux colonnes avec décalage
    data['spanA_1'] = leading_span_a.shift(1)
    data['spanA_2'] = leading_span_a.shift(deplacement)
    return data

