import pandas as pd
import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
import scipy.stats as stats
from scipy.optimize import differential_evolution
from statsmodels.api import OLS 
import datetime





def method_moment(X, dt):
    X = np.ravel(X)
    deltaX = np.diff(X)
    X = X[:-1]
    mu = X.mean()
    exog = (mu - X) * dt
    mode1 = OLS(endog=deltaX, exog=exog)
    res = mode1.fit()
    theta = res.params[0]
    resid = deltaX - theta * exog
    sigma = resid.std() / np.sqrt(dt)
    return theta, mu, sigma


def sigma_eqq(sigma,theta):
    return sigma/np.sqrt(2*theta)

def s_score(mu,sigma,theta,X):
    sigmaeqq = sigma_eqq(sigma,mu)
    return (X-mu) / sigmaeqq



def mean_reversion(close,windows):

    theta_vals = []
    mu_vals = []
    sigma_vals = []
    value_s_score=[]
    dt = 1.0/len(close)


    # # Estimation des parametres
    for i in range(len(close) - windows + 1):
        window_data = close[i:i + windows]
        theta, mu, sigma = method_moment(window_data, dt)
        theta_vals.append(theta)
        mu_vals.append(mu)
        sigma_vals.append(sigma)

    theta_vals = [np.nan] * (windows - 1) + theta_vals
    mu_vals = [np.nan] * (windows - 1) + mu_vals
    sigma_vals = [np.nan] * (windows - 1) + sigma_vals

    # Calcul du S-score sur la fenetre prédef
    for i in range(windows, len(close)):
        theta =  theta_vals[i]
        sigma =  sigma_vals[i]
        mu = mu_vals[i]
        X = close[i]
        score = s_score(mu, sigma, theta, X)
        value_s_score.append(score)

    value_s_score = [np.nan] * (windows) + value_s_score
    value_s_score = pd.Series(value_s_score).rolling(window=10).mean()

    df = pd.DataFrame({'S_Score': value_s_score})
    df['MA30'] = df['S_Score'].rolling(window=50).mean()

    #Ajout de la upper band et de la lower band
    rolling_window = 200
    df['Mean'] = df['S_Score'].rolling(window=rolling_window).mean()
    df['Std'] = df['S_Score'].rolling(window=rolling_window).std()
    df['Upper_Band'] = df['Mean'] + 2.5 * df['Std']    ## IMPORTANT => Ici je calcul la moyenne et apres je fais + et - mais théoriquement la moyenne est de 0 donc si les résultats sont moyen juste ne calcul pas la moyenne et j'ai 0 - + std 1,5
    df['Lower_Band'] = df['Mean'] - 2.5 * df['Std']
    df = df.drop(columns=['Mean', 'Std'])

    return df['S_Score'],df['MA30'],df['Upper_Band'],df['Lower_Band']

### df a 4 colonnes -> s-score | s-score ma 30 | Upper_Band | Lower_Band


"""

Le dataframe doit avoir
s-score | s-score ma 30 | std sup 1.5 | std inf 1.5

 tu calculs les ecart type sur une fenetres mais ca peut pas etre la meme que celle pour le calcul du s-score.. car y'a besoin de beaucoup d'échantillon au moins 1 année soit

 parcourir le s-score sur une fenetre de 200 pour ensuite le mettre dans le dataframe final.. 


"""