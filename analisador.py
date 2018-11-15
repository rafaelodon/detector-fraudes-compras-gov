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
import constantes

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
import pyLDAvis.gensim

import matplotlib.pyplot as plt

from wordcloud import WordCloud

import pickle


class Analisador:

    REMOVER = ['pregao eletronico', 'pregao', 'aquisicao', 'valor', 'limite', 
        'licitacao', 'licitacao', 'justificativa', 'edital', 'contratacao', 'fornecimento', 
        'prestacao', 'precos', 'preco', 'formacao', 'empresa', 'servico', 'servicos',
        'inscricao', 'pagamento', 'taxa', 'para', 'objeto']  

    def __init__(self, db=None):        
        if db is None:
            self.db = constantes.ARQ_BANCO
        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()
        self.vectorizer = self.carregar_vectorizer()               

    def carregar_vectorizer(self):
        arquivo_vectorizer = constantes.ARQ_VECTORIZER
        if os.path.exists(arquivo_vectorizer):
            logging.debug('Carregando o TF-IDF Vectorizer existente de '+arquivo_vectorizer)
            with open(arquivo_vectorizer, 'rb') as file:
                return pickle.load(file)
        else:
            logging.error("O vectorizer ainda não existe. Execute o processador.")
            exit(1)

    def analisar_topicos(self):
        '''
        ldamodel = None
        arquivo_ldamodel = './cache/ldamodel.pickle'        
        if os.path.exists(arquivo_ldamodel):
            logging.info("Carregando modelo LDA já existente de "+arquivo_ldamodel)
            with open(arquivo_ldamodel, 'rb') as file:
                ldamodel = pickle.load(file)            
        else:
            logging.info("Gravando modelo LDA em "+arquivo_ldamodel)
            with open(arquivo_ldamodel, 'wb') as file:
                pickle.dump(ldamodel, file)  
        '''
        logging.info("Vetorizando documentos")
        df = pd.read_sql_query("SELECT texto_processado FROM documentos", self.connection)                            
        
        logging.info("Criando dicionário")            
        
        docs = [row.texto_processado.split() for row in df.itertuples()]            
        dictionary = gensim.corpora.Dictionary(docs)            

        logging.info("Criando corpus ")            
        corpus = [dictionary.doc2bow(text) for text in docs]

        logging.info("Gerando modelo LDA")
        ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=2, id2word = dictionary, passes=10)        

        p = pyLDAvis.gensim.prepare(ldamodel, corpus, dictionary)
        pyLDAvis.save_html(p, './out/lda.html')

        logging.info("Tópicos encontrados pelo LDA:")
        ldamodel.print_topics(num_topics=2, num_words=5)            
        with open('./out/lda.txt', 'w') as file:            
            for i in range(ldamodel.num_topics):
                file.write(ldamodel.print_topic(i)+"\n")

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

        logging.info('Analisando frequência de termos para o tipo '+tipo)
        
        df = pd.read_sql_query("SELECT texto_processado, tipo FROM documentos", self.connection)        
        df = df[df['tipo'] == tipo]        
        
        tfidf_matrix = self.vectorizer.fit_transform(df['texto_processado'])                
        
        freqs = { word : tfidf_matrix.getcol(idx).sum() for word, idx in self.vectorizer.vocabulary_.items()}                     

        with open('./out/termos_'+tipo+'.md', 'w') as file:
            file.write('| palavra | tf-idf |\n')
            file.write('| --- | --- |\n')
            for k,v in sorted(freqs.items(), key=lambda kv : kv[1], reverse=True):
                file.write('| %s | %f |\n' % (k,v))
        
        return freqs

    def tratar_frequencia(self, value):
        if math.isnan(value):
            return 0.0
        else:
            return value        

    def treinar_modelo_tipo(self):  
        '''
            A idéia aqui é treinar um classificador Naive Bayes no modelo Bag of Words para verificar
            depois quais são as features com maior variância, o que dará uma pista de quais são os
            termos mais discriminantes entre compra/licitação
        '''      
        logging.debug('Processando documentos')    
        
        df = pd.read_sql_query("SELECT texto_processado, tipo FROM documentos", self.connection)        
        
        x = self.vectorizer.transform(df['texto_processado']).toarray()
        y = df['tipo']  

        logging.debug("Treinando classificador Naive Bayes")
        classificador = self.treinar_testar(GaussianNB(), x, y, 0.25)                        
        self.lista_features_importantes(classificador)
        
    def treinar_modelo_faixa_gasto(self):
        '''
            A idéia aqui é treinar um classificador que tenha alta revogação na faixa de preços menores,
            e julgar os registros da faixa maior classificados como faixa menor como candidatos
            a "compras suspeitas" (valor alto mas texto parecido com outras compras de valor menor)
        '''
        
        logging.debug('Processando documentos')    
        
        df = pd.read_sql_query("SELECT id, id_compra_licitacao, texto_processado, valor, tipo FROM documentos WHERE valor > 0", self.connection)                    
        df['faixa_gasto'] = pd.qcut(df['valor'], q=[0, .90, .95, 1.], labels=['Faixa 1', 'Faixa 2', 'Faixa 3'])

        x = self.vectorizer.transform(df['texto_processado']).toarray()
        y = df['faixa_gasto']  

        logging.debug("Verificando a acurácia do classificador Random Forest")
        classificador = RandomForestClassifier(n_estimators=50, max_depth=50, random_state=0)
        acuracias = cross_val_score(classificador, x, y, cv=5)
        logging.debug("Acurácias:"+str(acuracias))        

        logging.debug("Ajustando classificador Random Forest com toda a base")
        classificador.fit(x, y)

        logging.debug("Classificando documentos para encontrar suspeitas")
        suspeitas = []        
        for t in df.itertuples():
            y = classificador.predict([x[t.Index]])            
            if t.faixa_gasto > y[0]:                                                 
                suspeitas.append({
                    "tipo" : t.tipo,
                    "id" : t.id,
                    "valor" : t.valor,
                    "faixa_banco" : t.faixa_gasto,
                    "faixa_predita" : y[0],
                    'id_compra_licitacao' : t.id_compra_licitacao
                })

        logging.info("%d suspeitas encontradas. Gravando no arquivo %s " % (len(suspeitas), constantes.ARQ_SUSPEITAS))

        with codecs.open(constantes.ARQ_SUSPEITAS, 'w', 'utf-8') as file:                            
            for t in sorted(suspeitas, key=lambda s : s['valor'], reverse=True):                                    
                link = "http://compras.dados.gov.br"
                if t['tipo'] == 'compra':
                    link += "/compraSemLicitacao/doc/compra_slicitacao/" + t['id_compra_licitacao']
                else:
                    link += "/licitacoes/doc/licitacao/" + t['id_compra_licitacao']
                file.write("A %s #%d de valor %0.2f é da %s mas parece ser da %s. (%s)\n" % (t['tipo'], t['id'], t['valor'], t['faixa_banco'], t['faixa_predita'], link))
    
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

    def lista_features_importantes(self, clas, n=20):
        feature_names = self.vectorizer.get_feature_names()                
        for i in range(0, len(clas.classes_)):
            topn = sorted(zip(clas.sigma_[i], clas.theta_[i], feature_names),reverse=True)[:n]
            logging.info("Palavras importantes em "+clas.classes_[i])

            with open('./out/features_nb_'+clas.classes_[i]+'.md', 'w') as file:
                file.write('| ranking | palavra | sigma | theta |\n')
                file.write('| --- | --- | --- | --- |\n')                                    
                for index, (sigma, tetha, feat) in enumerate(topn):                    
                    file.write('| %d | %s | %f | %f |\n' % (index+1, feat, sigma, tetha))
        
    def analisar_valores(self):

        df = pd.read_sql_query("SELECT valor FROM documentos WHERE valor > 0", self.connection)                
        print(pd.qcut(df['valor'], q=[0, .95, 1], retbins=True))
        #plt.hist(df['valor'], bins=10)
        #plt.show()