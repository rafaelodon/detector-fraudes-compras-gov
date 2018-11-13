# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json
import sqlite3
import pandas as pd
import operator
import unidecode
import os
import math
import string
import codecs

from nltk.corpus import stopwords, mac_morpho
from nltk.tokenize import word_tokenize, RegexpTokenizer
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split  
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import cross_val_score

import gensim 

import matplotlib.pyplot as plt

from wordcloud import WordCloud

import pickle

class Processador:

    REMOVER = ['pregao eletronico', 'pregao', 'aquisicao', 'valor', 'limite', 
        'licitacao', 'licitacao', 'justificativa', 'edital', 'contratacao', 'fornecimento', 
        'prestacao', 'precos', 'preco', 'formacao', 'empresa', 'servico', 'servicos',
        'inscricao', 'pagamento', 'taxa', 'para', 'objeto']  

    def __init__(self, db=None):        
        if db is None:
            self.db = 'database.db'
        
        self.stem_count = dict()
        self.word_count = dict()           
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()    
        self.stemmer = RSLPStemmer()
        self.tokenizer = RegexpTokenizer(r'\w+')                

    def vetorizar(self):        
        logging.debug('Calculando TF-IDF das palavras dos documentos')                    
        df = pd.read_sql_query("SELECT texto_processado FROM documentos", self.connection)                        
        self.stem_count = dict()            
        self.vectorizer = TfidfVectorizer(
            max_features=1500,
            min_df=5,
            max_df=0.7,
            preprocessor=None, # já foi processado antes
            tokenizer=self.tokenizer.tokenize,
            stop_words=stopwords.words('portuguese')
        ) 
        return self.vectorizer.fit_transform(df['texto_processado'])

    def is_number(self, s):
        try:            
            int(str(s).strip())
            return True
        except:
            return False    

    def gerar_vocabulario(self):           
        arquivo_vocabulario = './cache/word_count.json'
        if os.path.exists(arquivo_vocabulario):
            logging.debug('Carregando o arquivo de vocabulário de palavras de '+arquivo_vocabulario)
            with open(arquivo_vocabulario, 'rb') as file:
                self.word_count = json.loads(file.read().decode('utf-8'))
        else:
            logging.info("Gerando vocabulário a partir dos documentos.")
            df = pd.read_sql_query("SELECT (texto_itens || texto) as texto FROM documentos", self.connection)                        
            for idx, row in df.itertuples():
                
                input = row.texto

                # passa para minúsculo e remove acentos
                output = unidecode.unidecode(input.lower())
                
                # adiciona palavras no vocabulário            
                for w in self.tokenizer.tokenize(output): 

                    #ignora tokens numéricos
                    if self.is_number(w):
                        continue
                    
                    if w in self.word_count:
                        self.word_count[w] += 1
                    else:
                        self.word_count[w] = 1
            
            with codecs.open(arquivo_vocabulario, 'wb', 'utf-8') as file:
                file.write(json.dumps(self.word_count))

        logging.info("O vocabulário possui "+str(len(self.word_count))+" palavras distintas.")

    def pre_processar(self, input):           

        # passa para minúsculo
        output = input.lower()

        # remove acentos
        output = unidecode.unidecode(output)

        '''
        # faz algumas substituições para consertar palavras mal formatadas/quebradas
        output = ' '.join(output.split()) # transforma espaços múltiplos em 1 espaço apenas antes de substituir
        for item in self.SUBSTITUIR:
            output = output.replace(item[0], item[1])
        '''

        # remove palavras muito gerais do domínio licitação/pregão/compras
        for item in self.REMOVER:
            output = output.replace(item,'')   

        tokens = []        
        for w in self.tokenizer.tokenize(output): 
            #ignora tokens numéricos
            if self.is_number(w):
                continue   
            tokens.append(w)            
        output =  ' '.join(tokens)          
        
        # tenta resolver problema das palavras picadas verificando se a soma de 
        # palavras adjacentes forma uma palavra válida
        tokens = self.tokenizer.tokenize(output)
        i=0
        while i < len(tokens)-1:            
            p1 = tokens[i]            
            p2 = tokens[i+1]
            pm = p1+p2
            if((len(p1) <= 4 or len(p2) <=4) and
                pm in self.word_count):
                merge=False
                try:
                    if(self.word_count[pm] > self.word_count[p1]/2 and
                        self.word_count[pm] > self.word_count[p2]/2):
                        merge=True
                except KeyError:
                    pass
                if merge:
                    logging.debug("Unindo "+p1+"+"+p2)
                    tokens[i] = ''
                    tokens[i+1] = pm
                    i+=1 # pula a próxima palavra pois fez parte do merge                        
            i+=1
             
        output =  ' '.join(tokens)
        
        # faz stemmer preservando as contagens de palavras originais para recuperar a top-palavra
        tokens = []        
        for w in self.tokenizer.tokenize(output):            
            stem = self.stemmer.stem(w)                        
            if stem in self.stem_count:
                if w in self.stem_count[stem]:
                    self.stem_count[stem][w] += 1
                else:
                    self.stem_count[stem][w] = 1
            else:
                self.stem_count[stem] = { w : 1 }            
            
            tokens.append(stem)    
        
        output =  ' '.join(tokens)
        
        #logging.debug('['+input[:50]+'] -> ['+output[:50]+']')
        return output

    def undo_stemming(self, word):     

        # se for mais de uma palavra, chama recursivo
        if word.strip().find(' ') != -1:
            return ' '.join([self.undo_stemming(w) for w in word.strip().split(' ')])

        # descobre a top-palavra do stem
        if word not in self.stem_count:
            self.stem_count[word] = { '__top__' : word }
        if '__top__' not in self.stem_count[word]:            
            count = self.stem_count[word]            
            self.stem_count[word]['__top__'] = max(count, key=count.get)            

        return self.stem_count[word]['__top__']           

    def processar_texto(self):                
        
        self.gerar_vocabulario()        

        df = pd.read_sql_query("SELECT id, (texto_itens || texto) as texto, valor FROM documentos", self.connection)                        
        
        # pre processa o texto gerando uma sequencia de tokens com stemming
        # separados por espaço
        df['tokens_stem'] = df['texto'].apply(lambda t:(self.pre_processar(t)))

        # pre processo o texto passando cada stemming na sua top-palavra representativa        
        df['tokens_top_palavra'] = df['tokens_stem'].apply(lambda t:(self.undo_stemming(t)))

        # grava a forma final dos tokens no banco        
        try:
            self.cursor.execute("ALTER TABLE documentos ADD COLUMN texto_processado TEXT CLOB;")
        except sqlite3.OperationalError:
            logging.debug("A coluna texto_processado já existe.")                                
        for row in df.itertuples():
            sql = "UPDATE documentos SET texto_processado = ? WHERE id = ?"
            self.cursor.execute(sql, (row.tokens_top_palavra, row.id))            
        self.connection.commit()

    def tratar_frequencia(self, value):
        if math.isnan(value):
            return 0.0
        else:
            return value
