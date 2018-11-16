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

import scipy
import numpy as np
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

        if not os.path.exists(constantes.DIR_OUT):
            logging.info("Criando diretório de saídas da análise "+constantes.DIR_OUT)
            os.makedirs(constantes.DIR_OUT)        

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
        df = self.obter_df_texto_faixa_gasto()        
        self.analisar_topicos_categoria(df.loc[df['faixa_gasto'] == 'Faixa 1'], 'Faixa 1')
        self.analisar_topicos_categoria(df.loc[df['faixa_gasto'] == 'Faixa 2'], 'Faixa 2')        

    def analisar_topicos_categoria(self, df, categoria):        

        logging.info("Analisando tópicos da "+categoria+" com LDA")

        logging.info("Criando dicionário")                    
        docs = []            
        for row in df.itertuples():
            tokens = row.texto_processado.split()
            tokens_aux = []            
            for t in tokens:
                if t not in stopwords.words('portuguese'):
                    tokens_aux.append(t)
            docs.append(tokens_aux)
        dictionary = gensim.corpora.Dictionary(docs)            

        logging.info("Criando corpus")            
        corpus = [dictionary.doc2bow(text) for text in docs]

        logging.info("Gerando modelo LDA")
        ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=3, id2word = dictionary, passes=10)        

        p = pyLDAvis.gensim.prepare(ldamodel, corpus, dictionary)
        arquivo_html = constantes.DIR_OUT+'/lda_'+categoria+'.html'
        logging.info("Gravando HTML interativo dao LDA em "+arquivo_html)
        pyLDAvis.save_html(p, arquivo_html)

        arquivo_texto = constantes.DIR_OUT+'/lda_'+categoria+'.txt'
        logging.info("Gravando saída de texto do LDA em "+arquivo_texto)        
        with open(arquivo_texto, 'w') as file:            
            for i in range(ldamodel.num_topics):
                file.write(ldamodel.print_topic(i)+"\n")

    def gerar_tagclouds(self):                
        df = self.obter_df_texto_faixa_gasto()        
        self.gerar_tagcloud_categoria(df.loc[df['faixa_gasto'] == 'Faixa 1'], 'Faixa 1')
        self.gerar_tagcloud_categoria(df.loc[df['faixa_gasto'] == 'Faixa 2'], 'Faixa 2')        
    
    def gerar_tagcloud_categoria(self, df, categoria):                
        
        freqs = self.avaliar_frequencia_de_termos(df, categoria)

        logging.info('Gerando nuvem de tags para a categoria '+categoria)
        plt.style.use('seaborn')
        plt.figure(figsize=(12,6))                

        w = WordCloud(width=1200, height=600, mode='RGBA', background_color='white', max_words=100, margin=1).fit_words(freqs)        
        plt.title('Nuvem de palavras '+categoria)
        plt.imshow(w)        
        plt.axis('off')
        plt.savefig(constantes.DIR_OUT+'/tagcloud_'+categoria+'.png', bbox_inches='tight')
        plt.clf()

    def avaliar_frequencia_de_termos(self, df, categoria):                

        logging.info('Analisando frequência de termos para o tipo '+categoria)
                
        tfidf_matrix = self.vectorizer.fit_transform(df['texto_processado'])                
        
        freqs = { word : tfidf_matrix.getcol(idx).sum() for word, idx in self.vectorizer.vocabulary_.items()}                     

        with open(constantes.DIR_OUT+'/termos_'+categoria+'.md', 'w') as file:
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

    def avaliar_features_naive_bayes(self):  
        '''
            A idéia aqui é treinar um classificador Naive Bayes no modelo Bag of Words para verificar
            depois quais são as features com maior variância, o que dará uma pista de quais são os
            termos mais discriminantes entre compra/licitação
        '''      
        logging.debug('Processando documentos')    
        
        df = self.obter_df_texto_faixa_gasto()
        
        x = self.vectorizer.transform(df['texto_processado']).toarray()
        y = df['faixa_gasto']  

        logging.debug("Avaliando acurácia do classificador Naive Bayes")
        classificador = GaussianNB()
        acuracias = cross_val_score(classificador, x, y, cv=5)
        logging.debug("Acurácias:"+str(acuracias))        

        logging.debug("Ajustando classificador Naive Bayes com toda a base")
        classificador.fit(x, y)

        self.lista_features_importantes(classificador)

    def obter_df_texto_faixa_gasto(self):        
        df = pd.read_sql_query("SELECT id, id_compra_licitacao, texto_processado, valor_atualizado as valor, tipo FROM documentos WHERE valor > 0", self.connection)                
        p = scipy.stats.percentileofscore(df['valor'], df['valor'].mean() + df['valor'].std())
        df['faixa_gasto'] = pd.qcut(df['valor'], q=[0, p/100, 1], labels=['Faixa 1', 'Faixa 2'])                
        return df
        
    def identificar_compras_suspeitas(self):
        
        logging.debug('Processando documentos')    
        
        df = self.obter_df_texto_faixa_gasto()

        x = self.vectorizer.transform(df['texto_processado']).toarray()        
        y = df['faixa_gasto']

        logging.debug("Verificando a acurácia do classificador Random Forest")
        estimadores = 5
        profundidade = 10
        folds = 5
        classificador = RandomForestClassifier(n_estimators=estimadores, max_depth=profundidade, random_state=0)
        acuracias = cross_val_score(classificador, x, y, cv=folds)
        logging.debug("Acurácias:"+str(acuracias))        

        df_faixa1 = df.loc[df['faixa_gasto'] == 'Faixa 1']
        df_faixa2 = df.loc[df['faixa_gasto'] == 'Faixa 2']
        qtd_faixa1 = len(df_faixa1)
        qtd_faixa2 = len(df_faixa2)                
        corte = df['valor'].mean() + df['valor'].std()
        
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

        arquivo_suspeitas = constantes.DIR_OUT+"/suspeitas.txt"
        logging.info("%d suspeitas encontradas. Gravando no arquivo %s " % (len(suspeitas), arquivo_suspeitas))
        
        with codecs.open(arquivo_suspeitas, 'w', 'utf-8') as file:                            

            file.write("Classificador Random Forest com %d estimadores e profundidade máxima %d.\n" % (estimadores, profundidade) )        
            file.write("Classes: \n")
            file.write(" * Faixa 1 (gasto até %.2f) - %d registros.\n" % (corte, qtd_faixa1))
            file.write(" * Faixa 2 (acima de %.2f) - %d registros.\n" % (corte, qtd_faixa2))        
            file.write("Acurácias obtidas na validação cruzada com %d folds: %s\n" % (folds, ', '.join([str(a)+"%" for a in acuracias])))                
            file.write("Foram encontrada %d suspeitas.\n\n" % len(suspeitas))                

            for t in sorted(suspeitas, key=lambda s : s['valor'], reverse=True):                                    
                link = "http://compras.dados.gov.br"
                if t['tipo'] == 'compra':
                    link += "/compraSemLicitacao/doc/compra_slicitacao/" + t['id_compra_licitacao']
                else:
                    link += "/licitacoes/doc/licitacao/" + t['id_compra_licitacao']
                file.write("A %s #%d de valor %0.2f é da %s mas parece ser da %s. (%s)\n" % (t['tipo'], t['id'], t['valor'], t['faixa_banco'], t['faixa_predita'], link))

    def lista_features_importantes(self, clas, n=30):
        feature_names = self.vectorizer.get_feature_names()                
        for i in range(0, len(clas.classes_)):
            topn = sorted(zip(clas.sigma_[i], clas.theta_[i], feature_names),reverse=True)[:n]
    
            arquivo = constantes.DIR_OUT+'/features_naive_bayes_'+clas.classes_[i]+'.md'
            logging.info("Gravando lista de palavras importantes da %s em  %s" % (clas.classes_[i], arquivo))

            with open(arquivo, 'w') as file:
                file.write('| ranking | palavra | sigma | theta |\n')
                file.write('| --- | --- | --- | --- |\n')                                    
                for index, (sigma, tetha, feat) in enumerate(topn):                    
                    file.write('| %d | %s | %f | %f |\n' % (index+1, feat, sigma, tetha))
        
    def analisar_valores(self):

        df = pd.read_sql_query("SELECT tipo, valor_atualizado as valor FROM documentos WHERE valor > 0", self.connection)
        pd.options.display.float_format = '{:.2f}'.format        
        
        vmin = df['valor'].min()        
        vmax = df['valor'].max()                
        vmean = df['valor'].mean()        
        vstd = df['valor'].std()        
        corte = vmean + vstd

        plt.style.use('seaborn')
        plt.figure(figsize=(8,4))                

        df['valor'].plot(kind='hist', bins=100, log=True, rwidth=0.8)                
        plt.xticks(range(int(vmin), int(vmax), int((vmax-vmin)/20.0)), rotation=30)        
        plt.grid(axis='x')                
        plt.ylabel('Quantidade de compras')        
        plt.xlabel('Gasto em reais')        
        plt.title('Histograma dos valores das compras')      
        plt.tight_layout()        
        plt.savefig(constantes.DIR_OUT+'/histograma_valores.png')   

        plt.clf()
                
        percentis = df['valor'].describe(percentiles=[x/100 for x in range(0, 101, 3)])
        with open(constantes.DIR_OUT+'/descritiva.md', 'w') as file:                        
            file.write("| descritiva | valor |\n")
            file.write("| --- | --- |\n")
            for i,p in percentis.items():
                file.write("| %s | %d |\n" % (i,p))        

            p = scipy.stats.percentileofscore(df['valor'], corte)        
            file.write("\nO corte da Faixa 1 e Faixa 2 será no percentil %f.\n" % p)
