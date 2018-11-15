# Defina qual serviço será analisado através da constante abaixo
ID_SERVICO = '17663' # Curso Aperfeiçoamento / Especialização Profissional
#ID_SERVICO = '3239' #Transporte Rodoviário - Pessoal por Automóveis

# Diretórios
DIR_CACHE = './cache'
DIR_DATA = './data/'+ID_SERVICO
DIR_OUT = './out/'+ID_SERVICO

# Arquivos de dados usados durante análise
ARQ_BANCO = DIR_DATA + '/database.db'
ARQ_VECTORIZER = DIR_DATA + '/tfidf_vectorizer.pickle'
ARQ_VOCABULARIO = DIR_DATA + '/word_count.json'

