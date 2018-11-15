import glob
import os
import logging
import json
import pandas
import sqlite3
import constantes
import parsel
import pickle
from datetime import datetime

class Extrator():    

    def __init__(self, **kwargs):                        
        if 'base_dir' in kwargs:
            self.base_dir = kwargs['base_dir']
        else:
            self.base_dir = constantes.DIR_CACHE

        if 'db' in kwargs:
            self.db = kwargs['db']
        else:
            self.db = constantes.ARQ_BANCO
        
        if 'override' in kwargs:
            self.override = kwargs['override']
        else:
            self.override = False

        if not os.path.exists(constantes.DIR_DATA):
            os.mkdir(constantes.DIR_DATA)

        if self.override:   
            logging.debug('Apagando banco de dados anterior.')                     
            if os.path.exists(constantes.ARQ_BANCO):
                os.remove(constantes.ARQ_BANCO)            

        self.connection = sqlite3.connect(self.db)        
        self.cursor = self.connection.cursor()        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos (                
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo VARCHAR(255),
                texto TEXT CLOB,
                texto_itens TEXT CLOB,
                valor DOUBLE,
                data DATE,
                id_servico VARCHAR(10),
                id_compra_licitacao VARCHAR(100),
                tipo VARCHAR(10)                              
            );''')            
                
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS selic (                
                id INTEGER PRIMARY KEY AUTOINCREMENT,                
                data_inicio DATE,
                data_fim DATE,
                valor DOUBLE                                
            );''')            
        
        self.compras_analisadas = dict()
        self.licitacoes_analisadas = dict()

    def __gravar_documento(self, doc):        
        sql = '''INSERT INTO documentos (arquivo, texto, texto_itens, valor, data, id_servico, id_compra_licitacao, tipo) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
        self.cursor.execute(sql, (doc['arquivo'], doc['texto'], doc['texto_itens'], doc['valor'], doc['data'], doc['id_servico'], doc['id_compra_licitacao'], doc['tipo']))                    

    def __extrair_texto_compras_servico(self, id_servico):
        for file in glob.glob(self.base_dir+'/compras_servico'+id_servico+'*.json'):
            with open(file, 'rb') as arquivo:
                logging.debug('Extraindo texto das compras do arquivo '+file)
                txt_compras = arquivo.read().decode('utf-8')
                json_compras = json.loads(txt_compras)
                compras = json_compras['_embedded']['compras']
                for compra in compras:                                        
                    texto_itens = ''
                    id_compra = compra['_links']['self']['href'].split('/')[4]
                    if id_compra in self.compras_analisadas:
                        logging.debug('A compra '+id_compra+' já havia sido extraída')
                    else:                            
                        self.compras_analisadas[id_compra] = True
                        try:                        
                            file_itens = self.base_dir+'/itens_compra_'+id_compra+'.json' 
                            if os.path.exists(file_itens):   
                                with open(file_itens, 'rb') as arquivo_itens:
                                    logging.debug('Exraindo texto dos itens de compra '+file_itens)
                                    txt_itens = arquivo_itens.read().decode('utf-8')
                                    json_itens = json.loads(txt_itens)
                                    itens = json_itens['_embedded']['compras']
                                    for item in itens:
                                        texto_itens += item['ds_detalhada'] + '. '                            
                        except KeyError:
                            pass

                        try:              
                            self.__gravar_documento({
                                'arquivo' : file,                            
                                'texto' : compra['ds_objeto_licitacao'] + compra['ds_justificativa'],
                                'texto_itens' : texto_itens,
                                'valor' : float(compra['vr_estimado']),
                                'data' : datetime.strptime(compra['dtDeclaracaoDispensa'], '%Y-%m-%dT%H:%M:%S'),
                                'id_servico' : id_servico,
                                'id_compra_licitacao' : id_compra,
                                'tipo' : 'compra'
                            })
                        except KeyError:
                            pass
            self.connection.commit()

    def __extrair_texto_licitacoes_servico(self, id_servico):
        for file in glob.glob(self.base_dir+'/licitacoes_servico'+id_servico+'*.json'):
            with open(file, 'rb') as arquivo:
                logging.debug('Extraindo texto das licitações do arquivo '+file)
                txt_licitacoes = arquivo.read().decode('utf-8')
                json_licitacoes = json.loads(txt_licitacoes)
                licitacoes = json_licitacoes['_embedded']['licitacoes']
                for licitacao in licitacoes:                    
                    texto_itens = ''
                    id_licitacao = licitacao['_links']['self']['href'].split('/')[4]                        
                    if id_licitacao in self.licitacoes_analisadas:
                        logging.debug('A licitação '+id_licitacao+' já havia sido extraída')
                    else:
                        self.licitacoes_analisadas[id_licitacao] = True
                        valor = 0.0
                        try:                            
                            file_itens = self.base_dir+'/itens_licitacao_'+id_licitacao+'.json' 
                            if os.path.exists(file_itens):        
                                with open(file_itens, 'rb') as arquivo_itens:
                                    logging.debug('Exraindo texto dos itens de licitação '+file_itens)
                                    txt_itens = arquivo_itens.read().decode('utf-8')
                                    json_itens = json.loads(txt_itens)
                                    itens = json_itens['_embedded']['itensLicitacao']                                    
                                    for item in itens:
                                        texto_itens += item['descricao_item'] + '. '
                                        valor += item['valor_estimado']
                        except KeyError:
                            pass

                        try:                        
                            self.__gravar_documento({
                                'arquivo' : file,                            
                                'texto' : licitacao['objeto'],
                                'texto_itens' : texto_itens,
                                'valor' : valor,
                                'data' : datetime.strptime(licitacao['data_entrega_proposta'], '%Y-%m-%dT%H:%M:%S'),
                                'id_servico' : id_servico,
                                'id_compra_licitacao' : id_licitacao,
                                'tipo' : 'licitacao'
                            })
                        except KeyError:
                            pass
            self.connection.commit()

    def extrair_texto_compras_licitacoes(self):
        self.__extrair_texto_compras_servico(constantes.ID_SERVICO)
        self.__extrair_texto_licitacoes_servico(constantes.ID_SERVICO)

        logging.info("Quantidades de registros gerados pela extração: ")
        for row in self.cursor.execute('SELECT tipo, count(*) FROM documentos GROUP BY tipo'):
            logging.debug(row)

    def extrair_historico_selic(self):
        
        with open(constantes.DIR_CACHE+'/selic.html', 'rb') as file:
            html = file.read().decode('utf-8')

            logging.info("Apagando registros anteriores da SELIC")
            self.cursor.execute('DELETE FROM selic')
            self.connection.commit()

            sel = parsel.Selector(html)
            datas = sel.xpath('//html/body/div[2]/div[3]/table//tr/td[position()=4]/text()').getall()
            taxas = sel.xpath('//html/body/div[2]/div[3]/table//tr/td[position()=7]/text()').getall()
            selic = []
            i = 0                                
            while i < len(datas) and i < len(taxas):
                data = datas[i].strip()
                taxa = taxas[i].strip()                
                i += 1
                if data == '' or taxa == '':                    
                    continue
                else:                    
                    logging.debug('Taxa selic encontrada: %s - %s' % (data, taxa) )
                    data_inicio = datetime.strptime(data.split(' - ')[0], '%d/%m/%Y')
                    data_fim = datetime.strptime(data.split(' - ')[1], '%d/%m/%Y')                    
                    taxa = float(taxa.replace(',','.'))                    
                    self.cursor.execute('INSERT INTO selic (data_inicio, data_fim, valor) VALUES (?, ?, ?)', (data_inicio, data_fim, taxa))            
            
            logging.info("Gravando registros novos da SELIC")
            self.connection.commit()
