# Recuperação e Mineração de Texto sobre as Compras Governamentais

**Autor**: Rafael Odon de Alencar

**Email**: odon.rafael@gmail.com

**Data**: 15/11/2018

## Introdução

O presente trabalho busca exercitar técnicas de recuperação de informação e de mineração de texto através do desenvolvimento de um sistema que coleta, extrai, processa e analisa sob diversas óticas o conteúdo descritivo de uma amostra das compras do Governo Federal.
Os dados observados encontram-se disponíveis publicamente no site http://compras.dados.gov.br.

As compras feitas pelo governo podem ser do tipo **com licitação** ou **sem licitação**, e são categorizadas com ajuda de um catálogo de **serviços** e **materiais** que agrupa compras de segmentos semelhantes. No enanto, o volume de informações e a complexidade da base torna difícil contemplar as características dessas compras.

Afim de demonstrar o potencial de uma ferramenta automatizada para auxiliar na recuperação e análise em torno do texto dessas compras, foram selecionados 2 serviços:

 - Serviço 17663: Curso Aperfeiçoamento / Especialização Profissional
 - Serviço 3239: Transporte Rodoviário - Pessoal por Automóveis

O sistema foi construído em Python 3.5 com ajudas de bibliotecas tais como Pandas, Nltk, Scikit-Learn, Gensim, Matplotlib, Wordcloud dentre outras. O código foi separado em classes conforme as responsabilidades do fluxo de trabalho: **Coletor**, **Extrador**, **Processador** e **Analisador**.

Em resumo, foram coletadas todas compras com e sem licitação desses dois serviços, e o conteúdo textual descritivo desses documentos foi extraído, processado e utilizado para gerar *insights*. As compras foram classificadas quanto à faixa de gasto a partir de uma análise da estatística descritiva. Em seguida, foram geradas nuvens de tags destacando os termos descritivos de maior frequência para o **grupo de gastos menores** e para o **grupo de gastos maiores**. Um modelo de classificação *Naive Bayes* foi utilizado para verificar os termos que mais contribuiram para discriminar cada uma dessas classes. Também foi aplicada a técnica LDA (*Latent Dirichlet Allocation*) de detecção de tópicos em cada um desses grupos para verificar a co-ocorrência de termos nos conjunto de documentos. Por fim, uma estratégia de detecção de compras suspeitas foi proposta.

Cada uma das etapas será melhor descrita nas seçõe seguintes, bem como as observações e conclusões obtidas após as análises feitas com ajuda do sistema desenvolvido.

## Coleta dos documentos

