import json
import wikipediaapi
import requests
from bs4 import BeautifulSoup
import time
from collections import defaultdict

# Arquivo de entrada e saída
INPUT_FILE = "glossario_juncao.json"
OUTPUT_FILE = "glossario_enriquecido.json"
CATEGORIAS_FILE = "conceitos_por_categoria.json"

wiki = wikipediaapi.Wikipedia(
    language='pt',
    user_agent='PLN-Trabalho2/1.0'
)

def get_wikipedia_info(term):
    try:
        page = wiki.page(term)
        if page.exists():
            definicao = page.summary.split('\n')[0]
            return definicao
    except Exception as e:
        print(f"Erro ao consultar Wikipedia para '{term}': {e}")
    return ""

def get_wikipedia_synonyms_and_related(term):
    try:
        page = wiki.page(term)
        synonyms = []
        related = []
        # Sinónimos: títulos de redirecionamentos (aliases)
        # O wikipediaapi não traz redirects diretamente, então deixamos vazio
        # Termos relacionados: links da secção "Veja também"
        for section in page.sections:
            if section.title and section.title.lower() in ["veja também", "ver também", "see also"]:
                related = [l.title for l in section.links.values()]
        return synonyms, related
    except Exception as e:
        print(f"Erro ao buscar sinónimos/relacionados para '{term}': {e}")
        return [], []

def get_dicionario_medico(term):
    url = f"https://www.xn--dicionriomdico-0gb6k.com/termo/{term.lower()}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            definicao = soup.find("div", class_="definicao")
            if definicao:
                return definicao.text.strip()
    except Exception as e:
        print(f"Erro ao consultar Dicionário Médico para '{term}': {e}")
    return ""

def get_snomed_info(term):
    categorias_exemplo = {
        "fêmur": "Osso",
        "diabetes": "Doença",
        "aspirina": "Fármaco",
        "covid-19": "Doença infecciosa",
    }
    for k, v in categorias_exemplo.items():
        if k.lower() in term.lower():
            return v
    return ""

def extrair_nome_conceito(conceito):
    # Prioriza o campo "Conceito"
    for chave in ["Conceito", "Nome", "Termo"]:
        if chave in conceito and isinstance(conceito[chave], str) and conceito[chave].strip():
            return conceito[chave].strip()
    return ""

def enriquecer_conceito(conceito):
    nome = extrair_nome_conceito(conceito)
    if not nome:
        return conceito

    # Wikipedia - definição
    definicao_wiki = get_wikipedia_info(nome)
    if definicao_wiki:
        conceito["Definicao_Wikipedia"] = definicao_wiki

    # Wikipedia - sinónimos e termos relacionados
    sinonimos, relacionados = get_wikipedia_synonyms_and_related(nome)
    if sinonimos:
        conceito["Sinonimos_Wikipedia"] = sinonimos
    if relacionados:
        conceito["Termos_Relacionados_Wikipedia"] = relacionados

    # Dicionário Médico
    definicao_dic = get_dicionario_medico(nome)
    if definicao_dic:
        conceito["Definicao_DicionarioMedico"] = definicao_dic

    # SNOMED (simulado)
    categoria_snomed = get_snomed_info(nome)
    if categoria_snomed:
        conceito["Categoria_SNOMED"] = categoria_snomed

    return conceito

def agrupar_por_categoria(glossario, campo_categoria="Categoria"):
    categorias = defaultdict(list)
    for conceito in glossario:
        categoria = conceito.get(campo_categoria, "Sem Categoria")
        categorias[categoria].append(conceito)
    return categorias

def salvar_categorias_json(categorias, filename=CATEGORIAS_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(categorias, f, ensure_ascii=False, indent=2)

def main():
    # Carrega o glossário
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        glossario = json.load(f)

    glossario = glossario[:50]

    glossario_enriquecido = []
    for i, conceito in enumerate(glossario):
        conceito_enriquecido = enriquecer_conceito(conceito)
        glossario_enriquecido.append(conceito_enriquecido)
        print(f"[{i+1}/{len(glossario)}] {extrair_nome_conceito(conceito)} processado.")
        time.sleep(1)  # Evita sobrecarregar os sites

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(glossario_enriquecido, f, ensure_ascii=False, indent=2)

    print(f"\nGlossário enriquecido salvo em: {OUTPUT_FILE}")

    # Agrupar por categoria e salvar em outro JSON
    categorias = agrupar_por_categoria(glossario_enriquecido)
    salvar_categorias_json(categorias)
    print(f"Conceitos agrupados por categoria salvos em: {CATEGORIAS_FILE}")

if __name__ == "__main__":
    main()