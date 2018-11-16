# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import logging
import nltk
from nltk.corpus import floresta
from nltk.corpus import mac_morpho
from nltk.tokenize import word_tokenize
import pickle

class PortugueseTagger:    
    '''
        Esse portuguese tagger foi construído e usado na etapa inicial do trabalho, mas acabou ficando sem uso no projeto final.
    '''

    def __init__(self):
        self.tagger = None            
        self.sent_tokenizer=nltk.data.load('tokenizers/punkt/portuguese.pickle')        
        self.__preparar_tagger()

    def postag(self, txt):                               
        tags = []
        for sent in self.sent_tokenizer.tokenize(txt):
            tokens = word_tokenize(sent, language='portuguese')
            tokens = [t.lower() for t in tokens]
            tags.extend(self.tagger.tag(tokens))
        return tags

    def __simplify_tag(self, t):
        if "+" in t:
            if "-" in t:
                return t[t.index("+")+1:t.index("-")]
            else:
                return t[t.index("+")+1:]
        else:
            return t

    def __preparar_tagger(self):    

        nome_arquivo_tagger = './cache/postagger.pickle'

        if os.path.exists(nome_arquivo_tagger):        
            logging.debug("Carregando o Pos-Tagger já treinado de "+nome_arquivo_tagger)
            with open(nome_arquivo_tagger, 'rb') as arquivo:
                self.tagger = pickle.load(arquivo)

        else:
            logging.debug("Treinando o Pos-Tagger.")
            #tsents = floresta.tagged_sents()            
            tsents = mac_morpho.tagged_sents()
            tsents = [[(w.lower(),self.__simplify_tag(t)) for (w,t) in sent] for sent in tsents if sent]                            
            tagger0 = nltk.DefaultTagger('n')
            tagger1 = nltk.UnigramTagger(tsents, backoff=tagger0)
            tagger2 = nltk.BigramTagger(tsents, backoff=tagger1)
            #tagger3 = nltk.PerceptronTagger(tsents)
            self.tagger = tagger2

            logging.debug("Gravando o Pos-Tagger treinado em "+nome_arquivo_tagger)
            with open(nome_arquivo_tagger, 'wb') as arquivo:
                pickle.dump(self.tagger, arquivo)
