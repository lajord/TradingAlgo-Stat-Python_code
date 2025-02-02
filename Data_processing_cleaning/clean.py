import pandas as pd
df = pd.read_csv(r"C:\Users\Jordi\Desktop\ALGO\algo\DATA\es-30m_bk\SP30min_2024.csv")
df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['time'])
df = df.sort_values('Datetime')
df.drop(columns=['Datetime'], inplace=True)
df.to_csv("SP30min_2024_sorted.csv", index=False)
