# Recuperação e Mineração de Texto sobre as Compras Governamentais

**Autor**: Rafael Odon de Alencar

**Email**: odon.rafael@gmail.com

**Data**: 15/11/2018

## Introdução

O presente trabalho busca exercitar técnicas de recuperação de informação e de mineração de texto através do desenvolvimento de um sistema que coleta, extrai, processa e analisa sob determinadas óticas o conteúdo textual descritivo de uma amostra das compras do Governo Federal.
Os dados observados encontram-se disponíveis publicamente no site http://compras.dados.gov.br.

As compras feitas pelo governo podem ser do tipo **com licitação** ou **sem licitação**, e são categorizadas com ajuda de um catálogo de **serviços** e **materiais** que agrupa compras de segmentos semelhantes. No enatnto, o volume de informações e a complexidade da base torna difícil contemplar as características gerais do comportamento de compra por parte das entidades públicas.

Afim de demonstrar o potencial de uma ferramenta automatizada para auxiliar na recuperação e análise em torno do texto dessas compras, foram selecionados apenas 2 serviços específicos do catálogo:

 - Serviço 17663: Curso Aperfeiçoamento / Especialização Profissional
 - Serviço 3239: Transporte Rodoviário - Pessoal por Automóveis

Em resumo, foram coletadas todas compras com e sem licitação desses dois serviços, e o conteúdo textual descritivo desses documentos foi extraído, processado e utilizado para gerar *insights*. As compras foram classificadas quanto à faixa de gasto a partir de uma análise da estatística descritiva. Em seguida, foram geradas nuvens de palavras destacando os termos descritivos de maior frequência para o **grupo de gastos menores** e para o **grupo de gastos maiores**. Um modelo de classificação *Naive Bayes* foi utilizado para verificar os termos que mais contribuiram para discriminar cada uma dessas classes. Também foi aplicada a técnica LDA (*Latent Dirichlet Allocation*) de detecção de tópicos em cada um desses grupos para verificar a co-ocorrência de termos nos conjunto de documentos. Por fim, uma estratégia de detecção de compras suspeitas foi proposta.

O sistema foi construído em Python 3.5 com ajudas de bibliotecas tais como *Pandas*, *Nltk*, *Scikit-Learn*, *Gensim*, *Matplotlib*, *Wordcloud* dentre outras. O código foi separado em classes conforme as responsabilidades do fluxo de trabalho: **Coletor**, **Extrator**, **Processador** e **Analisador**.

Cada uma das etapas será melhor descrita nas seções seguintes, bem como as observações e conclusões obtidas após as análises feitas.

## Coleta dos documentos

