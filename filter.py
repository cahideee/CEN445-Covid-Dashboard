import pandas as pd

# 1. Tanımlamalar
input_file_path = 'owid-covid-data.csv' 
hedef_kita = 'Europe' 
output_file_path = 'owid-covid-data-europe-final.csv' 

# SADECE İSTENEN SÜTUNLARIN LİSTESİ (10 sütun)
columns_to_keep = [
    'continent',
    'location',
    'date',
    'total_cases',
    'new_cases',
    'total_deaths',
    'new_deaths',
    'total_tests',
    'new_tests', # Veri setindeki doğru sütun adı
    'aged_65_older'
]

# ----------------------------------------------------------------------

# 2. Veri Setini Yükleme
df = pd.read_csv(input_file_path)

# 3. Koşullu Filtreleme (Sadece Europe)
df_temiz = df[df['continent'] == hedef_kita].copy()

# 4. Sütunları Seçme (Sadece İstenen 10 Sütun)
df_final = df_temiz[columns_to_keep]

# 5. Yeni veri setini kaydetme
df_final.to_csv(output_file_path, index=False)