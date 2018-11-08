        
import sqlite3
import pandas as pd
import re
import nltk
import unidecode

connection = sqlite3.connect('database.db')        
cursor = connection.cursor() 

df = pd.read_sql_query("SELECT (texto_itens || texto) as texto, tipo FROM documentos", connection)        

dic_ocs = dict()

padroes = [
    'curso',
    'especializacao',
    'mba',
    'mestrado',
    'doutorado',
    'graduacao',
    'superior',
    'bacharelado',
    'congresso',
    'seminario',
    'simposio',
    'conferencia',
    'encontro',
    'convencao',
    'capacitacao',
    'lato sensu',
    'strictu sensu',
    'treinamento',
    'certificacao',
    'oficina',
    'workshop',
    'aula',    
    'ead',
    'exame',
    'avaliacao'
    ]
regex = '(?:'+('|'.join(padroes))+') \w+ \w+'

tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+') 

qtd_docs = 0
qtd_m = 0
for row in df.itertuples():
    texto = ' '.join(tokenizer.tokenize(unidecode.unidecode(row.texto.lower())))
    contem = False    
    ocs = re.findall(regex, texto)
    if len(ocs) > 0:
        contem = True
        for o in ocs:        
            if o in dic_ocs:
                dic_ocs[o] += 1
            else:
                dic_ocs[o] = 1
            qtd_m += 1
    if contem:
        qtd_docs += 1

for k,v in sorted(dic_ocs.items(), key=lambda kv:kv[1], reverse=True):
    print('%s - %d' % (k,v))

print('Documentos: '+str(qtd_docs)+'/'+str(df.size))
print(str(qtd_m)+' ocorrências.')