import shutil
from flask import Flask, render_template, request, redirect, url_for
import json
import os
import unicodedata
from collections import defaultdict
import re

app = Flask(__name__)

file = "glossario_por_categoria.json"

with open(file, 'r', encoding='utf-8') as file:
    conceitos = json.load(file)

def guardar_conceitos(conceitos, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(conceitos, file, ensure_ascii=False, indent=4)
        
def carregar_conceitos(file):
    with open(file, 'r', encoding='utf-8') as file:
        conceitos = json.load(file)
    return conceitos

@app.route("/")
def home():
    tamanho = len(conceitos)
    return render_template("home.html", tamanho = tamanho)

@app.route("/conceitos")
def listar_conceitos():
    conceitos = carregar_conceitos("glossario_por_categoria.json")

    conceitos_por_letra = defaultdict(list)

    for categoria, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            conceito = item.get("Conceito")
            if conceito:
                conceito_sem_acentos = unicodedata.normalize("NFD", conceito).encode("ascii", "ignore").decode("utf-8")
                primeira_letra = conceito_sem_acentos[0].upper()
                conceitos_por_letra[primeira_letra].append(conceito)

    for letra in conceitos_por_letra:
        conceitos_por_letra[letra].sort(key=lambda c: unicodedata.normalize("NFD", c).encode("ascii", "ignore").decode("utf-8"))

    # Ordenar as letras
    conceitos_por_letra_ordenado = dict(sorted(conceitos_por_letra.items()))

    return render_template("conceitos.html", conceitos_por_letra=conceitos_por_letra_ordenado)

def smart_capitalize(texto):
    if not texto:
        return texto
    return texto[0].upper() + texto[1:]

def parse_traducoes(traducoes):
    traducoes_dict = {}

    if isinstance(traducoes, str):
        partes = traducoes.split(";")
        for parte in partes:
            parte = parte.strip()
            if "[" in parte and "]" in parte:
                termo, idioma = parte.rsplit("[", 1)
                idioma = idioma.replace("]", "").strip().lower()
                termo = termo.strip()
                termo = smart_capitalize(termo)
                traducoes_dict[idioma] = termo
    elif isinstance(traducoes, list):
        for item in traducoes:
            if ":" in item:
                idioma, termo = item.split(":", 1)
                idioma = idioma.strip().lower()
                termo = termo.strip()
                termo = smart_capitalize(termo)
                traducoes_dict[idioma] = termo
    elif isinstance(traducoes, dict):
        # No caso de já ser dict, aplicamos o capitalize a cada termo
        for idioma, termo in traducoes.items():
            traducoes_dict[idioma] = smart_capitalize(termo)
    else:
        traducoes_dict = {}

    return traducoes_dict

@app.route("/conceito/<designacao>") 
def consultar_conceitos(designacao):

    conceitos = carregar_conceitos("glossario_por_categoria.json")

    conceito_encontrado = None
    fonte_usada = None
    link_google_scholar = None  
    palavras_proximas = None

    for categoria_nome, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            if item["Conceito"].lower() == designacao.lower():
                conceito_encontrado = item
                fonte_usada = next(iter(item["Fontes"].values()))
                link_google_scholar = item.get("Link Google Scholar") 
                palavras_proximas = item.get("Palavras próximas")  
                break
        if conceito_encontrado:
            break

    if not conceito_encontrado:
        return f"Conceito '{designacao}' não encontrado", 404

    categoria = fonte_usada.get("Categoria", categoria_nome)
    descricao = fonte_usada.get("Descrição") or fonte_usada.get("Descricao")
    citacao = fonte_usada.get("Citação") or None  
    sigla = fonte_usada.get("Sigla") or None
    traducoes_raw = fonte_usada.get("Traduções") or fonte_usada.get("Traducoes")

    traducoes_dict = parse_traducoes(traducoes_raw)

    return render_template("descricao.html",
                           categoria=categoria,
                           descricao=descricao,
                           citacao=citacao,  
                           sigla=sigla,
                           link_google_scholar=link_google_scholar,
                           traducoes=traducoes_dict,
                           designacao=smart_capitalize(designacao),
                           palavras_proximas=palavras_proximas)  

@app.route("/conceito/<designacao>/eliminar", methods=["POST"])
def eliminar_conceito(designacao):
    ficheiro_json = "glossario_por_categoria.json"
    conceitos = carregar_conceitos(ficheiro_json)

    conceito_removido = False

    for categoria, lista_conceitos in conceitos.items():
        for i, item in enumerate(lista_conceitos):
            if item["Conceito"].lower() == designacao.lower():
                shutil.copyfile(ficheiro_json, "glossario_backup.json")
                del lista_conceitos[i]
                conceito_removido = True
                break
        if conceito_removido:
            break

    if conceito_removido:
        guardar_conceitos(conceitos, ficheiro_json)
        return redirect(url_for("listar_conceitos"))
    else:
        return f"Conceito '{designacao}' não encontrado", 404

# Função auxiliar para garantir que nunca passamos None aos templates
def safe_get(dicionario, chave, default=""):
    if not dicionario:
        return default
    valor = dicionario.get(chave)
    return valor if valor is not None else default

# Função que formata as traduções para o input
def formatar_traducoes_para_input(traducoes):
    if not traducoes:
        return ""
    if isinstance(traducoes, dict):
        partes = []
        for idioma, termo in traducoes.items():
            partes.append(f"{termo}[{idioma}]")
        return "; ".join(partes)
    elif isinstance(traducoes, str):
        return traducoes
    else:
        return ""
@app.route("/conceito/<designacao>/editar", methods=["GET", "POST"])
def editar_conceito(designacao):
    ficheiro_json = "glossario_por_categoria.json"
    conceitos = carregar_conceitos(ficheiro_json)

    conceito_encontrado = None
    categoria_conceito = None

    for categoria, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            if item.get("Conceito", "").lower() == designacao.lower():
                conceito_encontrado = item
                categoria_conceito = categoria
                break
        if conceito_encontrado:
            break

    if not conceito_encontrado:
        return f"Conceito '{designacao}' não encontrado", 404

    fontes = conceito_encontrado.get("Fontes", {})
    fonte_usada = next(iter(fontes.values()), {})

    if request.method == "POST":
        shutil.copyfile(ficheiro_json, "glossario_backup.json")

        novo_conceito = request.form.get("conceito", "").strip()
        nova_categoria = request.form.get("categoria", "").strip()
        nova_descricao = request.form.get("descricao", "").strip()
        nova_sigla = request.form.get("sigla", "").strip()
        nova_citacao = request.form.get("citacao", "").strip()
        novo_link = request.form.get("link_google_scholar", "").strip()
        novas_traducoes = request.form.get("traducoes", "").strip()

        if nova_categoria != categoria_conceito:
            conceitos[categoria_conceito].remove(conceito_encontrado)
            if not conceitos[categoria_conceito]:
                del conceitos[categoria_conceito]
            if nova_categoria not in conceitos:
                conceitos[nova_categoria] = []
            conceitos[nova_categoria].append(conceito_encontrado)
            categoria_conceito = nova_categoria

        conceito_encontrado["Conceito"] = novo_conceito
        fonte_usada["Categoria"] = nova_categoria
        fonte_usada["Descrição"] = nova_descricao or fonte_usada.get("Descricao", "")
        fonte_usada["Sigla"] = nova_sigla or None
        fonte_usada["Citação"] = nova_citacao or None
        conceito_encontrado["Link Google Scholar"] = novo_link or None

        if novas_traducoes:
            traducoes_dict = parse_traducoes(novas_traducoes)
            fonte_usada["Traduções"] = traducoes_dict
        else:
            fonte_usada["Traduções"] = {}

        guardar_conceitos(conceitos, ficheiro_json)

        return redirect(url_for("consultar_conceitos", designacao=novo_conceito))


    conceito_nome = safe_get(conceito_encontrado, "Conceito")
    categoria_atual = safe_get(fonte_usada, "Categoria", categoria_conceito)
    descricao_atual = safe_get(fonte_usada, "Descrição") or safe_get(fonte_usada, "Descricao")
    sigla_atual = safe_get(fonte_usada, "Sigla")
    citacao_atual = safe_get(fonte_usada, "Citação")
    traducoes_raw = safe_get(fonte_usada, "Traduções") or safe_get(fonte_usada, "Traducoes")
    traducoes_atual = formatar_traducoes_para_input(traducoes_raw)
    link_google_scholar = safe_get(conceito_encontrado, "Link Google Scholar")

    return render_template("editar.html",
                           designacao=designacao,
                           conceito=conceito_nome,
                           categoria=categoria_atual,
                           descricao=descricao_atual,
                           sigla=sigla_atual,
                           citacao=citacao_atual,
                           traducoes=traducoes_atual,
                           link_google_scholar=link_google_scholar)

def obter_categorias(caminho):
    conceitos = carregar_conceitos(caminho)
    
    lista_categorias = list(conceitos.keys())
    
    lista_categorias = [categoria.capitalize() for categoria in lista_categorias]
    
    return sorted(lista_categorias)

@app.route("/categorias")
def listar_categorias():
    caminho_json = "glossario_por_categoria.json"
    lista_ordenada = obter_categorias(caminho_json)
    return render_template("categorias.html", lista_ordenada=lista_ordenada)

@app.route("/categorias/<categoria>")
def consultar_categoria(categoria):
    conceitos_por_categoria = carregar_conceitos("glossario_por_categoria.json")

    categoria_original = next((cat for cat in conceitos_por_categoria.keys() if cat.lower() == categoria.lower()), None)

    if not categoria_original:
        return f"Categoria '{categoria}' não encontrada", 404

    lista_conceitos = conceitos_por_categoria[categoria_original]

    return render_template("consultar_categoria.html", categoria=categoria_original, conceitos=lista_conceitos)

@app.route("/tabela")
def tabela():
    conceitos_por_categoria = carregar_conceitos("glossario_por_categoria.json")

    todos_conceitos = []
    for categoria, lista_conceitos in conceitos_por_categoria.items():
        for conceito in lista_conceitos:
            conceito_dict = {
                "Conceito": conceito.get("Conceito", ""),
                "Categoria": categoria,
                "Descricao": next(iter(conceito.get("Fontes", {}).values())).get("Descrição", "")
            }
            todos_conceitos.append(conceito_dict)

    return render_template("tabela.html", conceitos=todos_conceitos)

@app.route('/proximas')
def relacoes_conceitos():
    conceito_palavras = {}

    for categoria in conceitos:
        for item in conceitos[categoria]:
            conceito = item['Conceito']
            palavras = [p[0] for p in item.get('Palavras próximas', [])]
            conceito_palavras[conceito] = palavras

    relacoes = {}

    for conceito, palavras in conceito_palavras.items():
        ligacoes = {}
        for palavra in palavras:
            conceitos_relacionados = []
            for outro_conceito, outras_palavras in conceito_palavras.items():
                if outro_conceito != conceito and palavra in outras_palavras:
                    conceitos_relacionados.append(outro_conceito)
            ligacoes[palavra] = conceitos_relacionados
        relacoes[conceito] = ligacoes

    termo_pesquisa = request.args.get('query', '').strip()

    if termo_pesquisa:
        relacoes = {k: v for k, v in relacoes.items() if termo_pesquisa.lower() in k.lower()}

    relacoes_ordenado = {}
    for conceito in sorted(relacoes.keys(), key=lambda x: x.lower()):
        conceito_formatado = conceito.title()
        relacoes_ordenado[conceito_formatado] = relacoes[conceito]

    return render_template('palavras_proximas.html', relacoes=relacoes_ordenado)

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

@app.route('/inversa')
def listar_palavras_proximas():
    palavras_unicas = set()

    for categoria in conceitos:
        for item in conceitos[categoria]:
            palavras = [p[0].strip() for p in item.get('Palavras próximas', [])]
            palavras_unicas.update(palavras)

    palavras_por_letra = {}

    for palavra in palavras_unicas:
        palavra_limpa = palavra.strip()
        if palavra_limpa:
            primeira_letra = remover_acentos(palavra_limpa[0].upper())

            # Agora vamos fazer o "truque" que querias:
            if primeira_letra.startswith("F") and not primeira_letra == "F":
                primeira_letra = "F"

            palavras_por_letra.setdefault(primeira_letra, []).append(palavra)

    for letra in palavras_por_letra:
        palavras_por_letra[letra].sort(key=lambda x: x.lower())

    palavras_por_letra = dict(sorted(palavras_por_letra.items()))

    return render_template('inversa.html', palavras_por_letra=palavras_por_letra)

@app.route('/inversa/<palavra>')
def mostrar_conceitos_por_palavra(palavra):
    resultados = []

    for categoria in conceitos:
        for item in conceitos[categoria]:
            conceito = item['Conceito']
            palavras = [p[0] for p in item.get('Palavras próximas', [])]
            if palavra in palavras:
                resultados.append(conceito)

    return render_template('inversa_palavra.html', palavra=palavra, resultados=resultados)

@app.route("/adiciona", methods=["GET", "POST"])
def adicionar_conceito():
    ficheiro_json = "glossario_por_categoria.json"
    conceitos = carregar_conceitos(ficheiro_json)

    if request.method == "POST":
        shutil.copyfile(ficheiro_json, "glossario_backup.json")

        # Recolher dados do formulário
        conceito_nome = request.form.get("conceito", "").strip()
        categoria = request.form.get("categoria", "").strip()
        descricao = request.form.get("descricao", "").strip()
        sigla = request.form.get("sigla", "").strip()
        citacao = request.form.get("citacao", "").strip()
        traducoes_raw = request.form.get("traducoes", "").strip()
        link_google_scholar = request.form.get("link_google_scholar", "").strip()

        # Verificar se a categoria já existe no ficheiro
        if categoria not in conceitos:
            conceitos[categoria] = []

        # Preparar as traduções no formato dicionário
        traducoes_dict = parse_traducoes(traducoes_raw) if traducoes_raw else {}

        # Definir fonte (pode ser sempre 'manual' ou outro identificador)
        fonte = {
            "Conceito": conceito_nome,
            "Categoria": categoria,
            "Descrição": descricao,
            "Sigla": sigla if sigla else "Sem Sigla Associada",
            "Citação": citacao,
            "Traduções": traducoes_dict
        }

        novo_conceito = {
            "Conceito": conceito_nome,
            "Fontes": {
                "manual": fonte
            },
            "Palavras próximas": [],
            "Link Google Scholar": link_google_scholar if link_google_scholar else None
        }

        conceitos[categoria].append(novo_conceito)

        guardar_conceitos(conceitos, ficheiro_json)
        return redirect(url_for("listar_conceitos"))

    return render_template("adicionar.html")



app.run(host="localhost", port=4001, debug=True)
