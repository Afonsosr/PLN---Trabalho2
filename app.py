import shutil
from flask import Flask, render_template, request, redirect, url_for
import json
import os
import unicodedata
from collections import defaultdict

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
def consultar_doencas(designacao):
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
                palavras_proximas = item.get("Palavras próximas")  # <-- adicionamos aqui
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

@app.route("/conceito/<designacao>/editar", methods=["GET", "POST"])
def editar_conceito(designacao):
    ficheiro_json = "glossario_por_categoria.json"
    conceitos = carregar_conceitos(ficheiro_json)

    conceito_encontrado = None
    categoria_conceito = None

    for categoria, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            if item["Conceito"].lower() == designacao.lower():
                conceito_encontrado = item
                categoria_conceito = categoria
                break
        if conceito_encontrado:
            break

    if not conceito_encontrado:
        return f"Conceito '{designacao}' não encontrado", 404

    fonte_usada = next(iter(conceito_encontrado["Fontes"].values()))

    if request.method == "POST":
        # Antes de qualquer alteração: backup
        shutil.copyfile(ficheiro_json, "glossario_backup.json")

        # Obter dados do formulário
        novo_conceito = request.form.get("conceito")
        nova_categoria = request.form.get("categoria")
        nova_descricao = request.form.get("descricao")
        nova_sigla = request.form.get("sigla")
        nova_citacao = request.form.get("citacao")
        novo_link = request.form.get("link_google_scholar")
        novas_traducoes = request.form.get("traducoes")

        # Atualizar os campos
        conceito_encontrado["Conceito"] = novo_conceito
        fonte_usada["Categoria"] = nova_categoria
        fonte_usada["Descrição"] = nova_descricao
        fonte_usada["Sigla"] = nova_sigla or None
        fonte_usada["Citação"] = nova_citacao or None
        conceito_encontrado["Link Google Scholar"] = novo_link or None

        # Processamento básico das traduções (pode ser melhorado)
        if novas_traducoes:
            traducoes_dict = parse_traducoes(novas_traducoes)
            fonte_usada["Traduções"] = traducoes_dict

        guardar_conceitos(conceitos, ficheiro_json)

        return redirect(url_for("consultar_doencas", designacao=novo_conceito))

    # GET - enviar dados atuais para o formulário
    categoria_atual = fonte_usada.get("Categoria", categoria_conceito)
    descricao_atual = fonte_usada.get("Descrição") or fonte_usada.get("Descricao")
    sigla_atual = fonte_usada.get("Sigla") or ""
    citacao_atual = fonte_usada.get("Citação") or ""
    traducoes_atual = fonte_usada.get("Traduções") or ""
    link_google_scholar = conceito_encontrado.get("Link Google Scholar") or ""

    return render_template("editar.html",
                           designacao=designacao,
                           conceito=conceito_encontrado["Conceito"],
                           categoria=categoria_atual,
                           descricao=descricao_atual,
                           sigla=sigla_atual,
                           citacao=citacao_atual,
                           traducoes=traducoes_atual,
                           link_google_scholar=link_google_scholar)



app.run(host="localhost", port=4001, debug=True)