O site http://compras.dados.gov.br permite navegar pelos dados através de sua interface em HTML, mas também oferece uma API que retorna documentos Json.
Há uma API própria para as **licitações** (http://compras.dados.gov.br/docs/lista-metodos-licitacoes.html), e outra API própria para as **compras sem licitação** (http://compras.dados.gov.br/docs/lista-metodos-compraSemLicitacao.html). 

Ambas possuem características diferentes mas permitem igualmente  consultar uma numerosa lista paginada com todas as compras de um determinado serviço. Em ambas as APIs, uma compra pode envolver mais de um item, e assim é preciso também navegar também para encontrar os detalhes textuais daquele item.
 
Foi desenvolvida uma estratégia de coletada automatizada que busca todas as compras e licitações de um determinado serviço, com seus respectivos itens.
A classe **Coletor** é responsável por essa parte do fluxo de trabalho, navegando pelas APIs, indo para as próximas páginas quando essas existem e guardando todas as respostas Json obtidas num **diretório de cache**.
Dessa forma, ao ser executada novamente, um acesso já realizado não é feito novamente e coleta procupa-se apenas com documentos ainda não visitados. Uma vez finalizada a coleta de todas as respostas das compras de um serviço é possível trabalhar *offline* sem a necessidade de acessar a API novamente.

Foi executada a coleta tanto para o [serviço 17663](http://compras.dados.gov.br/servicos/doc/servico/17663) (Curso Aperfeiçoamento / Especialização Profissional) quanto para o [serviço 3239](http://compras.dados.gov.br/servicos/doc/servico/3239) : (Transporte Rodoviário - Pessoal por Automóveis). 
Ao fim das coletas, constaram mais de 40 mil arquivos JSON no direótório de cache. Novos serviços podem ser coletados se houver interesse.

Além da navegação na api de compras, também foi feita uma coleta simples da página de divulgação oficial da taxa SELIC (https://www.bcb.gov.br/pec/copom/port/taxaselic.asp), afim de subsidiar a atualização monetária dos valores das compras durante a análise.

As coletas ocorreram entre 30/10/2018 e 15/11/2018.

## Extração de dados

Mediante a coleta finalizada dos documentos de um serviço, o **Extrator** é responsável por fazer o *parse* dos documentos JSON coletados, organizando as informações em um banco de dados relacional SQLite3.

Foram extraídos e armazenados como registros de uma tabela de documentos os seguintes dados: 

 * Id da Compra
 * Id do Serviço 
 * Texto descritivo da compra
 * Texto descritivos dos itens da compra
 * Valor da compra (DOUBLE)
 * Data da compra (DATE)
 * Tipo (com licitação / sem licitação)

Após a extração dos dados das compras, o banco de dados apresentou 3396 documentos do serviço 17663 (especialização) e 1842 documentos do serviço 3239 (transporte rodoviário).

O extrator também fez o *scrapping** do HTML da página com o histórico da taxa SELIC, recuperando as células da tabela através de *XPath* e armazenando numa tabela onde constou:

 * Data início (DATE)
 * Data fim (DATE)
 * Valor da taxa SELIC (DOUBLE)

Ao ser executado novamente, o extrator apaga o banco criado e cria um novo.

## Processamento dos dados

O **Processador** 

## Arquitetura da Solução

                                                    
    [ API ]--->[ Coletor ]--->[ Extrator ]--->[ Analisador ]
                    |              |              /      \
                    V              V         (modelos)  (saídas)
                 (.json)        (sqlite)         

## Pré-processamento do texto

Minúsculo

Remover acentuação 

Remover n-gramas comuns do domínio

Remove unigramas numéricos

Ignora espaços e pontuação tokenizando em palavras

Tenta resolver problema com palavras picadas (Ex: ca pacaitacação -> capacitação, traba lho -> trabalho) fazendo uma heurística sobre a sequência de tokens. Considerando o token_i + token_i+1, se um deles tiver menos de 4 caracteres, e se a junção de ambos formar uma palavra já presente no vocabulário dos documentos, e se a frequência dessa palavra for significante, funde os tokens num novo.

Exemplos de uniões de palavras que aconteceram durante o processamento:

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


Faz stemming de cada token, ao mesmo tempo contabilizando as variações de palavras de cada radical encontrado afim de utilizar a top-palavra como um representante mais amigável e legível do radical nas análises seguintes.
Ex:

    "estim": {
        "estimativas": 24,
        "estimada": 4,
        "estimados": 1,
        "estimativa": 1,
        "estimado": 3,
        "estimadas": 1
    },

A palavra **estimativas** é a melhor representante do radical **estim** na contagem acima, e logo poderá ser usada por exemplo para representar todas as demais palavras desse radical numa nuvem de tags.


## Dependências

* Python 3
* Pacotes do NLTK: floresta, mac_morpho, averaged_perceptron_tagger, rslp, stopwords 

Serviço 17663 - Curso Aperfeiçoamento / Especialização Profissional
http://compras.dados.gov.br/servicos/doc/servico/17663

## Análises

### Frequência de Termos
Pororó x y.
![](out/tagcloud_compra.png?raw=true)

![](out/tagcloud_licitacao.png?raw=true)

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