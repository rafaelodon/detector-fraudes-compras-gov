# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json

from portuguese_tagger import *
from coletor import *
from extrator import *
#from analisador import *


def main():    

    logging.basicConfig(
        level=logging.DEBUG,        
        format="%(asctime)s [%(levelname)s] - %(message)s"
    )

    logging.debug("Iniciando")
    
    coletor = Coletor()    
    coletor.coletar_compras_e_licitacoes_do_servico('17663')

    extrator = Extrator()
    extrator.extrair_texto_compras('./cache/compras*.json')

    #tagger = PortugueseTagger()    

    #analisador = AnalisadorCompras()    
    #analisador.set_cache(jsonCache)
    #analisador.set_tagger(tagger)

    #txt_servicos = jsonCache.buscar_json("http://compras.dados.gov.br/servicos/v1/servicos.json", "servicos.json")        
    #json_servicos = json.loads(txt_servicos)
    #servicos = json_servicos['_embedded']['servicos']    
         
    #for servico in servicos:        
    #    analisador.analisarServico(servico['codigo'])    

    #analisador.analisar_servico('17663')

    #analisador.analisar_irps()
    
    #analisador.imprimirContagens()


if __name__ == "__main__":    
    main()