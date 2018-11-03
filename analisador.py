# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json
import sqlite3
import pandas as pd
import operator
import unidecode

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split  
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import cross_val_score

import gensim 
from gensim.corpora.dictionary import Dictionary
from gensim.utils import simple_preprocess 
from gensim.parsing.preprocessing import STOPWORDS

import matplotlib.pyplot as plt

from wordcloud import WordCloud

import pickle

class Analisador:

    REMOVER = ['pregao eletronico', 'pregao', 'aquisicao', 'valor', 'limite', 
        'licitacao', 'licitacao', 'justificativa', 'edital', 'contratacao', 'fornecimento', 
        'prestacao', 'precos', 'preco', 'formacao', 'empresa', 'servico', 'servicos',
        'inscricao', 'pagamento', 'taxa', 'para']

    SUBSTITUIR = [('emp resa','empresa'), ('mater ial', 'material'), 
        ('p rofissional', 'profissional')]    

    def __init__(self, db=None):        
        if db is None:
            self.db = 'database.db'
        
        self.stem_count = dict()
        self.stem_top = dict()
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()    
        self.stemmer = RSLPStemmer()
        self.vectorizer = TfidfVectorizer(
            max_features=1500,
            min_df=5,
            max_df=0.99,
            #ngram_range=(1,3),
            preprocessor=self.pre_processar,
            stop_words=stopwords.words('portuguese')
        ) 

    def pre_processar(self, input):           

        # passa para minúsculo
        output = input.lower()

        # remove acentos
        output = unidecode.unidecode(output)

        # faz algumas substituições para consertar palavras mal formatadas/quebradas
        for item in self.SUBSTITUIR:
            output = output.replace(item[0], item[1])

        # remove palavras muito gerais do domínio licitação/pregão/compras
        for item in self.REMOVER:
            output = output.replace(item,'')        

        # faz stemming guardando a contagem de palavras por radical (a nuvem usará a top palavra)    
        tokens = word_tokenize(output)
        texto_stemmed = ''
        for w in tokens:            
            stem = self.stemmer.stem(w)            
            if stem in self.stem_count:
                if w in self.stem_count[stem]:
                    self.stem_count[stem][w] += 1
                else:
                    self.stem_count[stem][w] = 1
            else:
                self.stem_count[stem] = { w : 1 }            
            texto_stemmed += stem + ' '        
        output = texto_stemmed
            
        #logging.debug('['+input[:50]+'] -> ['+output[:50]+']')

        return output

    def undo_stemming(self, word):     

        # se for mais de uma palavra, chama recursivo
        if word.strip().find(' ') != -1:
            return ' '.join([self.undo_stemming(w) for w in word.strip().split(' ')])

        # se o stem não tiver tipo sua top palavra descoberta ainda, descobre...
        if word not in self.stem_top:        
            if word in self.stem_count:                
                count = self.stem_count[word]            
                self.stem_top[word] = max(count, key=count.get)
            else:
                self.stem_top[word] = word
        
        return self.stem_top[word]

    def analisar_topicos(self):
        '''
        Usar LDA:
        https://towardsdatascience.com/topic-modeling-and-latent-dirichlet-allocation-in-python-9bf156893c24
        https://rstudio-pubs-static.s3.amazonaws.com/79360_850b2a69980c4488b1db95987a24867a.html
        https://www.machinelearningplus.com/nlp/topic-modeling-gensim-python/
        https://www.analyticsvidhya.com/blog/2016/08/beginners-guide-to-topic-modeling-in-python/
        
        '''

    def gerar_tagclouds(self):
        self.gerar_tagcloud_tipo('compra')
        self.gerar_tagcloud_tipo('licitacao')

    def gerar_tagcloud_tipo(self, tipo):        
        '''
        https://hampao.wordpress.com/2016/04/08/building-a-wordcloud-using-a-td-idf-vectorizer-on-twitter-data/
        '''
        logging.info('Gerando nuvem de tags para o tipo '+tipo)

        sql = 'SELECT (texto || texto_itens) as texto,tipo FROM documentos WHERE tipo="'+tipo+'"'
        df = pd.read_sql_query(sql, self.connection)
        
        self.stem_count = dict()
        self.stem_top = dict()           
        tfidf_matrix = self.vectorizer.fit_transform(df['texto'], y=df['tipo'])                

        freqs = { self.undo_stemming(word) : tfidf_matrix.getcol(idx).sum() for word, idx in self.vectorizer.vocabulary_.items()}

        # Imprime as TOP 10 palavras
        i=1
        for key, value in sorted(freqs.items(), key=lambda kv: kv[1], reverse=True):
            print('%d - %s (freq=%f' % (i,key,value))
            i+=1
            if(i > 25):
                break

        # Gera o arquivo com a tagcloud
        w = WordCloud(width=1024, height=768, mode='RGBA', background_color='white', max_words=100).fit_words(freqs)
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
        df = pd.read_sql_query("SELECT (texto_itens || texto) as texto, tipo FROM documentos", self.connection)        

        logging.debug('Calculando TF-IDF das palavras dos documentos')        
        self.stem_count = dict()
        self.stem_top = dict()
        tdm = self.vectorizer.fit_transform(df['texto'], y=df['tipo'])
        X = tdm.toarray()
        y = df['tipo']

        logging.debug("Separando conjunto de teste e treino")        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=0)  

        logging.debug("Treinando classificador Random Forest")
        class1 = self.treinar_testar(RandomForestClassifier(n_estimators=10, random_state=0), X_train, X_test, y_train, y_test)

        logging.debug("Treinando classificador Naive Bayes")
        class2 = self.treinar_testar(GaussianNB(), X_train, X_test, y_train, y_test)                        
        self.lista_features_importantes(class2)

    def treinar_testar(self, classifier, X_train, X_test, y_train, y_test):
        classifier.fit(X_train, y_train)
        y_pred = classifier.predict(X_test) 

        logging.debug("Matriz de confusão:")
        print(confusion_matrix(y_test,y_pred))

        logging.debug("Matriz de confusão:")
        print(classification_report(y_test,y_pred))          

        logging.debug('Acurácia: '+str(accuracy_score(y_test, y_pred)))

        return classifier        

    def lista_features_importantes(self, classifier, n=20):
        class_labels = classifier.classes_
        feature_names = self.vectorizer.get_feature_names()
        topn_class1 = sorted(zip(classifier.theta_[0], feature_names),reverse=True)[:n]
        topn_class2 = sorted(zip(classifier.theta_[1], feature_names),reverse=True)[:n]
        logging.info("Palavras importantes em "+classifier.classes_[0])
        for index, (coef, feat) in enumerate(topn_class1):
            print('%d - %s (theta=%f)' % (index+1, self.undo_stemming(feat), coef))

        logging.info("Palavras importantes em "+classifier.classes_[1])
        for index, (coef, feat) in enumerate(topn_class2):
            print('%d - %s (theta=%f)' % (index+1, self.undo_stemming(feat), coef))