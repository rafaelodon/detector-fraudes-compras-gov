        
import sqlite3
import pandas as pd
import re


connection = sqlite3.connect('database.db')        
cursor = connection.cursor() 

df = pd.read_sql_query("SELECT (texto_itens || texto) as texto, tipo FROM documentos", connection)        

qtd_docs = 0
qtd_m = 0
for row in df.itertuples():
    ocs = re.findall('curso de \w+', row.texto.lower())
    if len(ocs) > 0:
        qtd_docs += 1
        for o in ocs:        
            print(o)
            qtd_m+=1

print('Documentos: '+str(qtd_docs)+'/'+str(df.size))
print(str(qtd_m)+' ocorrências.')