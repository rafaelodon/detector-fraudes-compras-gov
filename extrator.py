import glob
import logging
import json
import pandas

class Extrator():

    def extrair_texto_compras(self, path):

        array_compras = []

        for file in glob.glob(path):
            with open(file, 'rb') as arquivo:
                logging.debug('Extraindo texto das compras do arquivo '+file)
                txt_compras = arquivo.read().decode('utf-8')
                json_compras = json.loads(txt_compras)
                compras = json_compras['_embedded']['compras']
                for compra in compras:                    
                    try:
                        texto = compra['ds_justificativa']
                        valor = compra['vr_estimado']
                        array_compras.append([file, texto, valor, 'compra'])
                    except KeyError:
                        pass

        df_compras = pandas.DataFrame(array_compras, columns=['arquivo', 'texto', 'valor', 'tipo'])
        print(df_compras.size)

                    



