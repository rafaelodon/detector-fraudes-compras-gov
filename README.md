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

Logs de análise de palavras:

2018-11-04 22:18:14,812 [DEBUG] - Iniciando
2018-11-04 22:18:14,821 [DEBUG] - Calculando TF-IDF das palavras dos documentos
2018-11-04 22:18:43,253 [INFO] - Gerando nuvem de tags para o tipo compra
0 - servidores (freq = 187.528956)
1 - curso (freq = 158.866638)
2 - periodo (freq = 113.905872)
3 - material (freq = 106.681733)
4 - realizar (freq = 82.871684)
5 - abaixo (freq = 75.460494)
6 - participacao (freq = 73.403774)
7 - referente (freq = 70.733127)
8 - atender (freq = 70.522468)
9 - ser (freq = 68.934667)
10 - pelo (freq = 61.156590)
11 - esta (freq = 59.147904)
12 - brasil (freq = 58.430310)
13 - dentro (freq = 58.195190)
14 - lei (freq = 53.670647)
15 - especializacao (freq = 52.807785)
16 - congresso (freq = 50.832523)
17 - manutencao (freq = 49.891061)
18 - capacitacao (freq = 49.790121)
19 - horas (freq = 49.312931)
20 - necessidades (freq = 49.264270)
21 - equipamentos (freq = 47.927092)

2018-11-04 22:19:04,538 [INFO] - Gerando nuvem de tags para o tipo licitacao
0 - curso (freq = 213.699589)
1 - ensino (freq = 203.748483)
2 - profissional (freq = 163.341657)
3 - especializada (freq = 151.155210)
4 - acordo (freq = 137.586912)
5 - arte (freq = 134.392886)
6 - area (freq = 120.472502)
7 - eventual (freq = 104.968674)
8 - aplicacao (freq = 104.257782)
9 - prepom (freq = 104.183508)
10 - aquaviarios (freq = 103.932040)
11 - registro (freq = 102.819702)
12 - maritimo (freq = 100.971080)
13 - ministrar (freq = 99.708774)
14 - rede (freq = 98.804330)
15 - previstos (freq = 97.008775)
16 - programa (freq = 96.312676)
17 - capacitacao (freq = 94.080907)
18 - conforme (freq = 92.088761)
19 - treinamento (freq = 91.334011)
20 - educacao (freq = 87.218698)
21 - projeto (freq = 87.119624)

2018-11-04 22:21:57,453 [DEBUG] - Iniciando
2018-11-04 22:21:57,456 [DEBUG] - Calculando TF-IDF das palavras dos documentos
2018-11-04 22:22:25,730 [DEBUG] - Processando documentos
2018-11-04 22:22:50,303 [DEBUG] - Treinando classificador Naive Bayes
2018-11-04 22:22:50,508 [DEBUG] - Matriz de confusão:
[[284   7]
 [ 12 314]]
2018-11-04 22:22:50,514 [DEBUG] - Matriz de confusão:
             precision    recall  f1-score   support

     compra       0.96      0.98      0.97       291
  licitacao       0.98      0.96      0.97       326

avg / total       0.97      0.97      0.97       617

2018-11-04 22:22:50,523 [DEBUG] - Acurácia: 0.9692058346839546

2018-11-04 22:22:50,533 [INFO] - Palavras importantes em compra
1 - servidores (theta=0.064287)
2 - curso (theta=0.054192)
3 - periodo (theta=0.039112)
4 - material (theta=0.036358)
5 - realizar (theta=0.028200)
6 - abaixo (theta=0.026252)
7 - participacao (theta=0.025888)
8 - atender (theta=0.024697)
9 - referente (theta=0.024249)
10 - ser (theta=0.023987)
11 - pelo (theta=0.021057)
12 - esta (theta=0.020441)
13 - brasil (theta=0.020210)
14 - dentro (theta=0.020081)
15 - lei (theta=0.018019)
16 - congresso (theta=0.017622)
17 - especializacao (theta=0.017465)
18 - capacitacao (theta=0.017124)
19 - horas (theta=0.016981)
20 - necessidades (theta=0.016967)

2018-11-04 22:22:50,534 [INFO] - Palavras importantes em licitacao
1 - curso (theta=0.065337)
2 - ensino (theta=0.062463)
3 - profissional (theta=0.050218)
4 - especializada (theta=0.046399)
5 - acordo (theta=0.042273)
6 - arte (theta=0.041352)
7 - area (theta=0.037116)
8 - eventual (theta=0.032493)
9 - aplicacao (theta=0.031917)
10 - prepom (theta=0.031855)
11 - aquaviarios (theta=0.031786)
12 - registro (theta=0.031437)
13 - maritimo (theta=0.030899)
14 - rede (theta=0.030612)
15 - previstos (theta=0.029693)
16 - programa (theta=0.029594)
17 - ministrar (theta=0.029562)
18 - capacitacao (theta=0.029517)
19 - conforme (theta=0.028208)
20 - treinamento (theta=0.027277)
