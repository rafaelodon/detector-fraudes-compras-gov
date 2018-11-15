# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json
import string 
import constantes

from portuguese_tagger import PortugueseTagger
from coletor import Coletor
from extrator import Extrator
from analisador import Analisador
from processador import Processador

def main():

    logging.basicConfig(
        level=logging.DEBUG,        
        format="%(asctime)s [%(levelname)s] - %(message)s"
    )

    logging.debug("Iniciando")

    #coletor = Coletor()                
    #coletor.coletar_compras_e_licitacoes()

    #extrator = Extrator(override=True)
    #extrator.extrair_texto_compras_licitacoes()        

    #processador = Processador()
    #processador.processar_texto()    

    analisador = Analisador()      
    analisador.analisar_valores()
    #analisador.gerar_tagclouds()    
    #analisador.treinar_modelo_tipo()    
    #analisador.analisar_topicos()    
    #analisador.treinar_modelo_faixa_gasto()    
    
if __name__ == "__main__":    
    main()