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
    link_google_scholar = None  # <-- inicializa a variável

    for categoria_nome, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            if item["Conceito"].lower() == designacao.lower():
                conceito_encontrado = item
                fonte_usada = next(iter(item["Fontes"].values()))
                link_google_scholar = item.get("Link Google Scholar") 
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
                           designacao=designacao)




app.run(host="localhost", port=4001, debug=True)
