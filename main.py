# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json

from json_api_cache import *
from portuguese_tagger import *
from analisador_compras import *

def main():    

    logging.basicConfig(
        level=logging.DEBUG,        
        format="%(asctime)s [%(levelname)s] - %(message)s"
    )

    logging.debug("Iniciando")
    
    jsonCache = JsonApiCache()
    #jsonCache.set_modo_offline()

    tagger = PortugueseTagger()    

    analisador = AnalisadorCompras()    
    analisador.set_cache(jsonCache)
    analisador.set_tagger(tagger)

    #txt_servicos = jsonCache.buscar_json("http://compras.dados.gov.br/servicos/v1/servicos.json", "servicos.json")        
    #json_servicos = json.loads(txt_servicos)
    #servicos = json_servicos['_embedded']['servicos']    
         
    #for servico in servicos:        
    #    analisador.analisarServico(servico['codigo'])    

    #analisador.analisar_servico('264')

    analisador.analisar_irps()
    
    analisador.imprimirContagens()


if __name__ == "__main__":    
    main()