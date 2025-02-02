import numpy as np
import matplotlib.pyplot as plt
#Algo de pricing d'option en utilisant le model binomial 



#Variable

K = 120
S0 = 120
sigma=0.5
r = 0.03
T= 1
N = 20
type_ = 'C'

#j+1 pour la hausse et j pour la baisse 

def binomial_tree(K,S0,sigma,T,N,type_='C'):
    dt = T / N
    a = np.exp(r * dt)
    u = np.exp(sigma * np.sqrt(dt))
    d = np.exp(sigma * np.sqrt(dt) * -1)
    p = (a - d) / (u - d)

    disc = np.exp(-r * dt)

    S = S0 * d ** np.arange(N, -1, -1) * u ** np.arange(0,N+1,1)

    if type_=='C':
        O = np.maximum(S - K,0)
    else:
        O = np.maximum(K - S, 0)

    
    for i in np.arange(N-1,-1,-1):
        O = disc*(O[1:i+2] * p  + O[:i+1] * (1-p))

    print(O[0])
    return O[0]

binomial_tree(K,S0,sigma,T,N,type_='C')
#le résultat nous donne un prix d'option a 24,86364
