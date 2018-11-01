# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
from urllib.request import urlopen
import json
import os
import codecs

class JsonApiCache():

    def __init__(self):
        self.modo_offline = False

    def set_modo_offline(self):
        self.modo_offline = True

    def buscar_json(self, url, nome_arquivo_cache):
        data = ''
        cache_dir = './cache'
        if not os.path.exists(cache_dir):
            logging.debug('Criando o diretório de cache')
            os.makedirs(cache_dir)

        caminho_arquivo_cache = cache_dir+'/'+nome_arquivo_cache
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