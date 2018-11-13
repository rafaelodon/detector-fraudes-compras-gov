import glob
import os
import logging
import json
import pandas
import sqlite3
from datetime import datetime

class Extrator():    

    def __init__(self, **kwargs):                        
        if 'base_dir' in kwargs:
            self.base_dir = kwargs['base_dir']
        else:
            self.base_dir = './cache'        

        if 'db' in kwargs:
            self.db = kwargs['db']
        else:
            self.db = 'database.db'
        
        if 'override' in kwargs:
            self.override = kwargs['override']
        else:
            self.override = False

        self.compras_analisadas = dict()
        self.licitaceos_analisadas = dict()

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
                tipo VARCHAR(10)              
            );''')

        if self.override:   
            logging.debug('Apagando registros da tabela documentos.')         
            self.cursor.execute('DELETE FROM documentos')
            self.connection.commit()

    def gravar_documento(self, doc):
        if self.override:
            sql = '''INSERT INTO documentos (arquivo, texto, texto_itens, valor, data, id_servico, tipo) 
                VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (doc['arquivo'], doc['texto'], doc['texto_itens'], doc['valor'], doc['data'], doc['id_servico'], doc['tipo']))                    

    def extrair_texto_compras_servico(self, id_servico):
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
                            self.gravar_documento({
                                'arquivo' : file,                            
                                'texto' : compra['ds_objeto_licitacao'] + compra['ds_justificativa'],
                                'texto_itens' : texto_itens,
                                'valor' : float(compra['vr_estimado']),
                                'data' : datetime.strptime(compra['dtDeclaracaoDispensa'], '%Y-%m-%dT%H:%M:%S'),
                                'id_servico' : id_servico,
                                'tipo' : 'compra'
                            })
                        except KeyError:
                            pass
            self.connection.commit()

    def extrair_texto_licitacoes(self, id_servico):
        for file in glob.glob(self.base_dir+'/licitacoes_servico'+id_servico+'*.json'):
            with open(file, 'rb') as arquivo:
                logging.debug('Extraindo texto das licitações do arquivo '+file)
                txt_licitacoes = arquivo.read().decode('utf-8')
                json_licitacoes = json.loads(txt_licitacoes)
                licitacoes = json_licitacoes['_embedded']['licitacoes']
                for licitacao in licitacoes:                    
                    texto_itens = ''
                    id_licitacao = licitacao['_links']['self']['href'].split('/')[4]                        
                    if id_licitacao in self.licitaceos_analisadas:
                        logging.debug('A licitação '+id_licitacao+' já havia sido extraída')
                    else:
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
                            self.gravar_documento({
                                'arquivo' : file,                            
                                'texto' : licitacao['objeto'],
                                'texto_itens' : texto_itens,
                                'valor' : valor,
                                'data' : datetime.strptime(licitacao['data_entrega_proposta'], '%Y-%m-%dT%H:%M:%S'),
                                'id_servico' : id_servico,
                                'tipo' : 'licitacao'
                            })
                        except KeyError:
                            pass
            self.connection.commit()

    def imprimir(self):
        for row in self.cursor.execute('SELECT tipo, count(*) FROM documentos GROUP BY tipo'):
            logging.debug(row)

    def fechar(self):        
        self.connection.commit()
        self.connection.close()



