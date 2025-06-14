import json
import time
from tqdm import tqdm
from gensim.models import Word2Vec
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt')

# Carregar o glossário
with open('glossario_juncao_atualizado.json', encoding='utf-8') as f:
    glossario = json.load(f)

# Preparar frases para treinar o modelo
frases = []
for conceito in glossario:
    nome = conceito.get("Conceito", "")
    if nome:
        frases.append([token.lower() for token in word_tokenize(nome, language='portuguese') if token.isalpha()])
    # Também pode incluir descrições, se quiser enriquecer o contexto:
    fontes = conceito.get("Fontes", {})
    for fonte in fontes.values():
        desc = fonte.get("Descrição", "")
        if desc:
            frases.append([token.lower() for token in word_tokenize(desc, language='portuguese') if token.isalpha()])

# Treinar o modelo Word2Vec
model = Word2Vec(frases, vector_size=100, window=5, min_count=1, sg=1, epochs=10, workers=3)

# Organizar por categoria
categorias = {}

for conceito in tqdm(glossario, desc="Processando conceitos"):
    nome = conceito.get("Conceito", "")
    palavras_proximas = []
    if nome:
        tokens = [token.lower() for token in word_tokenize(nome, language='portuguese') if token.isalpha()]
        # Para cada token do conceito, pega as palavras mais próximas e junta numa lista
        similares = []
        for token in tokens:
            try:
                similares += [(w, round(score, 2)) for w, score in model.wv.most_similar(token, topn=10)]
            except KeyError:
                continue
        # Remove duplicados e o próprio termo, pega os 5 primeiros
        palavras_proximas = [w for w in dict.fromkeys(similares) if w not in tokens][:5]
    conceito["Palavras próximas"] = palavras_proximas

    if nome:
        conceito["Link Google Scholar"] = f"https://scholar.google.com/scholar?q={nome.replace(' ', '+')}"

    # Procurar categoria em qualquer fonte
    fontes = conceito.get('Fontes', {})
    categoria = None
    for fonte in fontes.values():
        if 'Categoria' in fonte:
            categoria = fonte['Categoria']
            break
    if not categoria:
        categoria = 'sem categoria'
    if categoria not in categorias:
        categorias[categoria] = []
    categorias[categoria].append(conceito)
    time.sleep(0.1)  # Pode reduzir, pois não há scraping

# Salvar resultado
with open('glossario_por_categoria.json', 'w', encoding='utf-8') as f:
    json.dump(categorias, f, ensure_ascii=False, indent=2)

print("Processo concluído! Veja o arquivo 'glossario_por_categoria.json'.")