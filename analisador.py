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

from nltk.corpus import stopwords
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

class Analisador:

    REMOVER = ['pregao eletronico', 'pregao', 'aquisicao', 'valor', 'limite', 
        'licitacao', 'licitacao', 'justificativa', 'edital', 'contratacao', 'fornecimento', 
        'prestacao', 'precos', 'preco', 'formacao', 'empresa', 'servico', 'servicos',
        'inscricao', 'pagamento', 'taxa', 'para', 'objeto']

    SUBSTITUIR = [('emp resa','empresa'), ('emp  resa', 'empresa'), ('mater ial', 'material'), 
        ('p rofissional', 'profissional'), ('traba lho', 'trabalho'),
        ('a rtesanato', 'artesanato'), ('mater ial', 'material')]    

    def __init__(self, db=None):        
        if db is None:
            self.db = 'database.db'
        
        self.stem_count = dict()        
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()    
        self.stemmer = RSLPStemmer()
        self.tokenizer = RegexpTokenizer(r'\w+') 

        self.carregar_vectorizer()       
        

    def carregar_vectorizer(self):
        arquivo_vectorizer = './cache/tfidf_vectorizer.pickle'
        arquivo_stem_count = './cache/stem_count.json'
        if os.path.exists(arquivo_vectorizer) and os.path.exists(arquivo_stem_count):
            logging.debug('Carregando o TF-IDF Vectorizer existente de '+arquivo_vectorizer)
            with open(arquivo_vectorizer, 'rb') as file:
                self.vectorizer = pickle.load(file)
            logging.debug('Carregando o contagem dos radicais de palavras de '+arquivo_stem_count)
            with open(arquivo_stem_count, 'rb') as file:
                self.stem_count = json.loads(file.read().decode('utf-8'))
        else:
            logging.debug('Calculando TF-IDF das palavras dos documentos')                    
            df = self.obter_df_documentos()
            self.stem_count = dict()            
            self.vectorizer = TfidfVectorizer(
                max_features=1500,
                min_df=5,
                max_df=0.7,
                preprocessor=self.pre_processar,
                #tokenizer=self.tokenizar,
                stop_words=stopwords.words('portuguese')
            ) 
            self.vectorizer.fit(df['texto'], y=df['tipo'])            
            with open(arquivo_vectorizer, 'wb') as file:
                pickle.dump(self.vectorizer, file)
            with codecs.open(arquivo_stem_count, 'wb', 'utf-8') as file:
                file.write(json.dumps(self.stem_count))

    def tokenizar(self, input):
        return word_tokenize(input, language='portuguese')        

    def is_number(self, s):
        try:            
            int(str(s).strip())
            return True
        except:
            return False

    def pre_processar(self, input):           

        # passa para minúsculo
        output = input.lower()

        # remove acentos
        output = unidecode.unidecode(output)

        # faz algumas substituições para consertar palavras mal formatadas/quebradas
        output = ' '.join(output.split()) # transforma espaços múltiplos em 1 espaço apenas antes de substituir
        for item in self.SUBSTITUIR:
            output = output.replace(item[0], item[1])

        # remove palavras muito gerais do domínio licitação/pregão/compras
        for item in self.REMOVER:
            output = output.replace(item,'')        

        # faz stemming contando as palavras originais para recuperar top-palavra depois                
        tokens = []
        for w in self.tokenizer.tokenize(output): 

            #ignora tokens numéricos
            if self.is_number(w):
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

    def analisar_topicos(self):
        logging.info("Gerando modelo LDA com os documentos")
        df = self.obter_df_documentos()
        corpus = self.vectorizer.transform(df['texto']).toarray()
        dictionary = gensim.corpora.Dictionary(corpus)
        ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=5, id2word = dictionary, passes=20)
        logging.info("Tópicos encontrados pelo LDA:")
        for topic in ldamodel.print_topics(num_topics=5, num_words=4):
            logging.info(topic)

    def tratar_frequencia(self, value):
        if math.isnan(value):
            return 0.0
        else:
            return value

    def gerar_tagclouds(self):
        self.gerar_tagcloud_tipo('compra')
        self.gerar_tagcloud_tipo('licitacao')
    
    def gerar_tagcloud_tipo(self, tipo):                
        
        freqs = self.avaliar_frequencia_de_termos(tipo)

        logging.info('Gerando nuvem de tags para o tipo '+tipo)
        w = WordCloud(width=1400, height=900, mode='RGBA', background_color='white', max_words=100, margin=1).fit_words(freqs)
        plt.title('Nuvem de palavras de '+tipo)
        plt.imshow(w)        
        plt.axis('off')
        plt.savefig('./out/tagcloud_'+tipo+'.png')

    def avaliar_frequencia_de_termos(self, tipo):                

        arquivo_freqs = './cache/freqs_'+tipo+'.json'        

        if os.path.exists(arquivo_freqs):        
            logging.info('Carregando frequência já analisadas de '+arquivo_freqs)
            with open(arquivo_freqs, 'rb') as file:             
                return json.loads(file.read().decode('utf-8'))                               
        else:
            logging.info('Analisando frequência de termos para o tipo '+tipo)
            
            df = self.obter_df_documentos()
            df = df[df['tipo'] == tipo]        
            
            tfidf_matrix = self.vectorizer.transform(df['texto'])                

            freqs = { self.undo_stemming(word) : self.tratar_frequencia(tfidf_matrix.getcol(idx).sum()) for word, idx in self.vectorizer.vocabulary_.items()}
            
            with codecs.open(arquivo_freqs, 'wb', 'utf-8') as file:             
                file.write(json.dumps(freqs))            

            with open('./out/termos_'+tipo+'.csv', 'w') as file:
                for k,v in sorted(freqs.items(), key=lambda kv : kv[1], reverse=True):
                    file.write('%s  %f\n' % (k,v))
            
            return freqs

    def obter_df_documentos(self):
        df = pd.read_sql_query("SELECT (texto_itens || texto) as texto, tipo FROM documentos", self.connection)        
        #compras = df[df['tipo'] == 'compra']
        #licitacoes = df[df['tipo'] == 'licitacao']
        #return compras.head(500).append(licitacoes.head(500))        
        return df

    def lda(self):        
        df = pd.read_sql_query('SELECT texto FROM documentos WHERE tipo="compra"', self.connection)                
        
        df['texto'] = df['texto'].apply(lambda t : word_tokenize(t, language='portuguese'))
        print(df['texto'][1])
        
        logging.debug("LDA")        

    def treinar_modelo(self):
        '''
        https://stackabuse.com/text-classification-with-python-and-scikit-learn/
        '''
        logging.debug('Processando documentos')    
        
        df = self.obter_df_documentos()
        x = self.vectorizer.transform(df['texto']).toarray()
        y = df['tipo']  

        logging.debug("Treinando classificador Naive Bayes")
        class2 = self.treinar_testar(GaussianNB(), x, y, 0.1)                        
        self.lista_features_importantes(class2)

        #logging.debug("Treinando classificador Random Forest")
        #class1 = self.treinar_testar(RandomForestClassifier(n_estimators=20, random_state=0), x, y, 0.5)


    def treinar_testar(self, classifier, x, y, split):
        
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=split, random_state=0)  
        classifier.fit(x_train, y_train)
        y_pred = classifier.predict(x_test) 

        logging.debug("Matriz de confusão:")
        print(confusion_matrix(y_test,y_pred))

        logging.debug("Matriz de confusão:")
        print(classification_report(y_test,y_pred))          

        logging.debug('Acurácia: '+str(accuracy_score(y_test, y_pred)))

        return classifier        

    def lista_features_importantes(self, classifier, n=20):

        feature_names = self.vectorizer.get_feature_names()
        topn_class1 = sorted(zip(classifier.theta_[0], feature_names),reverse=True)[:n]
        topn_class2 = sorted(zip(classifier.theta_[1], feature_names),reverse=True)[:n]
        logging.info("Palavras importantes em "+classifier.classes_[0])
        for index, (coef, feat) in enumerate(topn_class1):
            print('%d - %s (theta=%f)' % (index+1, self.undo_stemming(feat), coef))

        logging.info("Palavras importantes em "+classifier.classes_[1])
        for index, (coef, feat) in enumerate(topn_class2):
            print('%d - %s (theta=%f)' % (index+1, self.undo_stemming(feat), coef))
        