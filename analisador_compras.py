# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json

class AnalisadorCompras:

    def __init__(self):
        self.itens_licitacoes = dict()
        self.itens_intencoes = dict()
        self.words_count = dict()        
    
    def set_cache(self, cache):
        self.cache = cache

    def set_tagger(self, tagger):
        self.tagger = tagger

    def analisar_irps(self):                
        offset=0
        url = 'http://compras.dados.gov.br/licitacoes/v1/irps.json'
        while True:
            
            txt_irps = self.cache.buscar_json(url, 'irps_offset'+str(offset)+'.json')            
            json_irps = json.loads(txt_irps)
            irps = json_irps['_embedded']['irps']

            for irp in irps:
                self.__analisar_irp(irp)

            # navega para a próxima lsita de IRPS na paginação
            try:
                url = 'http://compras.dados.gov.br' + json_irps['_links']['next']['href']
                offset += 1
            except KeyError:            
                break

    def __analisar_irp(self, irp):
        try:
            numero_irp = irp['numero_irp']
            url_itens = 'http://compras.dados.gov.br' + irp['_links']['itens']['href'] + '.json'
            txt_itens = self.cache.buscar_json(url_itens,
                'itens_irp_'+str(numero_irp)+'.json')            
            
            json_itens = json.loads(txt_itens)
            itens = json_itens['_embedded']['itensIrp']
            for item in itens:
                logging.debug(item['descricao_detalhada'])

        except KeyError:
            pass              

    def analisar_servico(self, id_servico):

        if self.cache is None:
            logging.error('Um serviço de cache deve ser configurado')
            return
        
        if self.tagger is None:
            logging.error('Um serviço de tagger deve ser configurado')
            return

        id_servico = str(id_servico)        
        logging.debug('Consultando licitações do serviço '+id_servico)        
        txt_servico_licitacao = self.cache.buscar_json('http://compras.dados.gov.br/licitacoes/v1/licitacoes.json?item_servico='+id_servico,
            'servico_'+id_servico+'.json')
        
        if txt_servico_licitacao:
            json_servico = json.loads(txt_servico_licitacao)
            logging.debug(json_servico['_links']['self']['title'])

            # análisa o texto das licitações
            licitacoes = json_servico['_embedded']['licitacoes']            
            for licitacao in licitacoes:
                self.__analisar_licitacao(licitacao)


    def __analisar_licitacao(self, licitacao):
        try:
            id_licitacao = licitacao['identificador']
            if id_licitacao not in self.itens_licitacoes:                    
                txt_licitacao = self.cache.buscar_json('http://compras.dados.gov.br/licitacoes/id/licitacao/'+id_licitacao+'/itens.json',
                    'licitacao_'+id_licitacao+'.json')

                if txt_licitacao:                            
                    json_licitacao = json.loads(txt_licitacao)
                    itens = json_licitacao['_embedded']['itensLicitacao']

                    if len(itens) > 0:
                        logging.debug('Analisando licitacao '+id_licitacao)        
                        self.itens_licitacoes[id_licitacao] = itens
                        for item in itens:                            
                            self.__analisar_descricao(item['descricao_item'])                            
        except KeyError:
            pass       

    def __analisar_descricao(self, descricao):
        tags = self.tagger.postag(descricao)
        words = [t for t in tags if t[1] == 'N']
        for tag in words:
            if tag[0] in self.words_count:
                self.words_count[tag[0]] += 1
            else:
                self.words_count[tag[0]] = 1

    def imprimirContagens(self, limite=10):
        i=0
        for k,v in sorted(self.words_count.items(), key=lambda kv: kv[1], reverse=True):
            print('%s - %d' % (k,v))
            i+=1
            if i >= limite:
                break