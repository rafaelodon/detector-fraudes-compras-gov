# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import os
import codecs
from urllib.request import urlopen
import json

class Coletor:
   
    def __init__(self):
        self.modo_offline = False
        self.qtd_compras = 0
        self.qtd_licitacoes = 0
        self.cache_dir = './cache'

    def set_modo_offline(self):
        self.modo_offline = True

    def set_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir

    def coletar_compras_e_licitacoes_do_servico(self, id_servico):
        self.__coletar_compras_do_servico(id_servico)
        self.__coletar_licitacoes_do_servico(id_servico)

        logging.info(str(self.qtd_compras) + " compras coletadas.")
        logging.info(str(self.qtd_licitacoes) + " licitações coletadas.")

    def __coletar_compras_do_servico(self, id_servico):                
        offset=0
        url = 'http://compras.dados.gov.br/compraSemLicitacao/v1/itens_compras_slicitacao.json?co_servico='+id_servico        
        while True:            
            txt_compras = self.__buscar_com_cache(url, 'compras_servico'+id_servico+'_'+str(offset)+'.json')
            if txt_compras:
                json_compras = json.loads(txt_compras)                
                self.qtd_compras += len(json_compras['_embedded']['compras'])                                
                try:
                    url = 'http://compras.dados.gov.br' + json_compras['_links']['next']['href']
                    offset += 1
                except KeyError:            
                    break
    
    def __coletar_licitacoes_do_servico(self, id_servico):                
        offset=0
        url = 'http://compras.dados.gov.br/licitacoes/v1/licitacoes.json?item_servico='+id_servico
        while True:                             
            txt_licitacoes = self.__buscar_com_cache(url, 'licitacoes_servico'+id_servico+'_'+str(offset)+'.json')
            if txt_licitacoes:
                json_licitacoes = json.loads(txt_licitacoes)
                self.qtd_licitacoes += len(json_licitacoes['_embedded']['licitacoes'])                                
            try:
                url = 'http://compras.dados.gov.br' + json_licitacoes['_links']['next']['href']
                offset += 1
            except KeyError:            
                break
    
    def __buscar_com_cache(self, url, nome_arquivo_cache):
        data = ''        
        if not os.path.exists(self.cache_dir):
            logging.debug('Criando o diretório de cache')
            os.makedirs(self.cache_dir)

        caminho_arquivo_cache = self.cache_dir+'/'+nome_arquivo_cache
        if os.path.exists(caminho_arquivo_cache):        
            with open(caminho_arquivo_cache, 'rb') as arquivo:
                logging.debug('Recuperando resposta em cache '+nome_arquivo_cache)
                data = arquivo.read().decode('utf-8')
        else:        
            if not self.modo_offline:
                response = urlopen(url)
                data = response.read().decode('utf-8')
                with codecs.open(caminho_arquivo_cache, 'w', 'utf-8') as arquivo:
                    logging.debug('Gravando resposta em cache '+nome_arquivo_cache)            
                    arquivo.write(data)     

        return data