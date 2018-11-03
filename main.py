# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json

from portuguese_tagger import PortugueseTagger
from coletor import Coletor
from extrator import Extrator
from analisador import Analisador

def main():

    logging.basicConfig(
        level=logging.DEBUG,        
        format="%(asctime)s [%(levelname)s] - %(message)s"
    )

    logging.debug("Iniciando")
    
    #coletor = Coletor()        
    #coletor.coletar_compras_e_licitacoes_do_servico('17663')        

    #extrator = Extrator()
    #extrator.extrair_texto_compras_servico('17663')
    #extrator.extrair_texto_licitacoes('17663')
    #extrator.imprimir()

    #tagger = PortugueseTagger()    

    analisador = Analisador()        
    analisador.gerar_tagclouds()    
    #analisador.treinar_modelo()
    #analisador.lda()


if __name__ == "__main__":    
    main()