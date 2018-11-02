# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import json

class AnalisadorCompras:

    def __init__(self):
        self.words_count = dict()

    def set_cache(self, cache):        
        self.cache = cache

    def set_tagger(self, tagger):
        self.tagger = tagger
        
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