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
    #coletor.coletar_historico_selic()

    #extrator = Extrator()
    #extrator.extrair_texto_compras_licitacoes()        
    #extrator.extrair_historico_selic()

    #processador = Processador()
    #processador.processar_texto()    
    #processador.atualizar_valores_com_selic()    

    #analisador = Analisador()      
    #analisador.analisar_valores()
    #analisador.gerar_tagclouds()    
    #analisador.avaliar_features_naive_bayes()    
    #analisador.analisar_topicos()    
    #analisador.identificar_compras_suspeitas()    
    
if __name__ == "__main__":    
    main()