O site http://compras.dados.gov.br não só permite navegar pelos dados através de sua interface em HTML, mas também oferece APIs que retornam documentos Json.
Há uma [API própria para as licitações](http://compras.dados.gov.br/docs/lista-metodos-licitacoes.html), e outra [API própria para as compras sem licitação](http://compras.dados.gov.br/docs/lista-metodos-compraSemLicitacao.html). 
Ambas possuem características diferentes mas permitem igualmente consultar uma numerosa lista paginada com todas as compras de um determinado serviço. Em ambas as APIs, uma compra pode envolver mais de um item, e assim é preciso também fazer novos acessos para encontrar os detalhes textuais daquele item.
 
Foi desenvolvida uma estratégia de coletada automatizada que busca todas as compras e licitações de um determinado serviço, com seus respectivos itens.
A classe **Coletor** é responsável por essa parte do fluxo de trabalho, navegando pelas APIs, indo para as próximas páginas quando essas existem e guardando todas as respostas Json obtidas num **diretório de cache**.
Dessa forma, ao ser re-executada, as compras já coletadas não são re-visitadas. Com isso, uma vez finalizada a coleta de todas as respostas das compras de um serviço é possível trabalhar *offline* sem a necessidade de acessar a API novamente.

Foi executada a coleta tanto para o [serviço 17663](http://compras.dados.gov.br/servicos/doc/servico/17663) (Curso Aperfeiçoamento / Especialização Profissional) quanto para o [serviço 3239](http://compras.dados.gov.br/servicos/doc/servico/3239) (Transporte Rodoviário - Pessoal por Automóveis). 
Ao fim das coletas, constaram mais de 40 mil arquivos JSON no direótório de cache. Novos serviços podem ser coletados se houver interesse.

Além da navegação nas APIs de compras, também foi feita uma coleta simples da página de divulgação oficial da taxa SELIC (https://www.bcb.gov.br/pec/copom/port/taxaselic.asp), afim de subsidiar a atualização monetária dos valores das compras durante a análise.

As coletas ocorreram entre 30/10/2018 e 15/11/2018.

## Extração de dados

Mediante a coleta finalizada dos documentos de um serviço, o **Extrator** é responsável por fazer o *parse* dos documentos coletados, organizando as informações em um banco de dados relacional SQLite3 que torna fácil consultar as informações dos documentos.

Foram extraídos e armazenados como registros de uma tabela de documentos os seguintes dados: 

 * Id da Compra
 * Id do Serviço 
 * Texto descritivo da compra
 * Texto descritivos dos itens da compra
 * Valor da compra (DOUBLE)
 * Data da compra (DATE)
 * Tipo (com licitação / sem licitação)

Após a extração dos dados das compras, o banco de dados apresentou 3396 documentos do serviço 17663 (especialização) e 1842 documentos do serviço 3239 (transporte rodoviário).

Cada serviço tem os seus dados armazenados num banco separado, facilitando o manuseio nas etapas posteriores, já que as análises planejadas são feitas separadamente por serviço. A  presença da coluna **Tipo** torna o banco preparado para ser multi-serviço se necessáario. Ademais, a re-execução do **Extrator** apaga o banco e cria um novo, mas há como desligar essa abordagem.

O extrator também é responsável por fazer o *scraping* do HTML da página com o histórico da taxa SELIC mensal desde 1997, recuperando as células da tabela através de expressões *XPath* e armazenando os dados  obtidos numa tabela onde consta:

 * Data início (DATE)
 * Data fim (DATE)
 * Valor da taxa SELIC (DOUBLE)

## Processamento dos dados

O **Processador** assume a existência do banco de dados relacional SQLite3 fruto da execução do **Extrator**, e a partir dele cria novas colunas e arquivos de apoio com dados que irão subsidiar a análise.

A primeira responsabilidade do **Processador** é pré-processar o conteúdo textual de cada documento para tornar possível a criação de um bag-of-words mais otimizado que dará suporte às análises sobre os termos. O pré-processamento do texto incluiu:

* **Texto em minúsculo** - Optou-se por tratar todas as palavras em minúsculo.

* **Remoção de acentos** - Foi verificado navegando nos documentos extraídos, há ocorrência de palavras iguais com e sem acentuação ao longo dos textos, o que prejudica a correta contagem da frequência dos termos.

* **Remoção da pontuação** - Como não houve necessidade de preservar as sentenças, todas as palavras ficaram separadas por um único espaço, facilitando tratamentos posteriores. Isso foi feito com ajuda de um **RegexpTokenizer** que trasnformou o texto numa lista de palavras, ignorando espaços adjacentes e pontuação.

* **Remoção de tokens numéricos** - Tokens apenas numéricos não foram incluídos no texto processado final pois não apresentaram benefício para a análise.

* **Remoção de palavras do domínio** - Algumas expressões específicas do assunto Compras Goveernamentais estavam presentes nos documentos mas não contribuiram para uma boa compreensão do conteúdo das compras através da frequência de teremos. Sendo assim alguns termos foram removidos:
    
    ```{python}
    REMOVER = [ 'pregao eletronico', 'pregao', 'aquisicao', 'valor',
      'limite' 'licitacao', 'licitacao', 'justificativa', 'edital',
      'contratacao', 'fornecimento', 'prestacao', 'precos', 'preco',
      'formacao','empresa', 'servico', 'servicos', 'inscricao',
      'pagamento', 'taxa','para', 'objeto' ]
    ```

* **União de palavras quebradas:**
   Ao investigar a base de documentos visualmente, foi verificada uma grande ocorrência de palavras quebradas que deveriam estar unidas (ex: ca pacaitacação -> capacitação, traba lho -> trabalho).
   Para tenta resolver esse problema, foi proposta uma heurística sobre a sequência de tokens do texto. Se o *token i* concatenado ao *token i+1* formar uma palavra uma palavra integrante do vocabulário composto por todos documentos em questão, cuja frequência dessa palavra unida seja maior que 25% da frequência dos tokens separados, então os 2 tokens adjacentes são transformados num único token concatenado.
   
   Para que essa estratégia funcionasse foi preciso realizar uma primeira passada em todos os documentos para criar esse vocabulário e calcular as frequências dos tokens. Os resultados foram satisfatórios e trouxeram maior qualidade para a etapa de análise.

   O trecho de LOG abaixo demonstra algumas uniões de palavras que aconteceram durante o processamento:    

   ```
    ...
    2018-11-15 10:44:11,072 [DEBUG] - Unindo crit+erio
    2018-11-15 10:44:11,073 [DEBUG] - Unindo maqu+ina
    2018-11-15 10:44:11,099 [DEBUG] - Unindo mentori+ng
    2018-11-15 10:44:11,102 [DEBUG] - Unindo minis+trar
    2018-11-15 10:44:11,109 [DEBUG] - Unindo mer+cado
    2018-11-15 10:44:11,109 [DEBUG] - Unindo doce+ntes
    2018-11-15 10:44:11,109 [DEBUG] - Unindo integr+ada
    2018-11-15 10:44:11,109 [DEBUG] - Unindo oite+nta
    2018-11-15 10:44:11,126 [DEBUG] - Unindo univ+ersitaria
    2018-11-15 10:44:11,130 [DEBUG] - Unindo tra+nsferencia
    2018-11-15 10:44:11,132 [DEBUG] - Unindo amb+iente
    2018-11-15 10:44:11,137 [DEBUG] - Unindo enc+adernacao
    2018-11-15 10:44:11,142 [DEBUG] - Unindo w+indows
    2018-11-15 10:44:11,144 [DEBUG] - Unindo execut+iva
    2018-11-15 10:44:11,149 [DEBUG] - Unindo f+ormacao
    2018-11-15 10:44:11,152 [DEBUG] - Unindo vi+deo
    2018-11-15 10:44:11,163 [DEBUG] - Unindo te+cnicos    
    ...
   ```

* **Stemming** - Por fim, a sequẽncia de termos pré-processados é reduzida ao seu radical usando o *stemmer* para Português **nltk.stem.RSLPStemmer**. Como o objetivo era entender o panorama das compras governamentais de um determinado serviço, era importante também contemplar termos legíveis nas análises. Para tanto, ao realizar o *stemming*, foi armazenado num dicionário as frequências de cada variação do radical, para que num pós-processamento a top-palavra fosse utilizada como representante daquele conjunto de termos.

   Abaixo segue uma entrada do dicionário de frequências:

    ```
    "estim": {
        "estimativas": 24,
        "estimada": 4,
        "estimados": 1,
        "estimativa": 1,
        "estimado": 3,
        "estimadas": 1
    },
    ```

    No caso acima, a palavra **estimativas** é a melhor representante do radical **estim**, e será usada por exemplo para representar todas as demais palavras desse radical numa nuvem de palavra.

As decisões de pré-processamento do texto acima descritam foram feitas iterativamente com as análises, principalmente observando a qualidade da nuvem de palavra. O pré-processamento foi primordial para gerar uma nuvem com menos 'sujeira' e com frequências mais significativas para determinados assuntos. Abaixo segue um exemplo do texto antes e depois do processamento:

| Texto puro | Texto processsado |
| --- | --- |
|  *Frete de veiculo no percurso redencao/kikretum/redencao.. Objeto: Pregão Eletrônico -  Contratação de emp resa especializada em serviço de instalação de linha de gases especiais.Justificativa: Conduzindo professores para a aldeia kikretum.* | *frete veiculos percurso redencao kikretum redencao empresa especializada instalacao linha gases especial conduzir professores aldeia kikretum* |

O processamento final feito sobre o texto foi o ajuste de um objeto do tipo **sklean.feature_extraction.text.TfidfVectorizer** que recebeu como entrada o texto pré-processado de cada documento, e ajustou-se para fazer o cálculo do TF-IDF (Term Frequency - Inverse Document Frequncy), que é uma medida que traduz a frequência de um termo naquela coleção de documentos, levando em conta também que termos frequentes em mutos documentos são menos discriminantes.

O vetorizador foi configurado para trabalhar com 2000 palavras, cada uma sendo uma dimensão do *bag-of-words* final que pode representar um documento no espaço vetorial. O vetorizador também foi configurado para ignorar stopwords da língua Portuguesa através do **nltk.corpus.stopwords**.

Esse vetorizador foi serializado para ser usado durante a análise sempre que fosse necessário avaliar as frequências dos termos da coleção, ou vetorizar um conjunto de documentos.

Outra parte do processamento, não relacionada ao texto, foi o atualização monetária dos valores das compras pela taxa SELIC, permitindo assim uma análise mais justa das faixa de gasto maior e menor das compras durante a análise.

## Análise

### Definição das faixas de gasto

Uma análise estatística descritiva foi feito sobre os valores das compras de ambos os serviços. Em ambos os casos, verificou-se que, conforme é possível ver nas tabelas e nos gráficos, os valores de compras mais altos só ocorrem próximos do percentil 98, 99. Ou seja, a maior parte das compras tem valores moderados se comparadas com os valores máximos.

**Tabela 1**: estatística descritiva do serviço 17663 (Cursos)

| descritiva | valor |
| --- | --- |
| count | 2765 |
| mean | 47737 |
| std | 389498 |
| min | 8 |
| 0% | 8 |
| 15% | 2002 |
| 30% | 3384 |
| 45% | 5499 |
| 60% | 8522 |
| 75% | 15915 |
| 90% | 46917 |
| 93% | 63320 |
| 96% | 122307 |
| 99% | 830910 |
| max | 15324904 |

**Figura 1** - Histograma dos valores do Serviço 17663 (Cursos)
![](out/17663/histograma_valores.png?raw=true)


**Tabela 1**: estatística descritiva do serviço 3239 (Transporte)
| descritiva | valor |
| --- | --- |
| count | 1011 |
| mean | 148983 |
| std | 1673170 |
| min | 7 |
| 0% | 7 |
| 15% | 1609 |
| 30% | 2247 |
| 45% | 4183 |
| 60% | 7687 |
| 75% | 18283 |
| 90% | 68555 |
| 93% | 126200 |
| 96% | 442888 |
| 99% | 2188247 |
| max | 43048801 |

**Figura 1** - Histograma dos valores do Serviço 17663 (Cursos)
![](out/3239/histograma_valores.png?raw=true)

Para definir o ponto de corte da faixa de menor gasto para para a faixa de maior gasto, foram feitas algumas tentativas. Por fim, optou-se por uma regra que demonstrou chegar num valor adequado para ambos os serviços. O **valor de corte** foi definido como sendo a **média** somada com **1 desvio**.

Com essa abordagem, o ponto de corte do seviço 17663 foi o percentil 98.227848, e o do serviço 3239 foi o percentil 98.813056.

### Frequência de termos

O **Analisador** utiliza os valores TF-IDF advindos do processamento para gerar nuvens de palavras em que os termos com valores de frequências mais altas ficam em destaque. As nuvens foram construídas através do objeto **wordcloud.WordCloud**

Pororó x y.
![](out/17663/tagcloud_Faixa1.png?raw=true)

![](out/17663/tagcloud_Faixa2.png?raw=true)

### Termos Discriminantes (Naive Bayes)
Pororó x y.

### Modelagem de Tóṕicos (LDA)

Tópicos encontrados pelo LDA - 5 tópicos, 20 passadas, 4 palavras:

1. 0.041*"aplicacao" + 0.040*"prepom" + 0.040*"aquaviarios" + 0.039*"previstos"

2. 0.016*"curso" + 0.015*"gestao" + 0.015*"treinamento" + 0.013*"cur"

3. 0.015*"curso" + 0.014*"servidores" + 0.007*"periodo" + 0.007*"material"

4. 0.022*"conforme" + 0.019*"quantidades" + 0.018*"exigencias" + 0.018*"militares"

5. 0.039*"arte" + 0.038*"acordo" + 0.034*"ensino" + 0.021*"cacoal"

## Identificação de Padrões

Fazer uma análise da ocorrência dos padrões abaixo.

curso de *
especialização em *
mestrado em *
doutorado em *
graduação em *

## Termos que mais agregam preço às licitações/compras

## Série temporal de algum termo específico

## Anotações:

https://www.kaggle.com/ykhorramz/lda-and-t-sne-interactive-visualization