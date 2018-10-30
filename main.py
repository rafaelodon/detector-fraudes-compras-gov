# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
from urllib.request import urlopen
import json
import os
import nltk
from nltk.corpus import floresta
from nltk.tokenize import word_tokenize
import pickle

def buscar_json_com_cache(url, nome_arquivo_cache):
    data = ''
    cache_dir = './cache'
    if not os.path.exists(cache_dir):
        logging.debug('Criano o diretório de cache')
        os.makedirs(cache_dir)

    caminho_arquivo_cache = cache_dir+'/'+nome_arquivo_cache
    if os.path.exists(caminho_arquivo_cache):        
        with open(caminho_arquivo_cache, 'r') as arquivo:
            logging.debug('Recuperando resposta em cache '+nome_arquivo_cache)
            data = arquivo.read()
    else:        
        response = urlopen(url)
        data = response.read().decode('utf-8')
        with open(caminho_arquivo_cache, 'w') as arquivo:
            logging.debug('Gravando resposta em cache '+nome_arquivo_cache)            
            arquivo.write(data)     

    return data

class PortugueseTagger:

    def __init__(self):
        self.tagger = None    
        self.__preparar_tagger()

    def postag(self, txt):                       
        tokens = word_tokenize(txt, language='portuguese')            
        tags = self.tagger.tag(tokens)
        return tags

    def __simplify_tag(self, t):
        if "+" in t:
            return t[t.index("+")+1:]
        else:
            return t

    def __preparar_tagger(self):    

        nome_arquivo_tagger = 'postagger.pickle'

        if os.path.exists(nome_arquivo_tagger):        
            logging.debug("Carregando o Pos-Tagger já treinado de "+nome_arquivo_tagger)
            with open(nome_arquivo_tagger, 'rb') as arquivo:
                self.tagger = pickle.load(arquivo)

        else:
            logging.debug("Treinando o Pos-Tagger.")
            tsents = floresta.tagged_sents()
            tsents = [[(w.lower(),self.__simplify_tag(t)) for (w,t) in sent] for sent in tsents if sent]    
            tagger0 = nltk.DefaultTagger('n')
            tagger1 = nltk.UnigramTagger(tsents, backoff=tagger0)
            tagger2 = nltk.BigramTagger(tsents, backoff=tagger1)
            tagger3 = nltk.PerceptronTagger(tsents)
            self.tagger = tagger3

            logging.debug("Gravando o Pos-Tagger treinado em "+nome_arquivo_tagger)
            with open(nome_arquivo_tagger, 'wb') as arquivo:
                pickle.dump(self.tagger, arquivo)

class AnalisadorComprasNet:

    def __init__(self):
        self.itens_licitacoes = dict()
        self.adjs_count = dict()
        self.tagger = PortugueseTagger()

    def analisarServico(self, id_servico):
        id_servico = str(id_servico)        
        logging.debug('Consultando licitações do serviço '+id_servico)        
        txt_servico = buscar_json_com_cache('http://compras.dados.gov.br/licitacoes/v1/licitacoes.json?item_servico='+id_servico,
            'servico_'+id_servico+'.json')
        
        json_servico = json.loads(txt_servico)
        logging.debug(json_servico['_links']['self']['title'])

        licitacoes = json_servico['_embedded']['licitacoes']

        for licitacao in licitacoes:
            try:
                id_licitacao = licitacao['identificador']

                if id_licitacao not in self.itens_licitacoes:                    
                    txt_licitacao = buscar_json_com_cache('http://compras.dados.gov.br/licitacoes/id/licitacao/'+id_licitacao+'/itens.json',
                        'licitacao_'+id_licitacao+'.json')
                    json_licitacao = json.loads(txt_licitacao)
                    itens = json_licitacao['_embedded']['itensLicitacao']

                    if len(itens) > 0:
                        logging.debug('Analisando licitacao '+id_licitacao)        
                        self.itens_licitacoes[id_licitacao] = itens
                        for item in itens:
                            descricao = item['descricao_item']                
                            tags = self.tagger.postag(descricao)
                            adjs = [t for t in tags if t[1] == 'adj']

                            for tag in adjs:
                                if tag[0] in self.adjs_count:
                                    self.adjs_count[tag[0]] += 1 
                                else:
                                    self.adjs_count[tag[0]] = 1                        
                            
                            print(adjs)
                            
            except KeyError:
                pass

        self.adjs_count = sorted(self.adjs_count.items(), key=lambda kv: kv[1], reverse=True)            

    def imprimirContagens(self):
        for k,v in self.adjs_count:
            print('%s - %c' % (k,v))

def main():    

    logging.basicConfig(
        level=logging.DEBUG,        
        format="%(asctime)s [%(levelname)s] - %(message)s"
    )

    logging.debug("Iniciando")

    analisador = AnalisadorComprasNet()
    analisador.analisarServico(15245)           
    analisador.imprimirContagens()


if __name__ == "__main__":    
    main()