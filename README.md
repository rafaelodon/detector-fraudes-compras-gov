## Mineração de texto sobre os itens das licitações de compras do governo.

**Autor**: Rafael Odon de Alencar
**Email**: odon.rafael@gmail.com

Fonte: API de dados abertos do ComprasNet (http://compras.dados.gov.br)

### Dependências

* Python 3
* Pacotes do NLTK: floresta, mac_morpho, averaged_perceptron_tagger, rslp, stopwords 

Serviço 17663 - Curso Aperfeiçoamento / Especialização Profissional
http://compras.dados.gov.br/servicos/doc/servico/17663

### Fontes técnicas
https://hampao.wordpress.com/2016/04/08/building-a-wordcloud-using-a-td-idf-vectorizer-on-twitter-data/

Tópicos encontrados pelo LDA - 5 tópicos, 20 passadas, 4 palavras:
topic #0 (0.200): 0.041*"aplicacao" + 0.040*"prepom" + 0.040*"aquaviarios" + 0.039*"previstos"
topic #1 (0.200): 0.016*"curso" + 0.015*"gestao" + 0.015*"treinamento" + 0.013*"cur"
topic #2 (0.200): 0.015*"curso" + 0.014*"servidores" + 0.007*"periodo" + 0.007*"material"
topic #3 (0.200): 0.022*"conforme" + 0.019*"quantidades" + 0.018*"exigencias" + 0.018*"militares"
topic #4 (0.200): 0.039*"arte" + 0.038*"acordo" + 0.034*"ensino" + 0.021*"cacoal"
