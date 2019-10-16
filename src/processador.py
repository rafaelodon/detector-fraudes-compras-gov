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
import pickle
import constantes

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import TfidfVectorizer

class Processador:
    '''
        Classe responsável por processar o texto dos documentos gravados no banco
    '''

    REMOVER = ['pregao eletronico', 'pregao', 'aquisicao', 'valor', 'limite', 
        'licitacao', 'licitacao', 'justificativa', 'edital', 'contratacao', 'fornecimento', 
        'prestacao', 'precos', 'preco', 'formacao', 'empresa', 'servico', 'servicos',
        'inscricao', 'pagamento', 'taxa', 'para', 'objeto']  

    SUBSTITUIR = [('emp resa', 'empresa')]

    def __init__(self, db=None):        
        if db is None:
            self.db = constantes.ARQ_BANCO
        
        self.stem_count = dict()
        self.word_count = dict()           
        self.unidas_count = dict()
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()    
        self.stemmer = RSLPStemmer()
        self.tokenizer = RegexpTokenizer(r'\w+')                
    
    def __is_number(self, s):
        try:            
            int(str(s).strip())
            return True
        except:
            return False    

    def __gerar_vocabulario(self):           
        
        if os.path.exists(constantes.ARQ_VOCABULARIO):
            logging.debug('Carregando o arquivo de vocabulário de palavras de '+constantes.ARQ_VOCABULARIO)
            with open(constantes.ARQ_VOCABULARIO, 'rb') as file:
                self.word_count = json.loads(file.read().decode('utf-8'))
        else:
            logging.info("Gerando vocabulário a partir dos documentos.")
            df = pd.read_sql_query("SELECT (texto_itens || texto) as texto FROM documentos", self.connection)                        
            for row in df.itertuples():
                
                input = row.texto

                # passa para minúsculo e remove acentos
                output = unidecode.unidecode(input.lower())
                
                # adiciona palavras no vocabulário            
                for w in self.tokenizer.tokenize(output): 

                    #ignora tokens numéricos
                    if self.__is_number(w):
                        continue
                    
                    if w in self.word_count:
                        self.word_count[w] += 1
                    else:
                        self.word_count[w] = 1
            
            logging.debug("Gravando vocabulário em "+constantes.ARQ_VOCABULARIO)
            with codecs.open(constantes.ARQ_VOCABULARIO, 'wb', 'utf-8') as file:
                file.write(json.dumps(self.word_count))

        logging.info("O vocabulário possui "+str(len(self.word_count))+" palavras distintas.")

    def __pre_processar(self, input):           

        # passa para minúsculo
        output = input.lower()

        # remove acentos
        output = unidecode.unidecode(output)

        # deixa todas as palavras separadas por 1 espaço e remove numeros
        tokens = []        
        for w in self.tokenizer.tokenize(output): 
            #ignora tokens numéricos
            if self.__is_number(w):
                continue   
            tokens.append(w)            
        output =  ' '.join(tokens)

        # remove palavras muito gerais do domínio licitação/pregão/compras
        for item in self.REMOVER:
            output = output.replace(item,'')   

        # faz alguns substituições manuais
        for item in self.SUBSTITUIR:
            output = output.replace(item[0], item[1])
        
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
                    if(self.word_count[pm] > self.word_count[p1]/4 and
                        self.word_count[pm] > self.word_count[p2]/4):
                        merge=True
                except KeyError:
                    pass
                if merge:
                    unida = p1+"+"+p2                    
                    if unida in self.unidas_count:
                        self.unidas_count[unida] += 1
                    else:
                        logging.debug("Unindo "+unida)
                        self.unidas_count[unida] = 1
                    tokens[i] = ''
                    tokens[i+1] = pm
                    i+=1 # pula a próxima palavra pois fez parte do merge                        
            i+=1
             
        output =  ' '.join(tokens)
        
        # faz stemmer preservando as contagens de palavras originais para recuperar a top-palavra
        tokens = []        
        for w in self.tokenizer.tokenize(output):            

            #pula palavras com tamanho 2 ou menos
            if(len(w) <= 2):
                continue

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

    def __undo_stemming(self, word):     

        # se for mais de uma palavra, chama recursivo
        if word.strip().find(' ') != -1:
            return ' '.join([self.__undo_stemming(w) for w in word.strip().split(' ')])

        # descobre a top-palavra do stem
        if word not in self.stem_count:
            self.stem_count[word] = { '__top__' : word }
        if '__top__' not in self.stem_count[word]:            
            count = self.stem_count[word]            
            self.stem_count[word]['__top__'] = max(count, key=count.get)            

        return self.stem_count[word]['__top__']           

    def processar_texto(self):                
        
        self.__gerar_vocabulario()        

        df = pd.read_sql_query("SELECT id, (texto_itens || texto) as texto, valor FROM documentos", self.connection)
        
        # pre processa o texto gerando uma sequencia de tokens com stemming
        # separados por espaço
        df['tokens_stem'] = df['texto'].apply(lambda t:(self.__pre_processar(t)))

        # pre processo o texto passando cada stemming na sua top-palavra representativa        
        df['tokens_top_palavra'] = df['tokens_stem'].apply(lambda t:(self.__undo_stemming(t)))

        # grava a forma final dos tokens no banco        
        try:
            self.cursor.execute("ALTER TABLE documentos ADD COLUMN texto_processado TEXT CLOB;")
        except sqlite3.OperationalError:
            logging.debug("A coluna texto_processado já existe.")                                
        for row in df.itertuples():
            sql = "UPDATE documentos SET texto_processado = ? WHERE id = ?"
            self.cursor.execute(sql, (row.tokens_top_palavra, row.id))            
        self.connection.commit()
    
        logging.debug('Calculando IDF das palavras dos documentos')                                
        df = pd.read_sql_query("SELECT texto_processado FROM documentos", self.connection)                        
        self.stem_count = dict()            
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            min_df=0,
            max_df=0.99,
            preprocessor=None, # já foi processado antes e gravado no banco
            tokenizer=self.tokenizer.tokenize,
            stop_words=stopwords.words('portuguese')
        ) 
        vectorizer = self.vectorizer.fit(df['texto_processado'])

        logging.debug("Gravando vectorizer em "+constantes.ARQ_VECTORIZER)
        with open(constantes.ARQ_VECTORIZER, 'wb') as file:
            pickle.dump(vectorizer, file)        

    def atualizar_valores_com_selic(self):

        logging.info("Atualizando valores das compras com a SELIC")
        
        try:
            self.cursor.execute("ALTER TABLE documentos ADD COLUMN valor_atualizado DOUBLE;")
        except sqlite3.OperationalError:
            logging.debug("A coluna valor_atualizado já existe.")                                

        df1 = pd.read_sql_query("SELECT id, data, valor FROM documentos", self.connection)                        
        for compra in df1.itertuples():
            df2 = pd.read_sql_query("SELECT valor FROM selic WHERE data_inicio >= ? ORDER BY data_inicio", self.connection, params=[compra.data])                        
            valor_ajustado = compra.valor
            for selic in df2.itertuples():
                valor_ajustado = valor_ajustado * (1+(selic.valor/100))
            logging.debug("Atualizou de %.2f para %.2f" % (compra.valor, valor_ajustado))                   
            self.cursor.execute("UPDATE documentos SET valor_atualizado = ? WHERE id = ?", (valor_ajustado, compra.id))                        
        self.connection.commit()
        
        