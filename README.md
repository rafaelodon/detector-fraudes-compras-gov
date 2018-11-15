# Mineração de texto sobre os itens das licitações de compras do governo.

**Autor**: Rafael Odon de Alencar

**Email**: odon.rafael@gmail.com

## Introdução
Fonte: API de dados abertos do ComprasNet (http://compras.dados.gov.br)

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