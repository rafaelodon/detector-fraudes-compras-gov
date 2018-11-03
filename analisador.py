# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json
import sqlite3
import pandas as pd

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split  
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import gensim 
from gensim.corpora.dictionary import Dictionary
from gensim.utils import simple_preprocess 
from gensim.parsing.preprocessing import STOPWORDS

import matplotlib.pyplot as plt

from wordcloud import WordCloud

class Analisador:

    REMOVER = ['pregão eletrônico', 'pregão', 'aquisição', 'valor', 'limite', 
        'licitação', 'licitacao', 'justificativa', 'edital', 'contratação', 'fornecimento', 
        'prestação', 'preços', 'preço', 'formação', 'empresa', 'serviços', 'serviço',
        'curso', 'cursos', 'inscrição', 'inscricao', 'especializada', 'pagamento',
        'servidor', 'servidores', 'taxa']

    SUBSTITUIR = [('emp resa','empresa'), ('mater ial', 'material')]

    def __init__(self, db=None):        
        if db is None:
            self.db = 'database.db'

        self.words_count = dict()
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()    

    def pre_processar(self, texto):        

        texto = texto.lower()

        for item in self.SUBSTITUIR:
            texto = texto.replace(item[0], item[1])

        for item in self.REMOVER:
            texto = texto.replace(item,'')        

        return texto
        

    def analisar_topicos(self):
        '''
        https://towarpipdsdatascience.com/topic-modeling-and-latent-dirichlet-allocation-in-python-9bf156893c24
        Usar LDA
        '''

    def gerar_tagclouds(self):
        self.gerar_tagcloud_tipo('compra')
        self.gerar_tagcloud_tipo('licitacao')

    def gerar_tagcloud_tipo(self, tipo):        
        '''
        https://hampao.wordpress.com/2016/04/08/building-a-wordcloud-using-a-td-idf-vectorizer-on-twitter-data/
        '''
        vectorizer = TfidfVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('portuguese'))
        df = pd.read_sql_query('SELECT (texto_itens || texto) as texto,tipo FROM documentos WHERE tipo="'+tipo+'"', self.connection)                
        df['texto'] = df['texto'].apply(self.pre_processar)        
        tdm = vectorizer.fit_transform(df['texto'])
        freqs = { word : tdm.getcol(idx).sum() for word, idx in vectorizer.vocabulary_.items()}
        w = WordCloud(width=800, height=600, mode='RGBA', background_color='white', max_words=100).fit_words(freqs)
        plt.imshow(w)
        plt.axis('off')
        plt.savefig('./out/tagcloud_'+tipo+'.png')

    def lda(self):        
        df = pd.read_sql_query('SELECT texto FROM documentos WHERE tipo="compra"', self.connection)                
        
        df['texto'] = df['texto'].apply(lambda t : word_tokenize(t, language='portuguese'))
        print(df['texto'][1])
        
        logging.debug("LDA")        

    def treinar_modelo(self):
        '''
        https://stackabuse.com/text-classification-with-python-and-scikit-learn/
        '''
        logging.debug('Consultando documentos')
        df = pd.read_sql_query("SELECT texto,tipo FROM documentos", self.connection)        

        logging.debug('Pre-processando texto')
        df['texto'] = df['texto'].apply(self.pre_processar)        

        y = df['tipo']

        logging.debug('Calculando TF-IDF das palavras dos documentos')
        vectorizer = TfidfVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('portuguese'))
        tdm = vectorizer.fit_transform(df['texto'])
        X = tdm.toarray()

        logging.debug("Separando conjunto de teste e treino")        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=0)  

        logging.debug("Treinando classificador")
        classifier = RandomForestClassifier(n_estimators=1000, random_state=0)  
        classifier.fit(X_train, y_train)  

        logging.debug("Testando classificador")
        y_pred = classifier.predict(X_test)  

        print(confusion_matrix(y_test,y_pred))  
        print(classification_report(y_test,y_pred))  
        print(accuracy_score(y_test, y_pred))